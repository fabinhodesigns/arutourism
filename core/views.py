# core/views.py
from __future__ import annotations

import csv
import io
import re
from io import BytesIO, StringIO
from urllib.parse import urlparse, parse_qs

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm  # (mantido se você usar em outro lugar)
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import csv, io

from core.models import Categoria, Empresa
from .forms import CustomLoginForm, EmpresaForm, UserRegistrationForm

# ============================================================
# Constantes / Mapeamentos
# ============================================================

COLUMN_ALIASES = {
    "cnpj":      ["cnpj"],
    "categoria": [
        "categoria", "ramo atividade", "ramo de atividade", "ramo",
        "categoria (ramo atividade)", "categoria ramo atividade"
    ],
    "nome":      ["nome", "razão social", "razao social"],
    "bairro":    ["bairro", "endereço 2", "endereco 2"],
    "endereco":  [
        "endereço", "endereco", "logradouro", "rua",
        "endereço completo", "endereco completo"
    ],
    "numero":    ["número", "numero", "nº", "nro"],
    "cidade":    ["cidade", "municipio", "município"],
    "cep":       ["cep", "c.e.p."],
    "telefone":  ["telefone", "fone", "whatsapp"],
    "contato":   ["contato direto", "contato"],
    "digital":   [
        "digital", "site / redes", "site redes", "redes sociais",
        "site", "instagram", "facebook", "digital (site/redes)"
    ],
    "cadastrur": ["cadastur", "cadas tur", "cadastro tur"],
    "maps":      ["maps", "google maps", "mapa", "link mapa", "maps (link)"],
    "app":       ["app", "aplicativo"],
    "descricao": ["descrição", "descricao", "observacao", "observação", "obs"],
}


TEMPLATE_HEADERS = [
    ("CNPJ",                          False, "cnpj"),
    ("CATEGORIA (RAMO ATIVIDADE)",    False, "categoria"),
    ("NOME",                          False, "nome"),
    ("BAIRRO",                        False, "bairro"),
    ("ENDEREÇO COMPLETO",             False, "endereco"),
    ("TELEFONE",                      False, "telefone"),
    ("CONTATO DIRETO",                False, "contato"),
    ("DIGITAL (site/redes)",          False, "digital"),
    ("CADASTUR",                      False, "cadastrur"),
    ("MAPS (link)",                   False, "maps"),
    ("APP",                           False, "app"),
    ("DESCRIÇÃO",                     False, "descricao"),
    ("NÚMERO",                        False, "numero"),
    ("CEP",                           False, "cep"),
    ("CIDADE",                        False, "cidade"),
]

LOREM_DEFAULT = (
    "Descrição ainda não informada. Este estabelecimento está em processo de "
    "complementação de dados. Se você é o responsável, atualize as informações."
)

DEFAULT_DESC = (
    "Descrição ainda não informada. Este estabelecimento está em processo de "
    "complementação de dados. Se você é o responsável, atualize as informações."
)

EXPECTED_CANONS = [c for (_label, _req, c) in TEMPLATE_HEADERS]
HUMAN_LABEL_BY_CANON = {c: label for (label, _req, c) in TEMPLATE_HEADERS}

# ============================================================
# Helpers
# ============================================================





def _norm_text(s: str | None) -> str:
    return re.sub(r"[\W_]+", " ", (s or "")).strip().lower()

def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")

def _extract_latlng_from_maps(url: str | None):
    """Extrai lat/lng de links do Google Maps quando possível (opcional)."""
    try:
        if not url:
            return None, None
        u = urlparse(url)
        qs = parse_qs(u.query)
        if "q" in qs and "," in qs["q"][0]:
            lat, lng = qs["q"][0].split(",")[:2]
            return float(lat), float(lng)
        m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(1)), float(m.group(2))
    except Exception:
        pass
    return None, None

def _alias_match(key_norm: str, alias: str) -> bool:
    """Casa de forma flexível: tokens do alias presentes no cabeçalho."""
    a = _norm_text(alias).split()
    k = key_norm.split()
    return all(t in k for t in a) or key_norm == _norm_text(alias)

def _build_header_map(raw_headers: list[str]) -> dict[int, str]:
    """index_coluna -> chave_canônica (ordem livre, aceita variações)."""
    mapping = {}
    for idx, raw in enumerate(raw_headers or []):
        key_norm = _norm_text(raw)
        for canon, alts in COLUMN_ALIASES.items():
            if any(_alias_match(key_norm, alt) for alt in alts):
                mapping[idx] = canon
                break
    return mapping

def _read_rows_from_upload(file_obj, filename: str):
    """Lê .xlsx (openpyxl) ou .csv (utf-8). Retorna: (headers, body)"""
    name = (filename or "").lower()
    if name.endswith(".csv"):
        import csv, io
        data = file_obj.read().decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(data))
        rows = list(reader)
        if not rows:
            return [], []
        headers = [str(c).strip() for c in rows[0]]
        body = [[str(c).strip() for c in r] for r in rows[1:]]
        return headers, body

    # XLSX
    from openpyxl import load_workbook
    wb = load_workbook(file_obj, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([(c if c is not None else "") for c in row])
    if not rows:
        return [], []
    headers = [str(c).strip() for c in rows[0]]
    body = [[str(c).strip() for c in r] for r in rows[1:]]
    return headers, body

def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")

def _squeeze(s: str | None) -> str:
    """trim + colapsa espaços"""
    return re.sub(r"\s+", " ", (s or "").strip())

def _norm_label(s: str | None) -> str:
    """normaliza rótulo de coluna: lowercase, remove '(...)', colapsa espaços"""
    s = (s or "")
    # remove conteúdos em parênteses (ex.: '(OBRIGATÓRIO)', '(opcional)')
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.replace(":", " ").replace("/", " ")
    s = _squeeze(s).lower()
    return s

def _norm_space_lower(s: str | None) -> str:
    return re.sub(r"[\W_]+", " ", (s or "")).strip().lower()

def _to_float(val, default=None):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(str(val).replace(",", "."))
    except Exception:
        return default

def _match_header_map(headers: list[str]) -> dict[int, str]:
    """
    Mapeia índice da coluna -> chave canônica (ex.: 3 -> 'cidade'),
    aceitando sinônimos definidos em COLUMN_ALIASES.
    """
    result = {}
    for idx, raw in enumerate(headers):
        k = _norm_space_lower(raw)
        for canon, alts in COLUMN_ALIASES.items():
            if k in [_norm_space_lower(a) for a in alts]:
                result[idx] = canon
                break
    return result

def _get_reader(file_obj, filename: str):
    """
    Lê CSV (utf-8) ou XLSX e retorna lista de linhas (list[list[str]]).
    Primeira linha é header.
    """
    ext = (filename or "").lower()
    if ext.endswith(".csv"):
        data = file_obj.read().decode("utf-8", errors="ignore")
        reader = csv.reader(StringIO(data))
        rows = [[(c or "").strip() for c in r] for r in reader]
        return rows

    # XLSX (openpyxl)
    from openpyxl import load_workbook
    wb = load_workbook(file_obj, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append([("" if c is None else str(c)).strip() for c in row])
    return rows


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def _to_float(val, default=None):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(str(val).replace(",", "."))
    except Exception:
        return default

def _strip_parens(s: str | None) -> str:
    """Remove QUALQUER sufixo entre parênteses no cabeçalho."""
    if not s:
        return ""
    # remove tudo que estiver entre parênteses no final do texto
    return re.sub(r"\s*\(.*?\)\s*$", "", str(s)).strip()

def _has_field(model_class, field_name: str) -> bool:
    return any(getattr(f, "name", None) == field_name for f in model_class._meta.get_fields())



# ============================================================
# Páginas básicas / Auth
# ============================================================

def home(request):
    empresas = Empresa.objects.all().order_by('-data_cadastro')[:6]
    total_empresas = Empresa.objects.count()
    return render(request, 'home.html', {'empresas': empresas, 'total_empresas': total_empresas})

def sobre(request):
    return render(request, 'core/sobre.html/')

def termo_de_servico(request):
    return render(request, 'core/termo_de_servico.html/')

def politica_de_privacidade(request):
    return render(request, 'core/politica_de_privacidade.html/')

def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Atenção: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            auth_login(request, form.user)
            return redirect('home')
        messages.error(request, "Usuário ou senha inválidos.")
        return render(request, 'core/login.html', {'form': form})

    form = CustomLoginForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# ============================================================
# Usuários (admin simples)
# ============================================================

def listar_usuarios(request):
    if not request.user.is_authenticated:
        return redirect('login')
    usuarios = User.objects.all() if request.user.is_superuser else User.objects.filter(id=request.user.id)
    return render(request, '/listar_usuarios.html', {'usuarios': usuarios})

def editar_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    if request.user != usuario and not request.user.is_superuser:
        raise Http404("Você não tem permissão para editar este usuário.")
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('listar_usuarios')
    else:
        form = UserRegistrationForm(instance=usuario)
    return render(request, '/editar_usuario.html', {'form': form})

def excluir_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    if request.user != usuario and not request.user.is_superuser:
        raise Http404("Você não tem permissão para excluir este usuário.")
    if request.method == 'POST':
        usuario.delete()
        return redirect('listar_usuarios')
    return render(request, '/excluir_usuario.html', {'usuario': usuario})

# ============================================================
# Empresas (CRUD básico)
# ============================================================

@login_required(login_url='/login/')
def cadastrar_empresa(request):
    if request.method == 'GET':
        form = EmpresaForm()
        return render(request, 'core/cadastrar_empresa.html', {'form': form})

    if request.method == 'POST':
        post_data = request.POST.copy()

        # saneia CEP
        if 'cep' in post_data:
            post_data['cep'] = re.sub(r'\D', '', post_data['cep'])

        form = EmpresaForm(post_data, request.FILES)

        if form.is_valid():
            empresa = form.save(commit=False)

            # descrição padrão
            if not (empresa.descricao or '').strip():
                empresa.descricao = DEFAULT_DESC  # <— agora existe

            empresa.user = request.user
            empresa.save()

            message = f"Empresa '{empresa.nome}' cadastrada com sucesso!"
            action = 'reset' if 'save_and_add' in request.POST else 'redirect'
            redirect_url = '/suas_empresas/' if action == 'redirect' else ''

            return JsonResponse({
                'status': 'success',
                'message': message,
                'action': action,
                'redirect_url': redirect_url
            })

        return render(request, 'core/cadastrar_empresa.html', {'form': form}, status=400)
    
@login_required(login_url='/login/')
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if empresa.user != request.user:
        raise Http404("Você não tem permissão para editar esta empresa.")

    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f"A empresa '{empresa.nome}' foi atualizada com sucesso!")
            return redirect('suas_empresas')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'core/cadastrar_empresa.html', {'form': form, 'is_editing': True})

@login_required(login_url='/login/')
def suas_empresas(request):
    empresas = Empresa.objects.filter(user=request.user).order_by('-data_cadastro')
    paginator = Paginator(empresas, 6)
    page_obj = paginator.get_page(request.GET.get('page') or 1)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('core/partials/empresas_cards.html', {'page_obj': page_obj})
        return JsonResponse({'html': html, 'has_next': page_obj.has_next(),
                             'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None})
    return render(request, 'core/suas_empresas.html', {'page_obj': page_obj})

def empresa_detalhe(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    return render(request, 'core/empresa_detalhe.html', {'empresa': empresa})

# ============================================================
# Listagem + filtros (com “Load more” opcional)
# ============================================================

def listar_empresas(request):
    empresas = Empresa.objects.all().order_by('-id')

    q = (request.GET.get('q') or '').strip()
    categoria = (request.GET.get('categoria') or '').strip()
    cidade = (request.GET.get('cidade') or '').strip()
    com_imagem_real = request.GET.get('com_imagem_real') == '1'
    meus = request.GET.get('meus') == '1'

    if q:
        empresas = empresas.filter(
            Q(nome__icontains=q) |
            Q(descricao__icontains=q) |
            Q(bairro__icontains=q) |
            Q(cidade__icontains=q) |
            Q(categoria__nome__icontains=q)
        )
    if categoria:
        empresas = empresas.filter(categoria_id=categoria)
    if cidade:
        empresas = empresas.filter(cidade__iexact=cidade)
    if com_imagem_real:
        # ajuste conforme seu field/placeholder
        empresas = empresas.exclude(imagem='').exclude(imagem__icontains='placeholders/sem_imagem.png')
    if meus and request.user.is_authenticated:
        empresas = empresas.filter(user=request.user)

    paginator = Paginator(empresas, 12)  # 12 por página
    page_obj = paginator.get_page(request.GET.get('page') or 1)

    is_ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest') or (request.GET.get('ajax') == '1')
    if is_ajax:
        html = render_to_string('core/partials/empresas_cards.html', {'page_obj': page_obj}, request=request)
        return JsonResponse({'html': html, 'has_next': page_obj.has_next(),
                             'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None})

    filtros_aplicados = {
        'q': q, 'categoria': categoria, 'cidade': cidade,
        'com_imagem_real': '1' if com_imagem_real else '',
        'meus': '1' if meus else '',
    }
    return render(request, 'core/listar_empresas.html', {'page_obj': page_obj, 'filtros_aplicados': filtros_aplicados})

def buscar_empresas(request):
    """Rota legada: redireciona para a listagem com os mesmos GETs."""
    return listar_empresas(request)

@require_GET
def filtros_empresas(request):
    """Compat: retorna categorias e cidades em JSON (se ainda for usado em algum ponto)."""
    categorias = list(Categoria.objects.order_by('nome').values('id', 'nome'))
    cidades = list(
        Empresa.objects.exclude(cidade__isnull=True).exclude(cidade__exact='')
        .order_by('cidade').values_list('cidade', flat=True).distinct()
    )
    return JsonResponse({'categorias': categorias, 'cidades': list(cidades)})

# ============================================================
# Modelo XLSX para download
# ============================================================

@require_GET
def download_template_empresas(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Empresas"

    headers = [
        "CNPJ",
        "CATEGORIA (RAMO ATIVIDADE)",
        "NOME",
        "BAIRRO",
        "ENDEREÇO COMPLETO",
        "TELEFONE",
        "CONTATO DIRETO",
        "DIGITAL (site/redes)",
        "CADASTUR",
        "MAPS (link)",
        "APP",
        "DESCRIÇÃO",
        "NÚMERO",
        "CEP",
        "CIDADE",
    ]
    ws.append(headers)

    exemplo = [
        "12.345.678/0001-99",
        "Pousada",
        "Pousada Azul",
        "Centro",
        "Av. Central, 123",
        "(48) 99999-9999",
        "Maria (WhatsApp)",
        "site: https://exemplo.com / insta: @pousada",
        "123456789/0123-4",
        "https://maps.google.com/?q=-28.93,-49.48",
        "",
        "Hotel aconchegante com café da manhã.",
        "123",
        "88900-000",
        "Araranguá",
    ]
    ws.append(exemplo)

    for i in range(1, len(headers)+1):
        ws.column_dimensions[get_column_letter(i)].width = 28

    bio = BytesIO()
    wb.save(bio); bio.seek(0)
    return HttpResponse(
        bio.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="modelo_empresas.xlsx"'},
    )

# ============================================================
# Importação em lote (XLSX/CSV)
# ============================================================

@login_required
@require_POST
@transaction.atomic
def importar_empresas_arquivo(request):
    up = request.FILES.get("arquivo")
    if not up:
        return JsonResponse({"ok": False, "error": "Envie um arquivo .xlsx ou .csv."}, status=400)

    try:
        headers_raw, rows = _read_rows_from_upload(up, up.name)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Falha ao ler arquivo: {e}"}, status=400)

    if not rows:
        return JsonResponse({"ok": False, "error": "Arquivo vazio."}, status=400)

    header_map = _build_header_map(headers_raw)
    if not header_map:
        return JsonResponse({"ok": False, "error": "Nenhum cabeçalho reconhecido."}, status=400)

    created, errors = 0, 0
    msgs = []

    for line_no, r in enumerate(rows, start=2):  # 2 por causa do header
        # coleta valores normalizados pelas chaves canônicas
        data = {k: "" for k in COLUMN_ALIASES.keys()}
        for idx, canon in header_map.items():
            if idx < len(r):
                data[canon] = (r[idx] or "").strip()

        try:
            nome = (data.get("nome") or "").strip()
            if not nome:
                raise ValueError("NOME é obrigatório.")

            # categoria (cria se não existir)
            cat_name = (data.get("categoria") or "").strip() or "Sem Categoria"
            categoria, _ = Categoria.objects.get_or_create(nome=cat_name)

            # campos base (todos opcionais além do nome)
            bairro    = data.get("bairro") or ""
            endereco  = data.get("endereco") or ""
            numero    = data.get("numero") or ""
            cidade    = (data.get("cidade") or "Araranguá").strip()
            cep       = _digits(data.get("cep"))
            telefone  = data.get("telefone") or ""
            digital   = data.get("digital") or ""
            contato   = data.get("contato") or ""
            cadastrur = data.get("cadastrur") or ""
            app_val   = data.get("app") or ""
            descricao = data.get("descricao") or LOREM_DEFAULT
            cnpj      = _digits(data.get("cnpj"))
            lat, lng  = _extract_latlng_from_maps(data.get("maps"))

            # monta kwargs apenas com campos que existem no model
            kwargs = {
                "user": request.user,
                "nome": nome,
                "categoria": categoria,
                "descricao": descricao,
            }

            if _has_field(Empresa, "bairro"):      kwargs["bairro"] = bairro
            if _has_field(Empresa, "rua"):         kwargs["rua"] = endereco
            if _has_field(Empresa, "numero"):      kwargs["numero"] = numero
            if _has_field(Empresa, "cidade"):      kwargs["cidade"] = cidade
            if _has_field(Empresa, "cep"):         kwargs["cep"] = cep
            if _has_field(Empresa, "telefone"):    kwargs["telefone"] = telefone
            if _has_field(Empresa, "site"):        kwargs["site"] = digital
            if _has_field(Empresa, "contato_direto"): kwargs["contato_direto"] = contato
            if _has_field(Empresa, "cadastrur"):   kwargs["cadastrur"] = cadastrur
            if _has_field(Empresa, "app"):         kwargs["app"] = app_val
            if _has_field(Empresa, "cnpj"):        kwargs["cnpj"] = cnpj
            if _has_field(Empresa, "latitude") and lat is not None:   kwargs["latitude"] = lat
            if _has_field(Empresa, "longitude") and lng is not None:  kwargs["longitude"] = lng

            emp = Empresa(**kwargs)
            emp.save()
            created += 1

        except Exception as e:
            errors += 1
            msgs.append(f"Linha {line_no}: {e}")

    # se teve erro, devolve como erro (para o JS pintar o drop em vermelho e não redirecionar)
    status_code = 200 if errors == 0 else 400
    return JsonResponse({
        "ok": errors == 0,
        "importados": created,
        "erros": errors,
        "mensagens": msgs[:50],   # manda uma amostra (até 50 linhas)
        "redirect": errors == 0,
        "redirect_url": "/empresas/",
    }, status=status_code)
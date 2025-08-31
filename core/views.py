# core/views.py
from __future__ import annotations

import csv
import io
import re
from io import BytesIO, StringIO
from urllib.parse import urlparse, parse_qs

from django.views.decorators.http import require_http_methods
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

# core/views.py (imports)

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail  # se usar backend real
from django.utils import timezone

from .forms import ProfileForm, StartResetByCpfForm
from .models import PerfilUsuario, Empresa, Categoria

from core.models import Categoria, Empresa
from .forms import CustomLoginForm, EmpresaForm, UserRegistrationForm

# ============================================================
# Constantes / Mapeamentos
# ============================================================

# nomes aceitos (mantém os seus sinônimos)
COLUMN_ALIASES = {
    "cnpj":        ["cnpj"],
    "categoria":   ["ramo atividade", "ramo de atividade", "categoria", "ramo"],
    "nome":        ["nome", "razão social", "razao social"],
    "bairro":      ["bairro", "endereço 2", "endereco 2"],
    "endereco":    ["endereço", "endereco", "logradouro", "endereço completo", "endereco completo", "rua"],
    "numero":      ["número", "numero", "nº", "nro"],
    "cidade":      ["cidade", "municipio", "município"],
    "cep":         ["cep", "c.e.p."],
    "telefone":    ["telefone", "fone", "whatsapp"],
    "contato":     ["contato direto", "contato"],
    "digital":     ["digital", "site / redes", "redes sociais", "site", "instagram", "facebook"],
    "cadastrur":   ["cadastur", "cadas tur", "cadastro tur"],
    "maps":        ["maps", "google maps", "mapa", "link mapa"],
    "app":         ["app", "aplicativo"],
    "descricao":   ["descrição", "descricao", "observacao", "observação", "obs"],
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

def _clip(model_cls, field_name, value):
    """Trunca strings para caber no max_length do campo (se houver)."""
    if value is None:
        return value
    try:
        f = model_cls._meta.get_field(field_name)
    except Exception:
        return value
    if hasattr(f, "max_length") and f.max_length and isinstance(value, str):
        return value[:f.max_length]
    return value


def _maxlen(model_cls, field_name):
    try:
        f = model_cls._meta.get_field(field_name)
        return getattr(f, "max_length", None)
    except Exception:
        return None

def _norm_text(s: str | None) -> str:
    return re.sub(r"[\W_]+", " ", (s or "")).strip().lower()

def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")

def _extract_latlng_from_maps(url):
    try:
        if not url: return None, None
        u = urlparse(url)
        qs = parse_qs(u.query)
        if "q" in qs and "," in qs["q"][0]:
            lat, lng = qs["q"][0].split(",")[:2]
            return float(lat), float(lng)
        m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m: return float(m.group(1)), float(m.group(2))
    except Exception:
        pass
    return None, None

def _alias_match(key_norm: str, alias: str) -> bool:
    """Casa de forma flexível: tokens do alias presentes no cabeçalho."""
    a = _norm_text(alias).split()
    k = key_norm.split()
    return all(t in k for t in a) or key_norm == _norm_text(alias)

def _build_header_map(raw_headers):
    mapping = {}
    for idx, raw in enumerate(raw_headers or []):
        key = _norm_text(raw)
        for canon, alts in COLUMN_ALIASES.items():
            if key in (_norm_text(a) for a in alts):
                mapping[idx] = canon
                break
    return mapping

def _read_rows_from_upload(file_obj, filename):
    name = (filename or "").lower()
    if name.endswith(".csv"):
        data = file_obj.read().decode("utf-8", errors="ignore")
        reader = csv.reader(StringIO(data))
        rows = list(reader)
    else:
        from openpyxl import load_workbook
        wb = load_workbook(file_obj, data_only=True)
        ws = wb.active
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append([(c if c is not None else "") for c in row])
    if not rows: 
        return [], []
    headers = [str(c).strip() for c in rows[0]]
    body    = [[str(c).strip() for c in r] for r in rows[1:]]
    return headers, body

def _norm_text(s): 
    return re.sub(r"[\W_]+"," ",(s or "")).strip().lower()

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

def _looks_url(s):
    s = (s or "").strip()
    return s.startswith("http://") or s.startswith("https://")

def _first_url_in_text(s):
    s = (s or "")
    m = re.search(r'(https?://\S+)', s)
    return m.group(1) if m else None

# ============================================================
# Páginas básicas / Auth
# ============================================================

def home(request):
    empresas = Empresa.objects.all().order_by('-data_cadastro')[:6]
    total_empresas = Empresa.objects.count()
    return render(request, 'home.html', {'empresas': empresas, 'total_empresas': total_empresas})

def sobre(request):
    return render(request, 'core/sobre.html')

def termo_de_servico(request):
    return render(request, 'core/termo_de_servico.html')

def politica_de_privacidade(request):
    return render(request, 'core/politica_de_privacidade.html')

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
@require_http_methods(["GET", "POST"])
def cadastrar_empresa(request):
    initial = {"latitude": "-28.937100", "longitude": "-49.484000"}
    if request.method == 'GET':
        form = EmpresaForm(initial=initial)
        return render(request, 'core/cadastrar_empresa.html', {'form': form, 'is_editing': False})

    # POST
    form = EmpresaForm(request.POST, request.FILES)
    wants_json = (
        'application/json' in (request.headers.get('Accept') or '')
            or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    )

    if form.is_valid():
        empresa = form.save(commit=False)
        empresa.user = request.user
        empresa.save()

        # Resposta JSON para o JS atual
        if wants_json:
            action = 'reset' if 'save_and_add' in request.POST else 'redirect'
            return JsonResponse({
                'status': 'success',
                'message': f"Empresa '{empresa.nome}' cadastrada com sucesso!",
                'action': action,
                'redirect_url': '/suas_empresas/' if action == 'redirect' else ''
            })

        # Fallback para POST sem JS
        messages.success(request, f"Empresa '{empresa.nome}' cadastrada com sucesso!")
        return redirect('suas_empresas')

    # Erros de validação
    if wants_json:
        # devolve o bloco de erros renderizado para o JS mostrar
        html = render_to_string('core/partials/form_errors.html', {'form': form}, request=request)
        return JsonResponse({'ok': False, 'error': 'Erros de validação no formulário.', 'html': html}, status=400)

    return render(request, 'core/cadastrar_empresa.html', {'form': form, 'is_editing': False}, status=400)

@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if empresa.user != request.user:
        raise Http404("Você não tem permissão para editar esta empresa.")

    wants_json = (
        'application/json' in (request.headers.get('Accept') or '')
            or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    )

    if request.method == 'GET':
        form = EmpresaForm(instance=empresa)
        return render(request, 'core/empresa_editar.html', {'form': form, 'empresa': empresa, 'is_editing': True})

    form = EmpresaForm(request.POST, request.FILES, instance=empresa)
    if form.is_valid():
        form.save()

        if wants_json:
            return JsonResponse({
                'status': 'success',
                'message': f"A empresa '{empresa.nome}' foi atualizada com sucesso!",
                'redirect_url': '/suas_empresas/'
            })

        messages.success(request, f"A empresa '{empresa.nome}' foi atualizada com sucesso!")
        return redirect('suas_empresas')

    if wants_json:
        html = render_to_string('core/partials/form_errors.html', {'form': form}, request=request)
        return JsonResponse({'ok': False, 'error': 'Erros de validação no formulário.', 'html': html}, status=400)

    return render(request, 'core/empresa_editar.html', {'form': form, 'empresa': empresa, 'is_editing': True}, status=400)
    
@login_required(login_url='/login/')
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if empresa.user != request.user:
        raise Http404("Você não tem permissão para editar esta empresa.")

    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            # Se a requisição espera JSON, devolve JSON; senão redireciona clássico
            if request.headers.get('accept','').lower().find('application/json') >= 0:
                return JsonResponse({
                    'status':'success',
                    'message': f"A empresa '{empresa.nome}' foi atualizada com sucesso!",
                    'action': 'redirect',
                    'redirect_url': '/suas_empresas/'
                })
            messages.success(request, f"A empresa '{empresa.nome}' foi atualizada com sucesso!")
            return redirect('suas_empresas')
        else:
            if request.headers.get('accept','').lower().find('application/json') >= 0:
                # opcional: sumariza erros
                errs = []
                for f, lst in form.errors.items():
                    for e in lst: errs.append(f"{f}: {e}")
                return JsonResponse({'ok': False, 'error': "Erros de validação.", 'mensagens': errs}, status=400)

    else:
        form = EmpresaForm(instance=empresa)

    # use o template dedicado de edição se criou (passo 3)
    return render(request, 'core/editar_empresa.html', {'form': form, 'empresa': empresa})

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

    categoria_label = None
    if categoria:
        try:
            cat_obj = Categoria.objects.only("nome").get(pk=int(categoria))
            categoria_label = cat_obj.nome
        except (Categoria.DoesNotExist, ValueError, TypeError):
            categoria_label = None  # some em silêncio se não achar

    # Filtros “crus” (úteis se você precisa reconstruir URLs)
    filtros_aplicados = {
        'q': q,
        'categoria': categoria,           # <- ID original (ou string vazia)
        'cidade': cidade,
        'com_imagem_real': '1' if com_imagem_real else '',
        'meus': '1' if meus else '',
    }

    # Filtros legíveis para a UI
    filtros_legiveis = {
        'q': q or None,
        'categoria': categoria_label,     # <- nome da categoria (ou None)
        'cidade': cidade or None,
        'com_imagem_real': com_imagem_real,
        'meus': meus,
    }

    return render(request, 'core/listar_empresas.html', {
        'page_obj': page_obj,
        'filtros_aplicados': filtros_aplicados,
        'filtros_legiveis': filtros_legiveis,
    })

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
    try:
        up = request.FILES.get("arquivo")
        if not up:
            return JsonResponse({"ok": False, "error": "Envie um arquivo .xlsx ou .csv."}, status=400)

        # Lê planilha/CSV
        headers_raw, rows = _read_rows_from_upload(up, up.name)
        if not rows:
            return JsonResponse({"ok": False, "error": "Arquivo vazio."}, status=400)

        header_map = _build_header_map(headers_raw)
        if not header_map:
            return JsonResponse({"ok": False, "error": "Não reconheci nenhum cabeçalho na 1ª linha."}, status=400)

        created, errors = 0, 0
        msgs = []

        # Limites coerentes com core/models.py
        MAX_NOME = 255
        MAX_RUA = 255
        MAX_BAIRRO = 100
        MAX_CIDADE = 100
        MAX_NUMERO = 10
        MAX_CEP = 8
        MAX_TEL = 20
        MAX_CONTATO = 255
        MAX_CADASTUR = 50
        MAX_CNPJ = 18
        MAX_URL = 10000  # teus URLFields aceitarão até o limite do banco; cortamos por segurança

        def clip(s, n): return (s or "")[:n]
        def digits(s):  return re.sub(r"\D", "", s or "")

        def looks_url(s: str) -> bool:
            s = (s or "").strip().lower()
            return s.startswith("http://") or s.startswith("https://")

        def first_url(text: str):
            if not text:
                return None
            m = re.search(r'(https?://\S+)', text)
            return m.group(1) if m else None

        def extract_latlng_from_maps(url: str):
            if not url:
                return None, None
            try:
                # tenta ?q=-28.93,-49.48
                from urllib.parse import urlparse, parse_qs
                u = urlparse(url)
                qs = parse_qs(u.query)
                if "q" in qs and "," in qs["q"][0]:
                    lat, lng = qs["q"][0].split(",")[:2]
                    return float(lat), float(lng)
                # tenta @-28.93,-49.48
                m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
                if m:
                    return float(m.group(1)), float(m.group(2))
            except Exception:
                pass
            return None, None

        from core.models import Empresa, Categoria

        for line_no, r in enumerate(rows, start=2):  # começa na linha 2 por causa do header
            # Mapeia valores por chave canônica
            data = {
                'cnpj': '', 'categoria': '', 'nome': '', 'bairro': '', 'endereco': '', 'numero': '',
                'cidade': '', 'cep': '', 'telefone': '', 'contato': '', 'digital': '', 'cadastrur': '',
                'maps': '', 'app': '', 'descricao': ''
            }
            for idx, canon in header_map.items():
                if idx < len(r):
                    data[canon] = (r[idx] or "").strip()

            # Campos básicos + cortes
            nome      = clip(data.get("nome"), MAX_NOME)
            if not nome:
                errors += 1
                msgs.append(f"Linha {line_no}: Nome ausente.")
                continue

            cat_name  = clip((data.get("categoria") or "Sem Categoria"), 100)
            categoria, _ = Categoria.objects.get_or_create(nome=cat_name)

            bairro    = clip(data.get("bairro"), MAX_BAIRRO)
            endereco  = clip(data.get("endereco"), MAX_RUA)
            numero    = clip(data.get("numero"), MAX_NUMERO)
            cidade    = clip((data.get("cidade") or "Araranguá"), MAX_CIDADE)
            cep       = clip(digits(data.get("cep")), MAX_CEP)

            telefone  = clip(data.get("telefone"), MAX_TEL)
            contato   = clip(data.get("contato"), MAX_CONTATO)
            cadastrur = clip(data.get("cadastrur"), MAX_CADASTUR)
            cnpj      = clip(digits(data.get("cnpj")), MAX_CNPJ)
            descricao = (data.get("descricao") or
                        "Descrição ainda não informada. Este estabelecimento está em "
                        "processo de complementação de dados. Se você é o responsável, "
                        "atualize as informações.")

            # URLs
            digital_txt = (data.get("digital") or "").strip()
            site_url    = digital_txt if looks_url(digital_txt) else first_url(digital_txt)
            site_url    = clip(site_url, MAX_URL) if site_url else None

            maps_txt   = (data.get("maps") or "").strip()
            maps_url   = clip(maps_txt, MAX_URL) if looks_url(maps_txt) else None

            app_txt    = (data.get("app") or "").strip()
            app_url    = clip(app_txt, MAX_URL) if looks_url(app_txt) else None

            # Lat/Lng a partir do MAPS (ou default)
            lat, lng = extract_latlng_from_maps(maps_txt)
            lat = str(lat) if lat is not None else "-28.937100"
            lng = str(lng) if lng is not None else "-49.484000"

            # Grava com savepoint – se 1 falhar, continua as outras
            sid = transaction.savepoint()
            try:
                emp = Empresa(
                    user=request.user,
                    nome=nome,
                    categoria=categoria,
                    descricao=descricao,
                    rua=endereco,
                    bairro=bairro,
                    cidade=cidade,
                    numero=numero,
                    cep=cep,
                    latitude=lat,          # CharField no model
                    longitude=lng,         # idem
                    telefone=telefone,
                    contato_direto=contato,
                    cadastrur=cadastrur,
                    cnpj=cnpj,
                    site=site_url,
                    digital=site_url,      # se preferir não duplicar, remova esta linha
                    maps_url=maps_url,
                    app_url=app_url,
                    # imagem usa o default do model
                )
                emp.save()
                transaction.savepoint_commit(sid)
                created += 1
            except Exception as e:
                transaction.savepoint_rollback(sid)
                errors += 1
                msgs.append(f"Linha {line_no}: {e}")

        # Se houve qualquer erro, devolve 400 para a UI pintar a caixa de upload em vermelho e NÃO redirecionar
        if errors:
            return JsonResponse({
                "ok": False,
                "importados": created,
                "erros": errors,
                "mensagens": msgs[:100],
            }, status=400)

        # Tudo certo -> 200 e pode redirecionar
        return JsonResponse({
            "ok": True,
            "importados": created,
            "erros": 0,
            "mensagens": [],
            "redirect": True,
            "redirect_url": "/empresas/",
        })

    except Exception as e:
        # Nunca devolve 500 “mudo”: sempre explica
        return JsonResponse({
            "ok": False,
            "error": "Erro inesperado ao importar. Tente novamente ou contate o suporte.",
            "detalhe": str(e),
        }, status=500)
    

    # ========== PERFIL DO USUÁRIO ==========
@login_required
def perfil(request):
    perfil = getattr(request.user, 'perfil', None)
    if perfil is None:
        # cria se não existir
        perfil = PerfilUsuario.objects.create(user=request.user, cpf_cnpj='')

    empresas_qtd = Empresa.objects.filter(user=request.user).count()
    entrou_em = request.user.date_joined  # DateTimeField
    entrou_fmt = timezone.localtime(entrou_em).strftime("%m/%Y")

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil')
    else:
        form = ProfileForm(instance=perfil, user=request.user)

    return render(request, 'core/perfil.html', {
        'form': form,
        'empresas_qtd': empresas_qtd,
        'entrou_fmt': entrou_fmt,
    })


# ========== TROCAR SENHA (AUTENTICADO) ==========
@login_required
def trocar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # mantém logado
            messages.success(request, "Senha atualizada com sucesso!")
            return redirect('perfil')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'core/password_change.html', {'form': form})


# ========== ESQUECI A SENHA (E-MAIL PADRÃO DJANGO) ==========
def esqueci_senha_email(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='core/email_password_reset.txt',
                html_email_template_name='core/email_password_reset.html',  # <-- ADICIONE
                subject_template_name='core/email_password_reset_subject.txt',
                from_email=None
            )
            messages.success(request, "Se o e-mail existir no sistema, você receberá um link para alterar sua senha.")
            return redirect('perfil')
    else:
        form = PasswordResetForm()
    return render(request, 'core/password_reset_email.html', {'form': form})


def esqueci_senha_cpf(request):
    msg_privacidade = (
        "Por segurança, se o CPF existir e estiver vinculado a um e-mail, "
        "enviaremos um link de redefinição para esse e-mail."
    )
    if request.method == 'POST':
        form = StartResetByCpfForm(request.POST)
        if form.is_valid():
            cpf = form.cleaned_data['cpf_cnpj']
            try:
                perfil = PerfilUsuario.objects.select_related('user').get(cpf_cnpj=cpf)
                if perfil.user.email:
                    prf = PasswordResetForm({'email': perfil.user.email})
                    if prf.is_valid():
                        prf.save(
                            request=request,
                            use_https=request.is_secure(),
                            email_template_name='core/email_password_reset.txt',
                            html_email_template_name='core/email_password_reset.html',  # <-- ADICIONE
                            subject_template_name='core/email_password_reset_subject.txt',
                            from_email=None
                        )
                messages.success(request, msg_privacidade)
                return redirect('login')
            except PerfilUsuario.DoesNotExist:
                messages.success(request, msg_privacidade)
                return redirect('login')
    else:
        form = StartResetByCpfForm()

    return render(request, 'core/password_reset_cpf.html', {'form': form})
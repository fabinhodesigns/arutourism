# core/views.py
from __future__ import annotations
import unicodedata

import csv
import io
import re
from io import BytesIO, StringIO
from urllib.parse import urlparse, parse_qs
from .forms import ProfileForm, CpfUpdateForm, StartResetByCpfForm, CustomLoginForm, EmpresaForm, UserRegistrationForm, TagForm
from .models import PerfilUsuario, Empresa
from django.contrib.auth import authenticate
from .models import Tag
from django.contrib.admin.views.decorators import staff_member_required

import logging
logger = logging.getLogger(__name__)

from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm  # (mantido se você usar em outro lugar)
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
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

from .models import PerfilUsuario, Empresa, Tag

from core.models import Tag, Empresa

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


def _only_digits(s: str) -> str:
    import re
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

def _wants_json(request):
    h = (request.headers.get("Accept") or "").lower()
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in h


def _ident_kind(ident: str) -> str:
    ident = (ident or "").strip()
    if "@" in ident and "." in ident:
        return "email"
    digits = re.sub(r"\D+", "", ident)
    if len(digits) >= 11:
        return "cpf"
    return "username"

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
            if _wants_json(request):
                return JsonResponse({"ok": True, "redirect": reverse("login")})
            return redirect('login')

        if _wants_json(request):
            # serializa erros por campo
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()

    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        ident = (request.POST.get('identificador') or "").strip()
        pwd = request.POST.get('password') or ""
        
        # --- LÓGICA DE LOGIN MANUAL INSERIDA AQUI ---
        user_obj = None
        
        # 1. Determina o tipo de identificador e busca o usuário
        if '@' in ident:
            # Busca por e-mail
            user_obj = User.objects.filter(email__iexact=ident).first()
        elif re.match(r'^\d{11}$|^\d{14}$', re.sub(r'\D', '', ident)):
            # Busca por CPF
            digits = re.sub(r'\D', '', ident)
            perfil = PerfilUsuario.objects.select_related("user").filter(cpf_cnpj=digits).first()
            if perfil:
                user_obj = perfil.user
        else:
            # Por padrão, busca por username
            user_obj = User.objects.filter(username__iexact=ident).first()

        # 2. Se encontrou um usuário, tenta autenticar com a senha
        if user_obj:
            # IMPORTANTE: Usamos o user_obj.username para o authenticate!
            user = authenticate(request, username=user_obj.username, password=pwd)
            
            if user is not None:
                # Autenticação bem-sucedida!
                if user.is_active:
                    print(f"[LOGIN] Autenticação manual OK para user.id={user.id}")
                    auth_login(request, user)
                    
                    # Lógica para resposta JSON ou redirect
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({"ok": True, "redirect": reverse("home")})
                    return redirect('home')
                else:
                    # Usuário inativo
                    print(f"[LOGIN] Falha: usuário '{user.username}' está inativo.")
                    messages.error(request, 'Esta conta está desativada.')
            else:
                # Senha incorreta
                print(f"[LOGIN] Falha: Senha incorreta para o usuário '{user_obj.username}'.")
                messages.error(request, 'Por favor, verifique seu identificador e senha.')
        else:
            # Usuário não encontrado
            print(f"[LOGIN] Falha: Nenhum usuário encontrado para o identificador '{ident}'.")
            messages.error(request, 'Por favor, verifique seu identificador e senha.')
        
        # Se chegou até aqui, o login falhou.
        # Prepara a resposta de erro.
        form = CustomLoginForm(request.POST) # Para reenviar o form com os dados
        
        if request.headers.get('X-Requested-with') == 'XMLHttpRequest':
             # Pega a última mensagem de erro para enviar no JSON
            error_message = str(list(messages.get_messages(request))[-1])
            return JsonResponse({
                "ok": False, 
                "errors": [{"message": error_message}]
            }, status=400)
            
        # Para requisições normais, renderiza a página com a mensagem de erro
        return render(request, 'core/login.html', {'form': form})

    # GET
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

@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def cadastrar_empresa(request):
    initial = {"latitude": "-28.937100", "longitude": "-49.484000"}

    wants_json = (
        'application/json' in (request.headers.get('Accept') or '')
        or (request.headers.get('x-requested-with') == 'XMLHttpRequest')
    )

    if request.method == 'GET':
        form = EmpresaForm(initial=initial)
        return render(request, 'core/cadastrar_empresa.html', {
            'form': form,
            'is_editing': False
        })

    form = EmpresaForm(request.POST, request.FILES)
    if form.is_valid():
        empresa = form.save(commit=False)
        empresa.user = request.user
        empresa.save()

        if wants_json:
            action = 'reset' if 'save_and_add' in request.POST else 'redirect'
            return JsonResponse({
                'ok': True,
                'status': 'success',
                'message': f"Empresa '{empresa.nome}' cadastrada com sucesso!",
                'action': action,
                'redirect_url': reverse('suas_empresas') if action == 'redirect' else ''
            })

        messages.success(request, f"Empresa '{empresa.nome}' cadastrada com sucesso!")
        return redirect('suas_empresas')

    if wants_json:
        html = render_to_string('core/partials/form_errors.html', {'form': form}, request=request)
        return JsonResponse(
            {'ok': False, 'error': 'Erros de validação no formulário.', 'html': html},
            status=400
        )

    return render(request, 'core/cadastrar_empresa.html', {
        'form': form,
        'is_editing': False
    }, status=400)

@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def editar_empresa(request, slug):
    empresa = get_object_or_404(Empresa, slug=slug)

    # dono ou superuser
    if empresa.user_id != request.user.id and not request.user.is_superuser:
        raise Http404("Você não tem permissão para editar esta empresa.")

    wants_json = (
        'application/json' in (request.headers.get('Accept') or '')
        or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    )

    if request.method == 'GET':
        form = EmpresaForm(instance=empresa)
    else:
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            if wants_json:
                return JsonResponse({'ok': True, 'redirect_url': reverse('suas_empresas')})
            messages.success(request, f"A empresa “{empresa.nome}” foi atualizada com sucesso!")
            return redirect('suas_empresas')

        if wants_json:
            html = render_to_string('core/partials/form_errors.html', {'form': form}, request=request)
            return JsonResponse({'ok': False, 'html': html}, status=400)

    return render(request, 'core/editar_empresa.html', {
        'form': form,
        'empresa': empresa,
    }, status=(400 if request.method == 'POST' else 200))

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

def empresa_detalhe(request, slug):
    empresa = get_object_or_404(Empresa, slug=slug)
    return render(request, 'core/empresa_detalhe.html', {'empresa': empresa})

def listar_empresas(request):
    empresas = Empresa.objects.all().order_by('-id')

    # Pega os parâmetros da URL
    q = (request.GET.get('q') or '').strip()
    tag_id = (request.GET.get('tag') or '').strip()
    cidade = (request.GET.get('cidade') or '').strip()
    # ... outros filtros que você tenha

    # --- LÓGICA DE BUSCA GERAL (TEXTO) ---
    if q:
        empresas = empresas.filter(
            Q(nome__icontains=q) |
            Q(descricao__icontains=q) |
            Q(bairro__icontains=q) |
            Q(cidade__icontains=q) |
            Q(tags__nome__icontains=q)
        ).distinct()

    # --- NOVA LÓGICA DE BUSCA HIERÁRQUICA POR TAG ---
    tag_label = None
    if tag_id:
        try:
            # 1. Pega a tag selecionada no banco
            selected_tag = Tag.objects.prefetch_related('children').get(id=tag_id)
            tag_label = selected_tag.nome

            # 2. Pega os IDs de todas as suas "filhas" (subcategorias)
            child_ids = list(selected_tag.children.values_list('id', flat=True))

            # 3. VERIFICA A REGRA:
            if child_ids:
                # Se a tag tem filhas, ela é uma "mãe".
                # Buscamos empresas que tenham a tag "mãe" OU qualquer uma das "filhas".
                search_ids = [selected_tag.id] + child_ids
                empresas = empresas.filter(tags__id__in=search_ids).distinct()
            else:
                # Se não tem filhas, é uma subcategoria ou uma tag sozinha.
                # Buscamos apenas por empresas com essa tag específica.
                empresas = empresas.filter(tags__id=tag_id)

        except (Tag.DoesNotExist, ValueError):
            # Se o ID da tag for inválido, não faz nada e mostra todos os resultados
            pass
    # --- FIM DA NOVA LÓGICA ---
    
    if cidade:
        empresas = empresas.filter(cidade__iexact=cidade)
    # ... outros filtros

    # Paginação (mantém o que você já tinha)
    paginator = Paginator(empresas, 12)
    page_obj = paginator.get_page(request.GET.get('page') or 1)

    # Lógica de resposta AJAX (mantém o que você já tinha)
    is_ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest') or (request.GET.get('ajax') == '1')
    if is_ajax:
        html = render_to_string('core/partials/empresas_cards.html', {'page_obj': page_obj}, request=request)
        return JsonResponse({'html': html, 'has_next': page_obj.has_next(),
                             'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None})

    # Contexto para o template
    filtros_aplicados = { 'q': q, 'tag': tag_id, 'cidade': cidade }
    filtros_legiveis = { 'q': q or None, 'tag': tag_label, 'cidade': cidade or None }

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
    """Retorna tags e cidades em JSON."""
    tags = list(Tag.objects.order_by('nome').values('id', 'nome'))
    
    cidades = list(
        Empresa.objects.exclude(cidade__isnull=True).exclude(cidade__exact='')
        .order_by('cidade').values_list('cidade', flat=True).distinct()
    )
    return JsonResponse({'tags': tags, 'cidades': list(cidades)})

@require_GET
def download_template_empresas(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Empresas"

    headers = [
        "CNPJ",
        "CATEGORIA",
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

@login_required
@require_POST
@transaction.atomic
def importar_empresas_arquivo(request):
    created = 0
    errors = 0
    msgs = []

    try:
        up = request.FILES.get("arquivo")
        if not up:
            return JsonResponse({"ok": False, "error": "Envie um arquivo .xlsx ou .csv."}, status=400)

        headers_raw, rows = _read_rows_from_upload(up, up.name)
        if not rows:
            return JsonResponse({"ok": False, "error": "Arquivo vazio."}, status=400)

        header_map = _build_header_map(headers_raw)

        for line_no, r in enumerate(rows, start=2):
            data = {
                'cnpj': '', 'categoria': '', 'nome': '', 'bairro': '', 'endereco': '', 'numero': '',
                'cidade': '', 'cep': '', 'telefone': '', 'contato': '', 'digital': '',
                'cadastrur': '', 'maps': '', 'app': '', 'descricao': ''
            }
            for idx, canon in header_map.items():
                if idx < len(r): data[canon] = (r[idx] or "").strip()

            nome = _clip(Empresa, "nome", data.get("nome"))
            if not nome:
                errors += 1
                msgs.append(f"Linha {line_no}: O campo 'nome' é obrigatório.")
                continue

            tags_str = data.get("categoria", "")
            tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
            tag_objects = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(nome=name)
                tag_objects.append(tag)

            bairro    = _clip(Empresa, "bairro", data.get("bairro"))
            endereco  = _clip(Empresa, "rua", data.get("endereco"))
            numero    = _clip(Empresa, "numero", data.get("numero"))
            cidade    = _clip(Empresa, "cidade", (data.get("cidade") or "Araranguá"))
            cep       = _clip(Empresa, "cep", _digits(data.get("cep")))
            telefone  = _clip(Empresa, "telefone", _digits(data.get("telefone")))
            contato   = _clip(Empresa, "contato_direto", data.get("contato"))
            cadastrur = _clip(Empresa, "cadastrur", data.get("cadastrur"))
            cnpj      = _clip(Empresa, "cnpj", _digits(data.get("cnpj")))
            descricao = (data.get("descricao") or DEFAULT_DESC)
            digital_txt = data.get("digital", "").strip()
            site_url = _first_url_in_text(digital_txt)
            maps_txt = data.get("maps", "").strip()
            maps_url = maps_txt if _looks_url(maps_txt) else None
            app_txt  = data.get("app", "").strip()
            app_url  = app_txt if _looks_url(app_txt) else None
            lat, lng = _extract_latlng_from_maps(maps_txt)

            try:
                emp = Empresa(
                    user=request.user, nome=nome, descricao=descricao,
                    rua=endereco, bairro=bairro, cidade=cidade, numero=numero, cep=cep,
                    latitude=str(lat) if lat is not None else None, 
                    longitude=str(lng) if lng is not None else None,
                    telefone=telefone, contato_direto=contato,
                    cadastrur=cadastrur, cnpj=cnpj, site=site_url, digital=site_url,
                    maps_url=maps_url, app_url=app_url,
                )
                emp.save()
                
                if tag_objects:
                    emp.tags.set(tag_objects)
                
                created += 1
            except Exception as e:
                errors += 1
                msgs.append(f"Linha {line_no}: Erro ao salvar no banco: {e}")

        if errors > 0:
            return JsonResponse({"ok": False, "importados": created, "erros": errors, "mensagens": msgs[:100]}, status=400)
            
        return JsonResponse({"ok": True, "importados": created, "erros": 0, "mensagens": []})
        
    except Exception as e:
        logger.error(f"Erro catastrófico na importação: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": f"Erro inesperado: {e}"}, status=500)
    
    
@login_required
def perfil(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=request.user,
        defaults={"cpf_cnpj": "", "full_name": request.user.get_full_name() or request.user.username},
    )

    empresas_qtd = Empresa.objects.filter(user=request.user).count()
    entrou_fmt = timezone.localtime(request.user.date_joined).strftime("%m/%Y")

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil')
    else:
        form = ProfileForm(instance=perfil, user=request.user)

    cpf_form = CpfUpdateForm(request.user) 

    return render(request, 'core/perfil.html', {
        'form': form,
        'cpf_form': cpf_form,
        'empresas_qtd': empresas_qtd,
        'entrou_fmt': entrou_fmt,
    })

@login_required
def trocar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, "Senha atualizada com sucesso!")
            return redirect('perfil')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'core/password_change.html', {'form': form})


def esqueci_senha_email(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='core/email_password_reset.txt',
                html_email_template_name='core/email_password_reset.html',
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
        "Por segurança, se o CPF/CNPJ existir e estiver vinculado a um e-mail, "
        "enviaremos um link de redefinição para esse e-mail."
    )
    if request.method == 'POST':
        form = StartResetByCpfForm(request.POST)
        if form.is_valid():
            cpf_digits = form.cleaned_data['cpf_cnpj']  
            perfil = (PerfilUsuario.objects
                      .select_related('user')
                      .filter(cpf_cnpj=cpf_digits)
                      .first())

            if perfil and perfil.user.email:
                prf = PasswordResetForm({'email': perfil.user.email})
                if prf.is_valid():
                    prf.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='core/email_password_reset.txt',
                        html_email_template_name='core/email_password_reset.html',
                        subject_template_name='core/email_password_reset_subject.txt',
                        from_email=None
                    )
                    logger.info("Password reset enviado por CPF %s → %s", cpf_digits, perfil.user.email)
                else:
                    logger.warning("PasswordResetForm inválido para e-mail %s (CPF %s)", perfil.user.email, cpf_digits)
            else:
                logger.info("CPF/CNPJ não localizado ou sem e-mail cadastrado: %s", cpf_digits)

            messages.success(request, msg_privacidade)
            return redirect('perfil')
    else:
        form = StartResetByCpfForm()

    return render(request, 'core/password_reset_cpf.html', {'form': form})

@login_required
@require_POST
def perfil_alterar_cpf(request):
    with transaction.atomic():
        perfil = (PerfilUsuario.objects
                  .select_for_update()
                  .select_related('user')
                  .get(user=request.user))

        form = CpfUpdateForm(request.user, request.POST)
        if not form.is_valid():
            form_profile = ProfileForm(instance=perfil, user=request.user)
            empresas_qtd = Empresa.objects.filter(user=request.user).count()
            entrou_fmt = timezone.localtime(request.user.date_joined).strftime("%m/%Y")
            return render(request, 'core/perfil.html', {
                'form': form_profile,
                'cpf_form': form,
                'empresas_qtd': empresas_qtd,
                'entrou_fmt': entrou_fmt,
            }, status=400)

        novo_cpf = form.cleaned_data["cpf_cnpj"]
        if _only_digits(perfil.cpf_cnpj) == novo_cpf:
            messages.info(request, "O CPF informado é igual ao atual.")
            return redirect('perfil')

        try:
            perfil.cpf_cnpj = novo_cpf 
            perfil.save(update_fields=["cpf_cnpj"])
        except IntegrityError:
            messages.error(request, "Este CPF já está em uso por outra conta.")
            return redirect('perfil')

    messages.success(request, "CPF atualizado com sucesso!")
    return redirect('perfil')


def page_not_found(request, exception):
    return render(request, 'core/404.html', status=500)

def server_error(request):
    return render(request, 'core/500.html', status=500)

def senha_redefinida_redirect(request):
    messages.success(request, "Senha redefinida com sucesso! Faça login para continuar.")
    return redirect('login')

@login_required
@staff_member_required
def gerenciar_tags(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        tag_id = request.POST.get('tag_id')

        if action == 'add':
            form = TagForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Tag '{form.cleaned_data['nome']}' criada com sucesso.")
            else:
                messages.error(request, "Erro ao criar a tag: " + form.errors.as_text())

        elif action == 'edit' and tag_id:
            tag = get_object_or_404(Tag, id=tag_id)
            form = TagForm(request.POST, instance=tag)
            if form.is_valid():
                form.save()
                messages.success(request, f"Tag '{form.cleaned_data['nome']}' renomeada com sucesso.")
            else:
                messages.error(request, "Erro ao renomear: " + form.errors.as_text())

        elif action == 'delete' and tag_id:
            try:
                tag = get_object_or_404(Tag, id=tag_id)
                tag_nome = tag.nome
                tag.delete()
                messages.success(request, f"Tag '{tag_nome}' excluída com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao excluir a tag: {e}")
        
        elif action == 'update_children' and tag_id:
            parent_tag = get_object_or_404(Tag, id=tag_id)
            child_ids = request.POST.getlist('children')

            child_tags = Tag.objects.filter(id__in=child_ids)
            parent_tag.children.set(child_tags)
            parent_tag.children.exclude(id__in=child_ids).update(parent=None)

            messages.success(request, f"Subcategorias de '{parent_tag.nome}' atualizadas com sucesso.")

        return redirect('gerenciar_tags')

    all_tags = Tag.objects.all().order_by('nome')
    parent_tags = all_tags.filter(parent__isnull=True).prefetch_related('children')
    
    form = TagForm()
    
    context = {
        'parent_tags': parent_tags,
        'all_tags': all_tags,
        'form': form,
    }
    return render(request, 'core/gerenciar_tags.html', context)
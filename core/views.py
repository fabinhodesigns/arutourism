from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout
from .forms import UserRegistrationForm, EmpresaForm, CustomLoginForm
from django.contrib import messages
from django.shortcuts import render, redirect
from core.models import Empresa, Categoria
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
import re
import csv, io, re
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from openpyxl import Workbook

DEFAULT_DESC = (
    "Este estabelecimento faz parte do inventário turístico municipal. "
    "Descrição a ser atualizada em breve. Lorem ipsum dolor sit amet, "
    "consectetur adipiscing elit, sed do eiusmod tempor."
)

def home(request):
    empresas = Empresa.objects.all().order_by('-data_cadastro')[:6]  # pega só 6
    total_empresas = Empresa.objects.count()
    return render(request, 'home.html', {
        'empresas': empresas,
        'total_empresas': total_empresas,
    })

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
        else:
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
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            return render(request, 'core/login.html', {'form': form})
    else:
        form = CustomLoginForm()
    return render(request, 'core/login.html', {'form': form})

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

    return render(request, 'core/cadastrar_empresa.html', {
        'form': form,
        'is_editing': True
    })

@login_required(login_url='/login/')
def suas_empresas(request):
    empresas = Empresa.objects.filter(user=request.user).order_by('-data_cadastro')

    paginator = Paginator(empresas, 6) 
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('core/partials/empresas_cards.html', {'page_obj': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    return render(request, 'core/suas_empresas.html', {'page_obj': page_obj})

@login_required(login_url='/login/')
def cadastrar_empresa(request):
    if request.method == 'GET':
        form = EmpresaForm()
        return render(request, 'core/cadastrar_empresa.html', {'form': form})

    if request.method == 'POST':
        post_data = request.POST.copy()

        # saneia cep
        if 'cep' in post_data:
            post_data['cep'] = re.sub(r'\D', '', post_data['cep'])

        form = EmpresaForm(post_data, request.FILES)

        if form.is_valid():
            empresa = form.save(commit=False)
            # descrição padrão
            if not (empresa.descricao or '').strip():
                empresa.descricao = DEFAULT_DESC

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

def listar_usuarios(request):
    if not request.user.is_authenticated:
        return redirect('login') 
    if request.user.is_superuser: 
        usuarios = User.objects.all() 
    else:
        usuarios = User.objects.filter(id=request.user.id) 
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

def logout_view(request):
    logout(request)
    return redirect('login') 

def buscar_empresas(request):
    """
    Alias compatível: usa a mesma listagem por GET.
    /empresas/buscar/ -> mesma saída de listar_empresas
    """
    return listar_empresas(request)

def filtros_empresas(request):
    """
    Mantém endpoint JSON para quem ainda chama /empresas/filtros/.
    Hoje o header novo não depende disso, mas deixamos compatível.
    """
    from core.models import Categoria, Empresa
    categorias = list(Categoria.objects.order_by('nome').values('id', 'nome'))
    cidades = list(
        Empresa.objects.exclude(cidade__isnull=True).exclude(cidade__exact='')
        .order_by('cidade').values_list('cidade', flat=True).distinct()
    )
    return JsonResponse({'categorias': categorias, 'cidades': list(cidades)})

def empresa_detalhe(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    return render(request, 'core/empresa_detalhe.html', {'empresa': empresa})

def _query_empresas(params, user):
    q = params.get('q', '').strip()
    cat_id = params.get('categoria') or ''
    cidade = params.get('cidade', '').strip()
    com_imagem_real = params.get('com_imagem_real') == '1'
    somente_meus = params.get('meus') == '1' and user.is_authenticated

    qs = Empresa.objects.all().select_related('categoria', 'user').order_by('-id')

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(categoria__nome__icontains=q) |
            Q(descricao__icontains=q) |
            Q(bairro__icontains=q) |
            Q(cidade__icontains=q)
        )
    if cat_id:
        qs = qs.filter(categoria_id=cat_id)
    if cidade:
        qs = qs.filter(cidade__iexact=cidade)
    if com_imagem_real:
        qs = qs.exclude(imagem__icontains='placeholders/sem_imagem.png')
    if somente_meus:
        qs = qs.filter(user=user)

    return qs

def listar_empresas(request):
    # filtros existentes (mantém o que você já tem)
    empresas = Empresa.objects.all().order_by('-id')

    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    cidade = request.GET.get('cidade', '').strip()
    com_imagem_real = request.GET.get('com_imagem_real') == '1'
    meus = request.GET.get('meus') == '1'

    if q:
        from django.db.models import Q
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
        empresas = empresas.exclude(imagem='')  # ajuste conforme seu field

    if meus and request.user.is_authenticated:
        empresas = empresas.filter(user=request.user)

    # paginação
    paginator = Paginator(empresas, 12)  # 12 por página (como você pediu)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    # detecta ajax por header OU por ?ajax=1
    is_ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest') or (request.GET.get('ajax') == '1')

    if is_ajax:
        html = render_to_string('core/partials/empresas_cards.html', {'page_obj': page_obj}, request=request)
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    # filtros_aplicados usados no template
    filtros_aplicados = {
        'q': q,
        'categoria': categoria,
        'cidade': cidade,
        'com_imagem_real': '1' if com_imagem_real else '',
        'meus': '1' if meus else '',
    }

    return render(request, 'core/listar_empresas.html', {
        'page_obj': page_obj,
        'filtros_aplicados': filtros_aplicados,
    })

@login_required(login_url='/login/')
def modelo_empresas_xlsx(request):
    """
    Gera um XLSX com cabeçalhos + 1 linha de exemplo.
    Ajuste os nomes dos campos conforme o seu modelo/tela.
    """
    headers = [
        "CNPJ", "Categoria", "Nome", "Descricao", "Rua", "Bairro",
        "Cidade", "Numero", "CEP", "Telefone", "Email",
        "Latitude", "Longitude", "Facebook", "Instagram", "Site",
        # "ImagemURL"  # opcional: caso você queira importar por URL
    ]

    exemplo = [
        "12.345.678/0001-90", "Pousada", "Pousada Azul",
        "Um ótimo lugar para ficar. (se em branco, será preenchido com um texto padrão)",
        "Rua das Flores", "Centro", "Araranguá", "123", "88900000",
        "(48) 99999-9999", "email@exemplo.com",
        "-28.937100", "-49.484000",
        "https://facebook.com/pousadaazul", "https://instagram.com/pousadaazul",
        "https://pousadaazul.com.br",
        # "https://meus-arquivos/imagem.jpg"
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Empresas"
    ws.append(headers)
    ws.append(exemplo)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    resp = HttpResponse(
        stream.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = 'attachment; filename="modelo_empresas.xlsx"'
    return resp

def _to_float(val, default=None):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(str(val).replace(",", "."))
    except Exception:
        return default

def _clean_cnpj(cnpj):
    if not cnpj:
        return ""
    return re.sub(r'\D', '', str(cnpj))

def _norm(v):
    return (v or "").strip()

@login_required(login_url='/login/')
@transaction.atomic
def importar_empresas(request):
    """
    Recebe um arquivo XLSX/CSV e cria empresas em lote.
    Campos aceitos no header (case-insensitive):
      CNPJ, Categoria, Nome, Descricao, Rua, Bairro, Cidade, Numero, CEP, Telefone, Email,
      Latitude, Longitude, Facebook, Instagram, Site
    Regras:
      - Categoria: cria se não existir
      - Descrição vazia: usa DEFAULT_DESC
      - Latitude/Longitude vazias: usa centro de Araranguá (ajuste se quiser)
      - Imagem: NÃO importada (se quiser, adicione 'ImagemURL' e faça o download/attach)
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método inválido.'}, status=405)

    arquivo = request.FILES.get('arquivo')
    if not arquivo:
        return JsonResponse({'ok': False, 'error': 'Envie um arquivo .xlsx ou .csv.'}, status=400)

    filename = arquivo.name.lower()
    rows = []
    headers = []

    try:
        if filename.endswith('.xlsx'):
            from openpyxl import load_workbook
            wb = load_workbook(arquivo, data_only=True)
            ws = wb.active
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [(_norm(c)).lower() for c in row]
                else:
                    rows.append([c for c in row])
        elif filename.endswith('.csv'):
            decoded = arquivo.read().decode('utf-8', errors='ignore')
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(decoded.splitlines()[0])
            reader = csv.reader(io.StringIO(decoded), dialect)
            for i, row in enumerate(reader):
                if i == 0:
                    headers = [(_norm(c)).lower() for c in row]
                else:
                    rows.append(row)
        else:
            return JsonResponse({'ok': False, 'error': 'Formato não suportado. Use .xlsx ou .csv.'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Falha ao ler arquivo: {e}'}, status=400)

    # mapeia índices
    def col(name):
        name = name.lower()
        try:
            return headers.index(name)
        except ValueError:
            return None

    idx = {
        'cnpj': col('cnpj'),
        'categoria': col('categoria'),
        'nome': col('nome'),
        'descricao': col('descricao'),
        'rua': col('rua'),
        'bairro': col('bairro'),
        'cidade': col('cidade'),
        'numero': col('numero'),
        'cep': col('cep'),
        'telefone': col('telefone'),
        'email': col('email'),
        'lat': col('latitude'),
        'lng': col('longitude'),
        'facebook': col('facebook'),
        'instagram': col('instagram'),
        'site': col('site'),
        # 'imgurl': col('imagemurl'),  # se desejar
    }

    obrigatorios = ['nome']  # você pode exigir mais
    ok_count, err_count = 0, 0
    erros = []

    for r, row in enumerate(rows, start=2):  # inicia em 2 por causa do header
        try:
            def v(key):
                i = idx.get(key)
                return _norm(row[i]) if i is not None and i < len(row) else ""

            nome = v('nome')
            if not nome:
                raise ValueError("Nome ausente.")

            categoria_nome = v('categoria')
            categoria_obj = None
            if categoria_nome:
                categoria_obj, _ = Categoria.objects.get_or_create(nome=categoria_nome)

            empresa = Empresa(
                user=request.user,
                nome=nome,
                descricao= v('descricao') or DEFAULT_DESC,
                rua=v('rua'),
                bairro=v('bairro'),
                cidade=v('cidade') or "Araranguá",
                numero=v('numero'),
                cep=re.sub(r'\D','', v('cep')),
                telefone=v('telefone'),
                email=v('email'),
                latitude=_to_float(v('lat'), default=-28.937100),
                longitude=_to_float(v('lng'), default=-49.484000),
                facebook=v('facebook'),
                instagram=v('instagram'),
                site=v('site'),
                cnpj=_clean_cnpj(v('cnpj')) if hasattr(Empresa, 'cnpj') else None
            )
            if categoria_obj:
                empresa.categoria = categoria_obj

            # OBS: Imagem via URL (opcional) — precisa de fetch + gravação.
            # if idx.get('imgurl') is not None:
            #   url = v('imgurl')
            #   if url:
            #       # baixar e anexar (requer requests + ContentFile)
            #       pass

            empresa.save()
            ok_count += 1

        except Exception as e:
            err_count += 1
            erros.append(f"Linha {r}: {e}")

    return JsonResponse({
        'ok': True,
        'importados': ok_count,
        'erros': err_count,
        'mensagens': erros[:20],  # limita para não estourar a resposta
        'redirect': True,
        'redirect_url': '/empresas/'
    })
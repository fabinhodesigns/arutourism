from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout
from .forms import UserRegistrationForm, EmpresaForm, CustomLoginForm
from django.contrib import messages
from django.shortcuts import render, redirect
from core.models import Empresa
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
import re

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
        
        if 'cep' in post_data:
            post_data['cep'] = re.sub(r'\D', '', post_data['cep'])
        
        form = EmpresaForm(post_data, request.FILES)

        if form.is_valid():
            empresa = form.save(commit=False)
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
        
        else:
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

def listar_empresas(request):
    empresas = Empresa.objects.all().order_by('-id')
    paginator = Paginator(empresas, 9)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('core/partials/empresas_cards.html', {'page_obj': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    return render(request, 'core/listar_empresas.html', {'page_obj': page_obj})

def empresa_detalhe(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    return render(request, 'core/empresa_detalhe.html', {'empresa': empresa})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from .forms import EmpresaForm

# Home
def home(request):
    return render(request, 'home.html') 

#Sobre
def sobre(request):
    return render(request, 'sobre.html') 

# Página de cadastro
def register(request):
    if request.user.is_authenticated: 
        return redirect('home')
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Página de login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home') 
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def cadastrar_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)  # Passando request.FILES para lidar com o upload de imagem
        if form.is_valid():  # Agora verificamos o formulário, e não o modelo diretamente
            empresa = form.save(commit=False)
            empresa.usuario = request.user  # Associando a empresa ao usuário logado
            empresa.save()  # Salva a empresa no banco de dados
            return redirect('home')  # Redireciona para a página inicial após o cadastro
    else:
        form = EmpresaForm()
    return render(request, 'cadastrar_empresa.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login') 

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

# Excluir usuário
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
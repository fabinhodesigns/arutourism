from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm

# Home
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redireciona para o login se o usuário não estiver autenticado
    return render(request, 'home.html')

# Página de cadastro
def register(request):
    if request.user.is_authenticated:  # Se já estiver logado, redireciona para a página inicial
        return redirect('home')
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redireciona para o login após cadastro
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Página de login
def login_view(request):
    if request.user.is_authenticated:  # Se já estiver logado, redireciona para a página inicial
        return redirect('home')
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redireciona para a home após login
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')  # Redireciona para a página de login após logout

def listar_usuarios(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redireciona se não estiver logado
    if request.user.is_superuser:  # Se for um usuário administrador
        usuarios = User.objects.all()  # Lista todos os usuários
    else:
        usuarios = User.objects.filter(id=request.user.id)  # Lista apenas o próprio usuário
    return render(request, 'accounts/listar_usuarios.html', {'usuarios': usuarios})

def editar_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    if request.user != usuario and not request.user.is_superuser:
        raise Http404("Você não tem permissão para editar este usuário.")  # Verifica se o usuário pode editar
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('listar_usuarios')
    else:
        form = UserRegistrationForm(instance=usuario)
    return render(request, 'accounts/editar_usuario.html', {'form': form})

# Excluir usuário
def excluir_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    if request.user != usuario and not request.user.is_superuser:
        raise Http404("Você não tem permissão para excluir este usuário.")  # Verifica se o usuário pode excluir
    if request.method == 'POST':
        usuario.delete()
        return redirect('listar_usuarios')
    return render(request, 'accounts/excluir_usuario.html', {'usuario': usuario})

def logout_view(request):
    logout(request)
    return redirect('login') 
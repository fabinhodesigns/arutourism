from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),  # Cadastro
    path('login/', views.login_view, name='login'),  # Login
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),  # Lista os usuários
    path('logout/', views.logout_view, name='logout'),  # URL para logout
    path('editar_usuario/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('excluir_usuario/<int:id>/', views.excluir_usuario, name='excluir_usuario'),
]
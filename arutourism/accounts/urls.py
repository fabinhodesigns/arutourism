from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'), 
    path('login/', views.login_view, name='login'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'), 
    path('logout/', views.logout_view, name='logout'),
    path('editar_usuario/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('excluir_usuario/<int:id>/', views.excluir_usuario, name='excluir_usuario'),
]
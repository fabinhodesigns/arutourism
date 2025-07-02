from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from . import views
from django.contrib import admin


urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'), 
    path('logout/', views.logout_view, name='logout'),
    path('editar_usuario/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('excluir_usuario/<int:id>/', views.excluir_usuario, name='excluir_usuario'),
    path('empresa/<int:empresa_id>/', views.empresa_detalhe, name='empresa_detalhe'),
    path('cadastrar_empresa/', views.cadastrar_empresa, name='cadastrar_empresa'),
    path('empresa/<int:empresa_id>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('sobre/', views.sobre, name='sobre'),
    path('termo_de_servico/', views.termo_de_servico, name='termo_de_servico'),
    path('politica_de_privacidade/', views.politica_de_privacidade, name='politica_de_privacidade'),
    path('suas_empresas/', views.suas_empresas, name='suas_empresas')
]
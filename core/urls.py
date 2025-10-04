# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),

    # Páginas estáticas
    path('sobre/', views.sobre, name='sobre'),
    path('termo_de_servico/', views.termo_de_servico, name='termo_de_servico'),
    path('politica_de_privacidade/', views.politica_de_privacidade, name='politica_de_privacidade'),

    # Auth/usuários
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('editar_usuario/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('excluir_usuario/<int:id>/', views.excluir_usuario, name='excluir_usuario'),

    # Empresas
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('empresa/<slug:slug>/', views.empresa_detalhe, name='empresa_detalhe'),
    path('empresa/<slug:slug>/editar/', views.editar_empresa, name='editar_empresa'),
    path('cadastrar_empresa/', views.cadastrar_empresa, name='cadastrar_empresa'),
    path('suas_empresas/', views.suas_empresas, name='suas_empresas'),

    # Busca/filtros (compat)
    path('empresas/buscar/', views.buscar_empresas, name='buscar_empresas'),
    path('empresas/filtros/', views.filtros_empresas, name='filtros_empresas'),

    # Importação em lote + modelo (NOVOS nomes)
    path("empresas/modelo/", views.download_template_empresas, name="download_template_empresas"),
    path("empresas/importar/", views.importar_empresas_arquivo, name="importar_empresas_arquivo"),

     # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/trocar-senha/', views.trocar_senha, name='trocar_senha'),

    # Reset por e-mail (padrão Django, páginas custom)
    path('senha/esqueci/', views.esqueci_senha_email, name='esqueci_senha_email'),
    path('senha/esqueci-cpf/', views.esqueci_senha_cpf, name='esqueci_senha_cpf'),
    # core/urls.py
    
    path('perfil/alterar-cpf/', views.perfil_alterar_cpf, name='perfil_alterar_cpf'),
    path('gerenciar-tags/', views.gerenciar_tags, name='gerenciar_tags'),
    path('imagem-empresa/deletar/<int:imagem_id>/', views.deletar_imagem_empresa, name='deletar_imagem_empresa'),
    path('empresa/<slug:slug>/avaliar/', views.adicionar_avaliacao, name='adicionar_avaliacao'),
    path('avaliacao/deletar/<int:avaliacao_id>/', views.deletar_avaliacao, name='deletar_avaliacao'),
]

# servir mídia local quando DEBUG=True
if settings.DEBUG and settings.MEDIA_URL and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
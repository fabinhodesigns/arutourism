from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from . import views
from django.contrib import admin
from django.conf.urls import handler404


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
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('sobre/', views.sobre, name='sobre'),

    path('test/', views.test_view, name='test'),
]

handler404 = 'django.views.defaults.page_not_found'

# Para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
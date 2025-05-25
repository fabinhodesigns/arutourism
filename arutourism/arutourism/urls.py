from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.home, name='home'),
    path('sobre/', views.sobre, name='sobre'),
    path('', views.home, name='home_redirect'),
    path('accounts/', include('accounts.urls')),    
    path('cadastrar_empresa/', views.cadastrar_empresa, name='cadastrar_empresa'),
    path('empresas/', views.listar_empresas, name='listar_empresas'),
]

# Para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
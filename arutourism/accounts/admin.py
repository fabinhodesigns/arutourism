from django.contrib import admin
from django.contrib.admin import AdminSite
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Empresa 

class CustomAdminSite(AdminSite):
    site_header = "Administração do AruTourism"
    site_title = "AruTourism Admin"
    index_title = "Bem-vindo ao painel administrativo"

admin_site = CustomAdminSite(name='custom_admin')

admin_site.register(User, UserAdmin)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'telefone', 'email', 'site')  # Campos que aparecerão na listagem
    search_fields = ('nome', 'categoria', 'email')  # Campos que serão pesquisáveis
    list_filter = ('categoria',)  # Permite filtrar por categoria
    

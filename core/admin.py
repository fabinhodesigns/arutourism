from django.contrib import admin

from django.contrib import admin
from .models import Categoria, Empresa, PerfilUsuario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome']
    ordering = ['nome']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'email']

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'cpf_cnpj', 'full_name']
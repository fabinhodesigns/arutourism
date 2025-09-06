# core/admin.py

from django.contrib import admin, messages
from django.template.response import TemplateResponse
from .models import Categoria, Empresa, PerfilUsuario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome']
    ordering = ['nome']
    search_fields = ['nome'] # Adicionado para facilitar a busca

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'cidade', 'user')
    list_filter = ('categoria', 'cidade', 'user') # Adicionado para filtragem
    search_fields = ('nome', 'cnpj', 'descricao')
    raw_id_fields = ('user', 'categoria') # Melhora a performance
    actions = ['delete_selected', 'apagar_todas_action']

    @admin.action(description="APAGAR TODAS as empresas…")
    def apagar_todas_action(self, request, queryset):
        """Mostra página de confirmação própria."""
        if not request.user.is_superuser:
            self.message_user(request, "Ação restrita a superusuários.", messages.ERROR)
            return

        if request.POST.get("confirm") == "yes":
            total = Empresa.objects.count()
            Empresa.objects.all().delete()
            self.message_user(request, f"{total} empresas apagadas.", messages.SUCCESS)
            return

        context = {
            **self.admin_site.each_context(request),
            "title": "Tem certeza que deseja APAGAR TODAS as empresas?",
            "opts": self.model._meta,
            "action": "apagar_todas_action",
        }
        return TemplateResponse(request, "admin/confirm_delete_all.html", context)

# --- CORREÇÃO ESTÁ AQUI ---
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    # Usando os campos que REALMENTE existem no modelo PerfilUsuario
    list_display = ('user', 'full_name', 'cpf_cnpj', 'telefone')
    search_fields = ('user__username', 'full_name', 'cpf_cnpj')
    list_filter = ('user__is_staff', 'user__is_superuser', 'user__date_joined')
    raw_id_fields = ('user',) # Melhora performance ao selecionar o usuário
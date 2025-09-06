from django.contrib import admin
from django.contrib import admin
from .models import Categoria, Empresa, PerfilUsuario
from django.contrib import admin, messages
from django.template.response import TemplateResponse
from django.urls import path


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome']
    ordering = ['nome']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'categoria', 'cidade', 'user')
    actions       = ['delete_selected', 'apagar_todas_action']

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

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'categoria', 'cidade', 'user')
    search_fields = ('nome', 'cidade', 'descricao', 'categoria__nome')
    list_filter   = ('categoria', 'cidade', 'user')
    actions       = ['delete_selected']  # garante que o action padrão apareça
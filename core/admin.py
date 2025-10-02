# core/admin.py
from django.contrib import admin, messages
from django.template.response import TemplateResponse
# CORRIGIDO: Importa apenas 'Tag', sem 'Categoria'
from .models import Tag, Empresa, PerfilUsuario

# 1. Admin para PerfilUsuario (sem alterações)
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'cpf_cnpj', 'full_name')
    search_fields = ('user__username', 'cpf_cnpj', 'full_name')

# 2. Admin para Tag (APENAS UMA VEZ)
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nome']
    ordering = ['nome']
    search_fields = ['nome']

# 3. Admin para Empresa (UNIFICADO E CORRIGIDO)
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # CORRIGIDO: Removido 'categoria' do list_display
    list_display = ('nome', 'cidade', 'user', 'data_cadastro')
    # CORRIGIDO: Trocado 'categoria' por 'tags' no filtro
    list_filter = ('cidade', 'user', 'data_cadastro', 'tags') 
    search_fields = ('nome', 'cnpj', 'descricao')
    # CORRIGIDO: Removido 'categoria' do raw_id_fields. 'user' pode ficar se preferir.
    raw_id_fields = ('user',)
    
    # MELHORIA: Adiciona o widget de seleção múltipla amigável
    filter_horizontal = ('tags',)
    
    # MANTIDO: Sua ação customizada está aqui
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
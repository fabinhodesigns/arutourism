from django.contrib import admin, messages
from django.template.response import TemplateResponse
from django.utils.html import format_html 

from .models import Tag, Empresa, PerfilUsuario, ImagemEmpresa, Avaliacao 

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'cpf_cnpj', 'full_name', 'telefone') 
    search_fields = ('user__username', 'cpf_cnpj', 'full_name')
    list_select_related = ('user',) 
    filter_horizontal = ('favoritos',) 

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'parent') 
    list_filter = ('parent',) 
    ordering = ('nome',) 
    search_fields = ('nome',)

@admin.register(ImagemEmpresa)
class ImagemEmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'imagem_thumbnail', 'principal', 'data_upload')
    list_filter = ('empresa', 'principal')
    search_fields = ('empresa__nome',)
    list_select_related = ('empresa',) 
    readonly_fields = ('data_upload',)

    @admin.display(description='Miniatura')
    def imagem_thumbnail(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.imagem.url)
        return "Sem imagem"

@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'user', 'nota', 'data_criacao', 'comentario_curto')
    list_filter = ('empresa', 'user', 'nota', 'data_criacao')
    search_fields = ('empresa__nome', 'user__username', 'comentario')
    list_select_related = ('empresa', 'user') 
    readonly_fields = ('data_criacao',) 
    date_hierarchy = 'data_criacao' 

    @admin.display(description='Comentário (início)')
    def comentario_curto(self, obj):
        return (obj.comentario[:50] + '...') if len(obj.comentario or '') > 50 else obj.comentario

class ImagemEmpresaInline(admin.TabularInline): 
    model = ImagemEmpresa
    extra = 1 
    readonly_fields = ('data_upload',) 

class AvaliacaoInline(admin.TabularInline):
    model = Avaliacao
    extra = 0 
    readonly_fields = ('user', 'nota', 'comentario', 'data_criacao') 
    can_delete = True 

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'user', 'data_cadastro')
    list_filter = ('cidade', 'user', 'data_cadastro', 'tags') 
    search_fields = ('nome', 'slug', 'cnpj', 'descricao') 
    prepopulated_fields = {'slug': ('nome',)} 
    readonly_fields = ('data_cadastro',) 
    raw_id_fields = ('user',) 
    filter_horizontal = ('tags',) 
    
    inlines = [ImagemEmpresaInline, AvaliacaoInline]
    
    actions = ['delete_selected', 'apagar_todas_action']

    @admin.action(description="APAGAR TODAS as empresas…")
    def apagar_todas_action(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "Ação restrita a superusuários.", messages.ERROR)
            return None

        if request.POST.get("confirm") == "yes":
            total = Empresa.objects.count()
            try:
                Empresa.objects.all().delete() 
                self.message_user(request, f"{total} empresas apagadas com sucesso.", messages.SUCCESS)
            except Exception as e:
                 self.message_user(request, f"Erro ao apagar empresas: {e}", messages.ERROR)
            return None 

        context = {
            **self.admin_site.each_context(request),
            "title": "Tem certeza que deseja APAGAR TODAS as empresas?",
            "object_name": "Empresas", 
            "action_name": "apagar_todas_action", 
            "queryset": queryset, 
            "opts": self.model._meta,
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(request, "admin/confirm_delete_all.html", context)


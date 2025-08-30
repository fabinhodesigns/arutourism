from core.models import Categoria, Empresa

def search_filters(request):
    categorias = list(Categoria.objects.order_by('nome').values('id', 'nome'))
    cidades = list(
        Empresa.objects.exclude(cidade__isnull=True).exclude(cidade__exact='')
        .order_by('cidade').values_list('cidade', flat=True).distinct()
    )
    return {
        'GLOBAL_CATEGORIES': categorias,
        'GLOBAL_CITIES': cidades,
    }
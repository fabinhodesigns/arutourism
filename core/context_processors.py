from .models import Tag, Empresa

def search_filters(request):
    tags = list(Tag.objects.order_by('nome').values('id', 'nome')) 
    
    cidades = list(
        Empresa.objects.exclude(cidade__isnull=True).exclude(cidade__exact='')
        .order_by('cidade').values_list('cidade', flat=True).distinct()
    )
    
    return {
        'GLOBAL_TAGS': tags, 
        'GLOBAL_CITIES': cidades,
    }
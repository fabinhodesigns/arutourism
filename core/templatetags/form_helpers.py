from django import template

register = template.Library()

@register.filter(name='get_field_verbose_name')
def get_field_verbose_name(form, field_name):
    """
    Retorna o 'label' (nome amigável) de um campo do formulário.
    Ex: para o campo 'nome_empresa', retorna 'Nome da Empresa'.
    """
    # Verifica se o campo existe no formulário para evitar erros
    if field_name in form.fields:
        # Retorna o label definido no form ou no model. Se não houver, retorna o nome do campo.
        return form.fields[field_name].label or field_name

    # Se, por algum motivo, o nome do campo não for encontrado, apenas formata ele um pouco
    return field_name.replace('_', ' ').capitalize()
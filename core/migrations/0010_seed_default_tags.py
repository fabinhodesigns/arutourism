from django.db import migrations

DEFAULT_TAGS = [
    "Dia",
    "Noite",
    
    "Almoço",
    "Jantar",
    "Café",
    "Lanche",
    
    "Bares",
    "Restaurantes",
    "Pousadas",
    "Hotéis",
    
    "Praia",
    "Cachoeira",
    "Trilha",
    "Turismo Rural",
    "Gastronomia",
    "Compras",
    "Para Família",
    "Música ao Vivo",
]

def create_default_tags(apps, schema_editor):
    """
    Cria as tags padrão no banco de dados.
    """
    Tag = apps.get_model('core', 'Tag')
    for tag_name in DEFAULT_TAGS:
        Tag.objects.get_or_create(nome=tag_name)

def delete_default_tags(apps, schema_editor):
    """
    Remove as tags que foram criadas (para poder reverter a migration).
    """
    Tag = apps.get_model('core', 'Tag')
    Tag.objects.filter(nome__in=DEFAULT_TAGS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_tag_parent'),
    ]

    operations = [
        migrations.RunPython(create_default_tags, reverse_code=delete_default_tags),
    ]
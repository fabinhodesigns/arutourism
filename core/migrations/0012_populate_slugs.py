# Em core/migrations/0012_populate_slugs.py

from django.db import migrations
from django.utils.text import slugify

def generate_slugs(apps, schema_editor):
    Empresa = apps.get_model('core', 'Empresa')
    for empresa in Empresa.objects.all():
        # Não precisa gerar o slug manualmente, o método save() já faz isso
        empresa.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_empresa_slug'), 
    ]

    operations = [
        migrations.RunPython(generate_slugs),
    ]
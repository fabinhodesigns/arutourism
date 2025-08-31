# core/migrations/0004_backfill_lat_lng.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_alter_categoria_nome_alter_empresa_app_url_and_more'),  # EXATAMENTE o nome da sua 0003
    ]

def backfill_latlng(apps, schema_editor):
    Empresa = apps.get_model('core', 'Empresa')
    # Se ainda houver registros antigos sem lat/lng, define os defaults
    Empresa.objects.filter(latitude__isnull=True).update(latitude='-28.937100')
    Empresa.objects.filter(longitude__isnull=True).update(longitude='-49.484000')

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_alter_categoria_nome_alter_empresa_app_url_and_more'),
    ]
    operations = [
        migrations.RunPython(backfill_latlng, migrations.RunPython.noop),
    ]
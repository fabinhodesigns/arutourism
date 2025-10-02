# core/migrations/0008_migrate_categorias_to_tags.py

from django.db import migrations

def migrate_data_forward(apps, schema_editor):
    """
    Pega o nome da Categoria antiga de cada Empresa,
    cria uma Tag com esse nome (ou usa uma existente) e
    associa essa Tag à Empresa.
    """
    try:
        Empresa = apps.get_model('core', 'Empresa')
        Tag = apps.get_model('core', 'Tag')
        Categoria = apps.get_model('core', 'Categoria') # Acessa a versão histórica do modelo
    except LookupError:
        # Se o modelo Categoria já foi removido em uma migração anterior, não faz nada.
        # Isso torna a migração segura para ser re-executada.
        return

    for empresa in Empresa.objects.all():
        # Acessa a categoria antiga através do _meta para segurança
        if hasattr(empresa, 'categoria') and empresa.categoria:
            tag_nome = empresa.categoria.nome.strip()
            if tag_nome:
                tag, created = Tag.objects.get_or_create(nome=tag_nome)
                empresa.tags.add(tag)

class Migration(migrations.Migration):

    dependencies = [
        # IMPORTANTE: Coloque aqui o nome do arquivo da migração anterior
        # Exemplo: '0007_tag_remove_empresa_core_empres_categor_a5ab9f_idx_and_more'
        ('core', '0007_tag_remove_empresa_core_empres_categor_a5ab9f_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_data_forward),
    ]
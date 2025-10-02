# Em core/management/commands/regenerate_slugs.py

from django.core.management.base import BaseCommand
from core.models import Empresa

class Command(BaseCommand):
    help = 'Regenera os slugs para todas as empresas que não têm um.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando a regeneração de slugs...")
        
        empresas_sem_slug = Empresa.objects.filter(slug__isnull=True)
        total = empresas_sem_slug.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma empresa com slug vazio encontrada. Tudo certo!"))
            return

        self.stdout.write(f"Encontradas {total} empresas sem slug. Atualizando...")

        count = 0
        for empresa in empresas_sem_slug:
            empresa.save()  # O método save() vai gerar o slug
            count += 1
            self.stdout.write(f"  -> Slug gerado para: {empresa.nome}")

        self.stdout.write(self.style.SUCCESS(f"Operação concluída! {count} slugs foram gerados."))
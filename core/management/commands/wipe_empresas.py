# Em core/management/commands/limpartabela.py

from django.core.management.base import BaseCommand
from django.db import transaction
# Substitua 'core' pelo nome do seu app e 'Empresa' pelo nome do seu modelo
from core.models import Empresa

class Command(BaseCommand):
    help = 'Apaga todos os dados da tabela de Empresas de forma forçada e segura.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('INICIANDO PROCESSO DE EXCLUSÃO DE DADOS...'))
        
        try:
            # Usar uma transação atômica garante que ou tudo funciona, ou nada é alterado.
            with transaction.atomic():
                total_apagado, _ = Empresa.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'SUCESSO: {total_apagado} registros foram apagados da tabela de Empresas.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERRO: A operação falhou. Nenhum dado foi apagado. Erro: {e}'))
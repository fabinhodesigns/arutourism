# core/management/commands/import_tags.py
import csv
from django.core.management.base import BaseCommand
from core.models import Tag

class Command(BaseCommand):
    help = 'Importa tags de um arquivo CSV.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='O caminho para o arquivo CSV.')

    def handle(self, *args, **options):
        file_path = options['csv_file']
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Se seu arquivo tiver um cabeçalho (ex: "Nome da Tag"), descomente a linha abaixo
                # next(reader) 
                
                self.stdout.write("Iniciando importação de tags...")
                count = 0
                for row in reader:
                    if not row: continue
                    tag_nome = row[0].strip()
                    if tag_nome:
                        tag, created = Tag.objects.get_or_create(nome=tag_nome)
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'  + Tag "{tag_nome}" criada.'))
                            count += 1
                
                self.stdout.write(self.style.SUCCESS(f"\nImportação concluída! {count} novas tags criadas."))
        
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Arquivo não encontrado em: {file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ocorreu um erro inesperado: {e}'))
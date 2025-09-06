from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = "APAGA TODAS as empresas. Use com extremo cuidado."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", choices=["YES"], help="Confirme com YES para executar")
        parser.add_argument("--also-cloud", action="store_true",
                            help="Também remove os arquivos/imagens (se o campo suportar .delete()).")

    def handle(self, *args, **opts):
        allowed = os.environ.get("WIPE_EMPRESAS_ALLOWED") == "1"
        if not allowed:
            self.stderr.write(self.style.ERROR("Bloqueado. Defina WIPE_EMPRESAS_ALLOWED=1 no ambiente para autorizar."))
            return

        if opts.get("confirm") != "YES":
            self.stderr.write(self.style.ERROR("Passe --confirm YES para executar."))
            return

        from core.models import Empresa
        qs = Empresa.objects.all()
        total = qs.count()

        if opts.get("also_cloud"):
            for e in qs.iterator():
                try:
                    if getattr(e, "imagem", None):
                        # se for CloudinaryStorage/ImageField compatível
                        e.imagem.delete(save=False)
                except Exception:
                    pass

        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Empresas apagadas: {total}"))

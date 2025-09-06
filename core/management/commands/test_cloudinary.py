# core/management/commands/test_cloudinary.py
import base64
from datetime import datetime, timezone

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.conf import settings

ONE_BY_ONE_WHITE_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9W0qIasAAAAASUVORK5CYII="
)

class Command(BaseCommand):
    help = "Testa upload no storage (Cloudinary) e imprime a URL pública."

    def add_arguments(self, parser):
        parser.add_argument("--prefix", default="tests", help="Pasta/prefixo no storage (default: tests)")

    def handle(self, *args, **opts):
        storage_cls = getattr(settings, "DEFAULT_FILE_STORAGE", "<não definido>")
        self.stdout.write(self.style.NOTICE(f"DEFAULT_FILE_STORAGE: {storage_cls}"))

        # conteúdo PNG 1x1 para evitar dependências de Pillow
        content = ContentFile(base64.b64decode(ONE_BY_ONE_WHITE_PNG_B64))
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        name = f"{opts['prefix'].rstrip('/')}/ping-{ts}.png"

        saved_path = default_storage.save(name, content)
        url = default_storage.url(saved_path)

        self.stdout.write(self.style.SUCCESS(f"OK: salvo como {saved_path}"))
        self.stdout.write(self.style.SUCCESS(f"URL pública: {url}"))
        self.stdout.write(self.style.NOTICE("Abra a URL em uma aba anônima para validar acesso público."))

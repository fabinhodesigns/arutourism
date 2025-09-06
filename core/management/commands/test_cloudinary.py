import io, base64
from PIL import Image
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

class Command(BaseCommand):
    help = "Sobe uma imagem pequena e imprime a URL pública"

    def handle(self, *args, **opts):
        # PNG pequenininho em memória
        img = Image.new("RGB", (64, 64), (30, 100, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        content = ContentFile(buf.getvalue())

        path = "test_uploads/cloudinary_ping.png"
        saved = default_storage.save(path, content)
        url = default_storage.url(saved)
        self.stdout.write(self.style.SUCCESS(f"OK: {saved}"))
        self.stdout.write(self.style.SUCCESS(f"URL: {url}"))

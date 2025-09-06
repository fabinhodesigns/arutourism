from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

class Command(BaseCommand):
    help = "Envia um e-mail de teste usando as configs atuais"

    def add_arguments(self, parser):
        parser.add_argument("to", nargs="?", default=settings.EMAIL_HOST_USER or "seu@exemplo.com")

    def handle(self, *args, **opts):
        to = opts["to"]
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"Enviando para: {to}")

        msg = EmailMultiAlternatives(
            subject="Teste SMTP ARUTOURISM",
            body="Se você recebeu, o SMTP está OK.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
        )
        msg.attach_alternative(
            "<html><body style='font-family:system-ui'><h3>Teste SMTP</h3><p>OK ✅</p></body></html>",
            "text/html",
        )
        sent = msg.send(fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f"Enviados: {sent}"))

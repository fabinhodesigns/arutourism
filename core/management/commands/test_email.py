from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = "Testa envio de email via settings SMTP"

    def handle(self, *args, **options):
        to = settings.EMAIL_HOST_USER
        sent = send_mail(
            subject="Teste SMTP ARUTOURISM",
            message="Se você recebeu, o SMTP está OK.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Enviados: {sent}"))
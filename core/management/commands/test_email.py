# core/management/commands/test_smtp.py
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

class Command(BaseCommand):
    help = "Testa envio de email via settings SMTP. Uso: python manage.py test_smtp [email_destino]"

    def add_arguments(self, parser):
        parser.add_argument('to', nargs='?', help='E-mail de destino (opcional). Se não vier, usa EMAIL_HOST_USER.')

    def handle(self, *args, **options):
        to = options.get('to') or settings.EMAIL_HOST_USER
        if not to:
            self.stderr.write(self.style.ERROR("Nenhum destinatário. Informe um e-mail ou configure EMAIL_HOST_USER."))
            return

        self.stdout.write(self.style.NOTICE(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}"))
        self.stdout.write(self.style.NOTICE(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', '')}"))
        self.stdout.write(self.style.NOTICE(f"Enviando para: {to}"))

        subject = "Teste SMTP ARUTOURISM"
        text = "Se você recebeu, o SMTP está OK."
        html = """
        <html><body style="font-family:system-ui">
          <h3>Teste SMTP ARUTOURISM</h3>
          <p>Se você recebeu, o SMTP está <strong>OK</strong>.</p>
        </body></html>
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER),
            to=[to],
        )
        msg.attach_alternative(html, "text/html")
        sent = msg.send(fail_silently=False)

        self.stdout.write(self.style.SUCCESS(f"Enviados: {sent}"))

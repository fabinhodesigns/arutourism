from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario

@receiver(post_save, sender=User)
def ensure_perfil(sender, instance, created, **kwargs):
    # Garante que SEMPRE exista um PerfilUsuario
    PerfilUsuario.objects.get_or_create(
        user=instance,
        defaults={
            "cpf_cnpj": "",
            "full_name": instance.get_full_name() or instance.username,
        },
    )
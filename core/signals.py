# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from .models import PerfilUsuario
from core.utils.cpf import generate_unique_cpf

@receiver(post_save, sender=User)
def ensure_perfil(sender, instance: User, created: bool, **kwargs):
    # Cria perfil só quando o User nasce; se já existir, não mexe.
    if not created:
        return

    # Gera CPF válido/único para não deixar vazio e não quebrar unique
    cpf = generate_unique_cpf(PerfilUsuario, "cpf_cnpj")

    # Evita race condition com transação/retentativa
    for _ in range(3):
        try:
            with transaction.atomic():
                PerfilUsuario.objects.get_or_create(
                    user=instance,
                    defaults={
                        "cpf_cnpj": cpf,
                        "full_name": instance.get_full_name() or instance.username,
                    },
                )
            break
        except IntegrityError:
            cpf = generate_unique_cpf(PerfilUsuario, "cpf_cnpj")

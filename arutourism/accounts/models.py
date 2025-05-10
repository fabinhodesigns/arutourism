from django.contrib.auth.models import User
from django.db import models  # Adicionando a importação do models

class CustomUser(User):
    cpf_cnpj = models.CharField(max_length=18, blank=True, null=True)  # Exemplo de campo adicional
    # Adicione outros campos personalizados que você deseja
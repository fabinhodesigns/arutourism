from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def nome_limpo(self):
        return self.nome.split('(')[0].strip()

    def __str__(self):
        return self.nome


class Empresa(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='empresas')
    nome = models.CharField(max_length=255)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    descricao = models.TextField()

    rua = models.CharField(max_length=255)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    numero = models.CharField(max_length=10)
    cep = models.CharField(max_length=8)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    site = models.URLField(blank=True, null=True)
    imagem = models.ImageField(upload_to='empresas/', blank=True, null=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
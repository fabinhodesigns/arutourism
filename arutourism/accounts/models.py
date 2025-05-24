from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Empresa(models.Model):
    nome = models.CharField(max_length=255)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='empresas')
    descricao = models.TextField()
    endereco = models.CharField(max_length=255)
    telefone = models.CharField(max_length=15)
    email = models.EmailField()
    site = models.URLField(blank=True, null=True)
    imagem = models.ImageField(upload_to='empresa_imagens/', blank=True, null=True)

    def __str__(self):
        return self.nome
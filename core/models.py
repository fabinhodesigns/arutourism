# core/models.py
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
    def nome_limpo(self):
        return self.nome.split('(')[0].strip()
    def __str__(self):
        return self.nome

class Empresa(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='empresas', db_index=True)

    # essenciais
    nome = models.CharField(max_length=255, db_index=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, db_index=True)

    # identificação
    cnpj = models.CharField(max_length=18, blank=True, null=True, db_index=True)
    cadastrur = models.CharField(max_length=50, blank=True, null=True)

    # descrição / endereço granular
    descricao = models.TextField(blank=True, default='')
    rua = models.CharField(max_length=255, blank=True, default='')
    bairro = models.CharField(max_length=100, blank=True, default='')
    cidade = models.CharField(max_length=100, blank=True, default='')
    numero = models.CharField(max_length=10, blank=True, default='')
    cep = models.CharField(max_length=8, blank=True, default='')
    endereco_full = models.CharField(max_length=255, blank=True, default='')  # caso venha endereço completo no arquivo

    # localização: obrigatória com default (centro de Araranguá)
    latitude = models.CharField(max_length=50, null=False, blank=False, default='-28.937100')
    longitude = models.CharField(max_length=50, null=False, blank=False, default='-49.484000')

    # contatos
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    contato_direto = models.CharField(max_length=255, blank=True, null=True)  # pessoa de contato

    # presença digital
    site = models.URLField(blank=True, null=True)
    digital = models.URLField(blank=True, null=True)     # link “Digital” (se vier na planilha)
    maps_url = models.URLField(blank=True, null=True)    # link Google Maps (se vier na planilha “MAPS”)
    app_url = models.URLField(blank=True, null=True)     # link de App (se vier na planilha “APP”)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)

    # imagem: OBRIGATÓRIA com default (arquivo local ou Cloudinary em prod)
    imagem = models.ImageField(upload_to='empresas/', null=False, blank=False,
                               default='placeholders/sem_imagem.png')

    # flags existentes
    sem_telefone = models.BooleanField(default=False)
    sem_email = models.BooleanField(default=False)

    data_cadastro = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['categoria']),
            models.Index(fields=['cidade', 'bairro']),
            models.Index(fields=['cnpj']),
        ]
        # evita nomes exatamente iguais do mesmo usuário (se quiser)
        # unique_together = (('user', 'nome'),)

    def __str__(self):
        return self.nome
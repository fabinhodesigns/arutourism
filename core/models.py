# core/models.py
from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    def __str__(self):
        return self.user.username
    
    @property
    def display_name(self):
        full = (self.full_name or self.user.get_full_name() or self.user.first_name or "").strip()
        if full:
            return full.split()[0]
        return (self.user.username or (self.user.email.split("@")[0] if self.user.email else "Você"))
    
class Categoria(models.Model):
    nome = models.CharField(max_length=150, unique=True)  # + espaço p/ nomes longos
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
    cadastrur = models.CharField(max_length=80, blank=True, null=True)  # ↑ de 50 -> 80

    # descrição / endereço granular
    descricao = models.TextField(blank=True, default='')                 # já é “infinito” na prática
    rua = models.CharField(max_length=255, blank=True, default='')
    bairro = models.CharField(max_length=150, blank=True, default='')    # ↑ de 100 -> 150
    cidade = models.CharField(max_length=150, blank=True, default='')    # ↑ de 100 -> 150
    numero = models.CharField(max_length=20, blank=True, default='')     # ↑ de 10 -> 20 (ex.: “1500 Bloco B”)
    cep = models.CharField(max_length=10, blank=True, default='')        # ↑ de 8 -> 10 (com hífen)
    endereco_full = models.CharField(max_length=300, blank=True, default='')  # ↑ de 255 -> 300

    # localização
    # IMPORTANTE: deixe NULL permitido + default para evitar erro “NOT NULL” quando a importação vier sem lat/lng
    latitude = models.CharField(max_length=50, null=True, blank=True, default='-28.937100')
    longitude = models.CharField(max_length=50, null=True, blank=True, default='-49.484000')

    # contatos
    telefone = models.CharField(max_length=60, blank=True, null=True)    # ↑ de 20 -> 60 (vários números)
    email = models.EmailField(blank=True, null=True)
    contato_direto = models.CharField(max_length=255, blank=True, null=True)

    # presença digital
    # URLField corta em 200 chars por padrão — seus links do Maps podem estourar.
    # Troque para TextField para não limitar, OU aumente max_length do URLField.
    site = models.TextField(blank=True, null=True)        # antes URLField
    digital = models.TextField(blank=True, null=True)     # antes URLField
    maps_url = models.TextField(blank=True, null=True)    # antes URLField
    app_url = models.TextField(blank=True, null=True)     # antes URLField
    facebook = models.TextField(blank=True, null=True)    # antes URLField
    instagram = models.TextField(blank=True, null=True)   # antes URLField

    # imagem
    imagem = models.ImageField(upload_to='empresas/', null=True, blank=True)


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

    def __str__(self):
        return self.nome
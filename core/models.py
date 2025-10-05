# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import F, Avg
from django.core.validators import MinValueValidator, MaxValueValidator

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    favoritos = models.ManyToManyField('Empresa', blank=True, related_name='favoritado_por')

    TEMA_ESCOLHAS = [
        ('light', 'Claro'),
        ('dark', 'Escuro'),
        ('contrast', 'Alto Contraste'),
    ]
    tema_preferido = models.CharField(
        max_length=10,
        choices=TEMA_ESCOLHAS,
        default='light',
        verbose_name="Tema de preferência"
    )
    
    def __str__(self):
        return self.user.username
    
    @property
    def display_name(self):
        full = (self.full_name or self.user.get_full_name() or self.user.first_name or "").strip()
        if full:
            return full.split()[0]
        return (self.user.username or (self.user.email.split("@")[0] if self.user.email else "Você"))
    
class Tag(models.Model):
    nome = models.CharField(max_length=100, unique=True, db_index=True)
    
    # --- NOVO CAMPO DE HIERARQUIA ---
    parent = models.ForeignKey(
        'self',                          # Aponta para o próprio modelo (Tag)
        on_delete=models.CASCADE,        # Se um pai for excluído, os filhos também são
        null=True,                       # Permite que seja uma categoria pai (não tem pai)
        blank=True,                      # Permite que o campo fique vazio no admin/formulários
        related_name='children'          # Como acessar os filhos: ex: tag_pai.children.all()
    )

    class Meta:
        ordering = ['nome']

    def __str__(self):
        # Mostra a hierarquia no admin para fácil identificação
        if self.parent:
            return f"— {self.nome}"
        return self.nome


class Empresa(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='empresas', db_index=True)
    nome = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, help_text="Usado na URL da empresa. Deixe em branco para gerar automaticamente.")
    tags = models.ManyToManyField(Tag, blank=True, related_name='empresas')
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True, db_index=True)
    cadastrur = models.CharField(max_length=80, blank=True, null=True)
    descricao = models.TextField(blank=True, default='')
    rua = models.CharField(max_length=255, blank=True, default='')
    bairro = models.CharField(max_length=150, blank=True, default='')
    cidade = models.CharField(max_length=150, blank=True, default='')
    numero = models.CharField(max_length=20, blank=True, default='')
    cep = models.CharField(max_length=10, blank=True, default='')
    endereco_full = models.CharField(max_length=300, blank=True, default='')

    latitude = models.CharField(max_length=50, null=True, blank=True, default='-28.937100')
    longitude = models.CharField(max_length=50, null=True, blank=True, default='-49.484000')

    telefone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    contato_direto = models.CharField(max_length=255, blank=True, null=True)

    site = models.URLField(blank=True, null=True)
    digital = models.TextField(blank=True, null=True)
    maps_url = models.TextField(blank=True, null=True)
    app_url = models.TextField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)

    sem_telefone = models.BooleanField(default=False)
    sem_email = models.BooleanField(default=False)

    horario_semana = models.CharField(
        max_length=100, blank=True, null=True, 
        help_text="Ex: 09:00 - 18:00"
    )
    horario_sabado = models.CharField(
        max_length=100, blank=True, null=True, 
        help_text="Ex: 09:00 - 12:00 ou Fechado"
    )
    horario_domingo = models.CharField(
        max_length=100, blank=True, null=True, 
        help_text="Ex: Fechado"
    )
    horario_observacoes = models.TextField(
        blank=True, null=True, 
        help_text="Informações adicionais, como 'Fechado para almoço das 12h às 13h'."
    )

    data_cadastro = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['cidade', 'bairro']),
            models.Index(fields=['cnpj']),
        ]

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)

        original_slug = self.slug
        counter = 1
        queryset = Empresa.objects.filter(slug=self.slug)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)

        while Empresa.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f'{original_slug}-{counter}'
            counter += 1
            queryset = Empresa.objects.filter(slug=self.slug)
            
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
        super().save(*args, **kwargs)

    @property
    def imagem_principal(self):
        img = self.imagens.filter(principal=True).first()
        if img:
            return img
        return self.imagens.order_by('data_upload').first()
    
    @property
    def nota_media(self):
        media = self.avaliacoes.aggregate(Avg('nota')).get('nota__avg') or 0.0
        return round(media, 1)

    @property
    def total_avaliacoes(self):
        return self.avaliacoes.count()
    

class ImagemEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='empresas/galeria/')
    principal = models.BooleanField(default=False, help_text="Marque se esta é a imagem principal/capa da empresa.")
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [F('principal').desc(), '-data_upload'] # Principal sempre primeiro

    def __str__(self):
        return f"Imagem para {self.empresa.nome}"
    
class Avaliacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='avaliacoes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Nota de 1 a 5"
    )
    comentario = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['empresa', 'user']
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Avaliação de {self.user.username} para {self.empresa.nome}: {self.nota} estrelas'
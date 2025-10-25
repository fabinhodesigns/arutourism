from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import F, Avg
from django.core.validators import MinValueValidator, MaxValueValidator

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf_cnpj = models.CharField(max_length=14, unique=True, db_index=True) 
    full_name = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    favoritos = models.ManyToManyField(
        'Empresa', 
        blank=True, 
        related_name='favoritado_por',
        verbose_name="Empresas Favoritas"
    )

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
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Detalhes dos Usuários"
    
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
    parent = models.ForeignKey(
        'self',                          
        on_delete=models.CASCADE,        
        null=True,                       
        blank=True,                      
        related_name='children',
        verbose_name="Categoria Pai"
    )

    class Meta:
        ordering = ['nome']
        verbose_name = "Categoria / Tag"
        verbose_name_plural = "Categorias / Tags"

    def __str__(self):
        if self.parent:
            return f"— {self.nome}"
        return self.nome


class Empresa(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='empresas', db_index=True)
    nome = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, help_text="Usado na URL da empresa. Deixe em branco para gerar automaticamente.")
    tags = models.ManyToManyField(Tag, blank=True, related_name='empresas', verbose_name="Tags")
    cnpj = models.CharField(max_length=18, blank=True, null=True, db_index=True) 
    cadastrur = models.CharField(max_length=80, blank=True, null=True)
    descricao = models.TextField(blank=True, default='')
    rua = models.CharField(max_length=255, blank=True, default='')
    bairro = models.CharField(max_length=150, blank=True, default='')
    cidade = models.CharField(max_length=150, blank=True, default='')
    numero = models.CharField(max_length=20, blank=True, default='')
    cep = models.CharField(max_length=10, blank=True, default='')
    endereco_full = models.CharField(max_length=300, blank=True, default='')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True) 
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    telefone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    contato_direto = models.CharField(max_length=255, blank=True, null=True)
    site = models.URLField(max_length=500, blank=True, null=True) 
    facebook = models.URLField(max_length=500, blank=True, null=True)
    instagram = models.URLField(max_length=500, blank=True, null=True)
    sem_telefone = models.BooleanField(default=False)
    sem_email = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [ models.Index(fields=['cidade', 'bairro']), ]
        verbose_name = "Ponto Turístico"
        verbose_name_plural = "Pontos Turísticos"

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
        
        while queryset.exists():
            self.slug = f'{original_slug}-{counter}'
            counter += 1
            queryset = Empresa.objects.filter(slug=self.slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
        super().save(*args, **kwargs)

    @property
    def imagem_principal(self):
        if hasattr(self, 'imagem_principal_list') and self.imagem_principal_list:
            return self.imagem_principal_list[0]
        img = self.imagens.filter(principal=True).first()
        if img:
            return img
        return self.imagens.order_by('data_upload').first()
    
class ImagemEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='empresas/galeria/')
    principal = models.BooleanField(default=False, help_text="Marque se esta é a imagem principal/capa da empresa.")
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [F('principal').desc(), '-data_upload'] 
        verbose_name = "Imagem da Empresa"
        verbose_name_plural = "Imagens dos Pontos Turísticos / Empresas"

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
        ordering = ('-data_criacao',)
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"

    def __str__(self):
        return f'Avaliação de {self.user.username} para {self.empresa.nome}: {self.nota} estrelas'
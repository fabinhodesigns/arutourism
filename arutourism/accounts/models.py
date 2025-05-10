from django.db import models

class Empresa(models.Model):
    CATEGORIAS = [
        ('restaurante', 'Restaurante'),
        ('hotel', 'Hotel'),
        ('ponto_turistico', 'Ponto Turístico'),
        # Adicione outras categorias conforme necessário
    ]

    nome = models.CharField(max_length=255)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    descricao = models.TextField()
    endereco = models.CharField(max_length=255)
    telefone = models.CharField(max_length=15)
    email = models.EmailField()
    site = models.URLField(blank=True, null=True)
    imagem = models.ImageField(upload_to='empresa_imagens/', blank=True, null=True)  # Campo de imagem no singular

    def __str__(self):
        return self.nome

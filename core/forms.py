# core/forms.py
from __future__ import annotations
import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import PerfilUsuario
from .utils.cpf import is_valid_cpf, only_digits
from .models import Categoria, PerfilUsuario, Empresa

# ---------------------------------------------------------
# Helpers de normalização/limites (evitam erros no banco)
# ---------------------------------------------------------
def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")

def _clip_model(model_cls, field_name: str, value):
    """Trunca strings conforme max_length do field (se houver)."""
    if value is None:
        return value
    try:
        f = model_cls._meta.get_field(field_name)
        maxlen = getattr(f, "max_length", None)
    except Exception:
        maxlen = None
    if maxlen and isinstance(value, str):
        return value[:maxlen]
    return value

def _only_digits(s: str) -> str:
    import re
    return re.sub(r"\D", "", s or "")

def _cpf_is_valid(cpf_digits: str) -> bool:
    # Valida CPF (11 dígitos) com dígitos verificadores
    d = _only_digits(cpf_digits)
    if len(d) != 11 or d == d[0] * 11:
        return False
    def dv(nums):
        s = sum(int(n) * w for n, w in zip(nums, range(len(nums)+1, 1, -1)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    return dv(d[:9]) == int(d[9]) and dv(d[:10]) == int(d[10])


# =========================================================
# Usuários
# =========================================================
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    cpf_cnpj = forms.CharField(max_length=18)
    full_name = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Digite seu usuário',
            'email': 'Digite seu email',
            'password': '*********',
            'cpf_cnpj': 'Digite o CPF ou CNPJ',
            'full_name': 'Digite seu nome completo',
        }
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            classes = f'{existing_classes} form-control form-control-sm'.strip()
            field.widget.attrs['class'] = classes
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso.')
        return email

    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if PerfilUsuario.objects.filter(cpf_cnpj=cpf_cnpj).exists():
            raise ValidationError('Este CPF/CNPJ já está em uso.')
        return cpf_cnpj

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise ValidationError('As senhas não correspondem.')
        return cleaned

def save(self, commit=True):
    user = super().save(commit=False)
    user.set_password(self.cleaned_data['password'])
    user.email = (user.email or '').lower()

    if commit:
        user.save()
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        perfil.cpf_cnpj = re.sub(r"\D", "", self.cleaned_data['cpf_cnpj'])
        perfil.full_name = self.cleaned_data.get('full_name') or perfil.full_name or user.username
        perfil.save()

    return user
    

class ProfileForm(forms.ModelForm):
    # edita também campos do User
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=False, label="Nome de Exibição")
    telefone = forms.CharField(required=False, label="Telefone")

    class Meta:
        model = PerfilUsuario
        fields = ['full_name', 'telefone', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Seu nome completo'}),
        }
        labels = {
            'full_name': 'Nome completo',
            'avatar': 'Foto/Avatar'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        # placeholders/estilo
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.ClearableFileInput,)):
                field.widget.attrs.setdefault('class', 'form-control')
        self.fields['avatar'].widget.attrs.setdefault('class', 'form-control')

        # inicializa com dados do User
        self.fields['email'].initial = self.user.email
        self.fields['first_name'].initial = self.user.first_name
        self.fields['telefone'].initial = self.instance.telefone

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').lower()
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

    def save(self, commit=True):
        perfil = super().save(commit=False)
        # grava User
        self.user.email = self.cleaned_data['email'].lower()
        self.user.first_name = self.cleaned_data.get('first_name', '')
        if commit:
            self.user.save()
        # telefone vem do form (campo “espelhado”)
        perfil.telefone = self.cleaned_data.get('telefone') or perfil.telefone
        if commit:
            perfil.save()
        return perfil


class StartResetByCpfForm(forms.Form):
    cpf_cnpj = forms.CharField(label="CPF/CNPJ", max_length=18)

    def clean_cpf_cnpj(self):
        return (self.cleaned_data.get('cpf_cnpj') or '').strip()

class CustomLoginForm(forms.Form):
    identificador = forms.CharField(label="Usuário ou CPF", max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identificador'].widget.attrs.update({
            'placeholder': 'Digite seu CPF ou Email',
            'class': 'form-control'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Digite sua senha',
            'class': 'form-control'
        })

    def clean(self):
        identificador = (self.cleaned_data.get('identificador') or '').lower()
        password = self.cleaned_data.get('password')

        user = None
        if User.objects.filter(username=identificador).exists():
            user = authenticate(username=identificador, password=password)
        elif User.objects.filter(email=identificador).exists():
            user = authenticate(username=User.objects.get(email=identificador).username, password=password)
        elif PerfilUsuario.objects.filter(cpf_cnpj=identificador).exists():
            user_cpf = PerfilUsuario.objects.get(cpf_cnpj=identificador).user
            user = authenticate(username=user_cpf.username, password=password)

        if user is None:
            raise forms.ValidationError("Usuário ou senha inválidos.")
        self.user = user
        return self.cleaned_data


# =========================================================
# Empresas — Form público (cadastro rápido) 
#  - usado nas suas telas atuais de cadastrar/editar
# =========================================================
class EmpresaForm(forms.ModelForm):
    sem_telefone = forms.BooleanField(required=False, label="Sem Telefone")
    sem_email = forms.BooleanField(required=False, label="Sem Email")

    class Meta:
        model = Empresa
        fields = [
            'nome', 'categoria', 'descricao',
            'rua', 'bairro', 'cidade', 'numero', 'cep',
            'telefone', 'email', 'site', 'imagem',
            'latitude', 'longitude',
            'facebook', 'instagram',
            'sem_telefone', 'sem_email',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Digite o nome da empresa'}),
            'categoria': forms.Select(),
            'descricao': forms.Textarea(attrs={'placeholder': 'Digite a descrição da empresa', 'rows': 4}),
            'rua': forms.TextInput(attrs={'placeholder': 'Digite a rua'}),
            'bairro': forms.TextInput(attrs={'placeholder': 'Digite o bairro'}),
            'cidade': forms.TextInput(attrs={'placeholder': 'Digite a cidade'}),
            'numero': forms.TextInput(attrs={'placeholder': 'Digite o número'}),
            'cep': forms.TextInput(attrs={'placeholder': 'Apenas números'}),
            'telefone': forms.TextInput(attrs={'placeholder': 'Ex: 48912345678'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contato@empresa.com'}),
            'site': forms.URLInput(attrs={'placeholder': 'https://suaempresa.com'}),
            'imagem': forms.ClearableFileInput(),
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com/suaempresa'}),
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com/suaempresa'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        labels = {
            'nome': 'Nome da Empresa',
            'categoria': 'Categoria',
            'descricao': 'Descrição',
            'rua': 'Rua',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'numero': 'Número',
            'cep': 'CEP',
            'telefone': 'Telefone',
            'email': 'Email de Contato',
            'site': 'Site (opcional)',
            'imagem': 'Imagem da Empresa',
            'facebook': 'Facebook (opcional)',
            'instagram': 'Instagram (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ordena categorias alfabeticamente e mostra opção vazia
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        self.fields['categoria'].empty_label = "Selecione uma categoria"

        # classes padrão (mantendo compat com seu template)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-lg'})
            elif not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput, forms.ClearableFileInput)):
                field.widget.attrs.update({'class': 'form-control form-control-lg'})

        # se não vier lat/lng no GET/Instance, aplica default do model (evita NOT NULL)
        if not self.initial.get('latitude'):
            self.initial['latitude'] = Empresa._meta.get_field('latitude').default
        if not self.initial.get('longitude'):
            self.initial['longitude'] = Empresa._meta.get_field('longitude').default

    # ------------ Validações pontuais ------------
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero and not numero.isdigit():
            raise ValidationError("O número deve conter apenas dígitos.")
        # garante que cabe no banco
        return _clip_model(Empresa, 'numero', numero)

    def clean_cep(self):
        cep = _digits(self.cleaned_data.get('cep'))
        return _clip_model(Empresa, 'cep', cep)

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            tel = _digits(telefone)
            # aceita 10 ou 11 (com DDD)
            if len(tel) not in (10, 11):
                raise ValidationError("O telefone deve ter 10 ou 11 dígitos (com DDD).")
            return _clip_model(Empresa, 'telefone', tel)
        return telefone

    def clean_facebook(self):
        url = self.cleaned_data.get('facebook')
        if url and 'facebook.com' not in url.lower():
            raise ValidationError("Por favor, insira um link válido do Facebook.")
        return _clip_model(Empresa, 'facebook', url)

    def clean_instagram(self):
        url = self.cleaned_data.get('instagram')
        if url and 'instagram.com' not in url.lower():
            raise ValidationError("Por favor, insira um link válido do Instagram.")
        return _clip_model(Empresa, 'instagram', url)

    def clean_site(self):
        url = self.cleaned_data.get('site')
        # sem exigir http/https — quem valida é o URLField; só corta
        return _clip_model(Empresa, 'site', url)

    def clean(self):
        cleaned = super().clean()

        # defaults de latitude/longitude se vierem vazios
        if not cleaned.get('latitude'):
            cleaned['latitude'] = Empresa._meta.get_field('latitude').default
        if not cleaned.get('longitude'):
            cleaned['longitude'] = Empresa._meta.get_field('longitude').default

        sem_telefone = cleaned.get('sem_telefone')
        sem_email = cleaned.get('sem_email')
        telefone = cleaned.get('telefone')
        email = cleaned.get('email')

        # Regras suaves: exige telefone/email somente se a flag correspondente NÃO estiver marcada
        if not sem_telefone and not telefone:
            self.add_error('telefone', 'Este campo é obrigatório ou marque "Sem Telefone".')

        if not sem_email and not email:
            self.add_error('email', 'Este campo é obrigatório ou marque "Sem Email".')

        # se marcar “sem_*”, garante que salvaremos vazio
        if sem_telefone:
            cleaned['telefone'] = ''
        if sem_email:
            cleaned['email'] = ''

        # clipping extra para garantir limites do banco
        for field in ['nome', 'rua', 'bairro', 'cidade', 'descricao', 'facebook', 'instagram']:
            cleaned[field] = _clip_model(Empresa, field, cleaned.get(field))

        return cleaned


# =========================================================
# Empresas — Form COMPLETO (edição avançada com todos campos)
#   Use este form na página de edição “completa”
# =========================================================
class EmpresaFullForm(forms.ModelForm):
    sem_telefone = forms.BooleanField(required=False, label="Sem Telefone")
    sem_email = forms.BooleanField(required=False, label="Sem Email")

    class Meta:
        model = Empresa
        fields = [
            # essenciais
            'nome', 'categoria', 'descricao',
            # identificação
            'cnpj', 'cadastrur',
            # endereço granular + completo
            'rua', 'bairro', 'cidade', 'numero', 'cep', 'endereco_full',
            # localização
            'latitude', 'longitude',
            # contatos
            'telefone', 'email', 'contato_direto',
            # presença digital (TODOS)
            'site', 'digital', 'maps_url', 'app_url', 'facebook', 'instagram',
            # imagem
            'imagem',
            # flags
            'sem_telefone', 'sem_email',
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva o estabelecimento'}),
            'endereco_full': forms.TextInput(attrs={'placeholder': 'Se preferir, informe o endereço completo'}),
            'cnpj': forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
            'cadastrur': forms.TextInput(attrs={'placeholder': 'Código Cadastur (se houver)'}),
            'contato_direto': forms.TextInput(attrs={'placeholder': 'Nome/WhatsApp da pessoa de contato'}),
            'digital': forms.URLInput(attrs={'placeholder': 'Site ou link agregado (aceita 1º link do texto)'}),
            'maps_url': forms.URLInput(attrs={'placeholder': 'URL do Google Maps'}),
            'app_url': forms.URLInput(attrs={'placeholder': 'URL do App'}),
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com/suaempresa'}),
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com/suaempresa'}),
            'imagem': forms.ClearableFileInput(),
            'latitude': forms.TextInput(attrs={'placeholder': 'Latitude', 'inputmode': 'decimal'}),
            'longitude': forms.TextInput(attrs={'placeholder': 'Longitude', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        self.fields['categoria'].empty_label = "Selecione uma categoria"

        # aplica classes padrão
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-lg'})
            elif not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput, forms.ClearableFileInput)):
                field.widget.attrs.update({'class': 'form-control form-control-lg'})

        # defaults lat/lng
        if not self.initial.get('latitude'):
            self.initial['latitude'] = Empresa._meta.get_field('latitude').default
        if not self.initial.get('longitude'):
            self.initial['longitude'] = Empresa._meta.get_field('longitude').default

    # --- saneamentos básicos (espelham o form simples) ---
    def clean_cep(self):
        return _clip_model(Empresa, 'cep', _digits(self.cleaned_data.get('cep')))

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            tel = _digits(telefone)
            if len(tel) not in (10, 11):
                raise ValidationError("O telefone deve ter 10 ou 11 dígitos (com DDD).")
            return _clip_model(Empresa, 'telefone', tel)
        return telefone

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero and not numero.isdigit():
            raise ValidationError("O número deve conter apenas dígitos.")
        return _clip_model(Empresa, 'numero', numero)

    def clean(self):
        cleaned = super().clean()

        # defaults lat/lng
        if not cleaned.get('latitude'):
            cleaned['latitude'] = Empresa._meta.get_field('latitude').default
        if not cleaned.get('longitude'):
            cleaned['longitude'] = Empresa._meta.get_field('longitude').default

        sem_telefone = cleaned.get('sem_telefone')
        sem_email = cleaned.get('sem_email')
        telefone = cleaned.get('telefone')
        email = cleaned.get('email')

        if not sem_telefone and not telefone:
            self.add_error('telefone', 'Este campo é obrigatório ou marque "Sem Telefone".')
        if not sem_email and not email:
            self.add_error('email', 'Este campo é obrigatório ou marque "Sem Email".')

        if sem_telefone:
            cleaned['telefone'] = ''
        if sem_email:
            cleaned['email'] = ''

        # clipping extra
        for field in [
            'nome', 'rua', 'bairro', 'cidade', 'endereco_full', 'descricao',
            'contato_direto', 'cnpj', 'cadastrur', 'site', 'digital', 'maps_url',
            'app_url', 'facebook', 'instagram'
        ]:
            cleaned[field] = _clip_model(Empresa, field, cleaned.get(field))

        return cleaned
    
class CpfUpdateForm(forms.Form):
    cpf_cnpj = forms.CharField(
        label="CPF",
        max_length=14,  # com máscara
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.000.000-00",
            "inputmode": "numeric",
            "autocomplete": "off",
            "aria-describedby": "cpfHelp",
        }),
    )
    password = forms.CharField(
        label="Senha atual",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Digite sua senha atual",
            "autocomplete": "current-password",
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_cpf_cnpj(self):
        raw = self.cleaned_data.get("cpf_cnpj", "")
        digits = _only_digits(raw)
        if len(digits) != 11 or not _cpf_is_valid(digits):
            raise forms.ValidationError("CPF inválido.")
        # unicidade amigável (além da constraint do banco)
        qs = PerfilUsuario.objects.filter(cpf_cnpj=digits).exclude(user=self.user)
        if qs.exists():
            raise forms.ValidationError("Este CPF já está em uso por outra conta.")
        return digits

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        if not pwd or not self.user.check_password(pwd):
            # mensagem neutra para não vazar se a conta existe
            raise forms.ValidationError("Não foi possível validar sua senha.")
        return cleaned

from __future__ import annotations
import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from .utils.cpf import is_valid_cpf, only_digits
from .models import Tag, PerfilUsuario, Empresa
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from .models import Avaliacao
from django.utils.html import format_html
from django.urls import reverse

User = get_user_model()

def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")

def _clip_model(model_cls, field_name: str, value):
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

def clean_digits(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)

def is_valid_cpf(cpf: str) -> bool:
    cpf = clean_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    def calc_digit(digits: str) -> int:
        s = sum(int(d) * w for d, w in zip(digits, range(len(digits) + 1, 1, -1)))
        res = (s * 10) % 11
        return 0 if res == 10 else res

    return calc_digit(cpf[:9]) == int(cpf[9]) and calc_digit(cpf[:10]) == int(cpf[10])

def is_valid_cnpj(cnpj: str) -> bool:
    cnpj = clean_digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc_digit(digits: str, weights: list[int]) -> int:
        s = sum(int(d) * w for d, w in zip(digits, weights))
        res = s % 11
        return 0 if res < 2 else 11 - res

    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    return (calc_digit(cnpj[:12], weights1) == int(cnpj[12]) and
            calc_digit(cnpj[:13], weights2) == int(cnpj[13]))

_only_digits = lambda s: re.sub(r"\D", "", s or "")

def cpf_valido(cpf: str) -> bool:
    cpf = _only_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    def calc_digitos(cpf_parcial: str) -> str:
        for t in [9, 10]:
            soma = sum(int(cpf_parcial[i]) * (t + 1 - i) for i in range(t))
            d = (soma * 10) % 11
            cpf_parcial += "0" if d == 10 else str(d)
        return cpf_parcial[-2:]
    return cpf[-2:] == calc_digitos(cpf[:9])

def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def _cpf_is_valid(cpf_digits: str) -> bool:
    
    d = _only_digits(cpf_digits)
    if len(d) != 11 or d == d[0] * 11:
        return False
    def dv(nums):
        s = sum(int(n) * w for n, w in zip(nums, range(len(nums)+1, 1, -1)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    return dv(d[:9]) == int(d[9]) and dv(d[:10]) == int(d[10])

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(label="Nome Completo", max_length=150, required=True)
    email = forms.EmailField(label="Email", required=True)
    cpf_cnpj = forms.CharField(label="CPF ou CNPJ", max_length=18, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('full_name', 'username', 'email', 'cpf_cnpj', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        placeholders = {
            'full_name': 'Digite seu nome completo',
            'username': 'Digite seu usuário',
            'email': 'Digite seu email',
            'cpf_cnpj': 'Digite o CPF ou CNPJ',
            'password1': 'Crie sua senha',      
            'password2': 'Confirme sua senha',   
        }
        
        self.fields['username'].label = 'Usuário'
        self.fields['password1'].label = 'Senha' 
        self.fields['password2'].label = 'Confirmar Senha'

        for field_name, field in self.fields.items():
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso.')
        return email

    def clean_cpf_cnpj(self):
        cpf_cnpj_raw = self.cleaned_data.get('cpf_cnpj', '')
        digits = clean_digits(cpf_cnpj_raw) 
        
        if len(digits) == 11:
            if not is_valid_cpf(digits):
                raise ValidationError('O CPF informado não é válido.')
        elif len(digits) == 14:
            if not is_valid_cnpj(digits):
                raise ValidationError('O CNPJ informado não é válido.')
        else:
            raise ValidationError('O documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos.')
            
        if PerfilUsuario.objects.filter(cpf_cnpj=digits).exists():
            raise ValidationError('Este CPF/CNPJ já está em uso.')
            
        return digits

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').lower()
        
        full_name = self.cleaned_data.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        else:
            user.last_name = '' 

        if commit:
            user.save()
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
            perfil.full_name = full_name
            perfil.save()

        return user    

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=False, label="Nome de exibição (apelido)")

    class Meta:
        model = PerfilUsuario
        fields = ['full_name', 'telefone', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Seu nome completo'}),
            'telefone': forms.TextInput(attrs={'placeholder': 'Seu número com DDD'}),
        }
        labels = {
            'full_name': 'Nome completo',
            'telefone': 'Telefone',
            'avatar': 'Foto/Avatar'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['first_name'].initial = self.user.first_name
        self.fields['email'].initial = self.user.email

        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs.setdefault('class', 'form-control')

        self.fields['email'].error_messages['unique'] = format_html(
            'Este e-mail já está em uso. <a href="{}">Esqueceu sua senha?</a>',
            reverse('esqueci_senha_email')
        )
        
    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').lower()
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Este e-mail já está em uso por outra conta.')
        return email

    def save(self, commit=True):
        perfil = super().save(commit=False)

        self.user.email = self.cleaned_data['email'].lower()
        self.user.first_name = self.cleaned_data.get('first_name', '')
        
        if commit:
            self.user.save()
            perfil.save()
            
        return perfil


class StartResetByCpfForm(forms.Form):
    cpf_cnpj = forms.CharField(label="CPF/CNPJ", max_length=18)

    def clean_cpf_cnpj(self):
        raw = (self.cleaned_data.get('cpf_cnpj') or '').strip()
        digits = _only_digits(raw)  
        if not digits:
            raise forms.ValidationError("Informe o CPF ou CNPJ.")
        if len(digits) not in (11, 14):
            raise forms.ValidationError("Digite um CPF (11) ou CNPJ (14) válido.")
        if PerfilUsuario.objects.filter(cpf_cnpj=digits).exists():
            raise forms.ValidationError(
                format_html(
                    'Este CPF/CNPJ já está cadastrado. <a href="{}">Precisa recuperar o acesso?</a>', 
                    reverse('esqueci_senha_cpf')
                ),
                code='unique'
            )
        return digits
    
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['nome']
        widgets = {'nome': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nome da nova tag'})}

class CustomLoginForm(forms.Form):
    identificador = forms.CharField(label="E-mail, CPF ou usuário", max_length=150)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identificador'].widget.attrs.update(
            {'placeholder': 'Digite seu e-mail, CPF ou usuário'}
        )
        self.fields['password'].widget.attrs.update(
            {'placeholder': 'Digite sua senha'}
        )
    
    def clean(self):
        cleaned_data = super().clean()
        ident = cleaned_data.get("identificador", "").strip()
        pwd = cleaned_data.get("password")

        if not ident or not pwd:
            raise ValidationError("Preencha todos os campos.")

        user = None
        
        if "@" in ident:
            user = User.objects.filter(email__iexact=ident).first()
        elif ident.isdigit():
            perfil = PerfilUsuario.objects.select_related("user").filter(cpf_cnpj=ident).first()
            if perfil:
                user = perfil.user
        else:
            user = User.objects.filter(username__iexact=ident).first()

        if not user:
            self.add_error('identificador', "Nenhuma conta encontrada com este identificador.")
            # ✨ CORREÇÃO: Adicionado 'return' para parar a execução aqui e evitar o crash.
            return

        # A partir daqui, o código só executa se 'user' for encontrado.
        if not user.is_active:
            raise ValidationError("Esta conta está inativa. Entre em contato com o suporte.")

        authenticated_user = authenticate(username=user.username, password=pwd)
        if not authenticated_user:
            self.add_error('password', "A senha está incorreta. Tente novamente.")
            return

        self.user = authenticated_user
        return cleaned_data
            
class EmpresaForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all().order_by('nome'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Categorias e Tags"
    )

    imagem_inicial = forms.ImageField(
        label="Imagem Principal da Empresa",
        required=False,
    )
    
    novas_imagens = forms.ImageField(
        label="Adicionar novas imagens à galeria (limite de 5 no total)",
        required=False
    )

    class Meta:
        model = Empresa
        fields = [
            'nome', 'tags', 'descricao', 'rua', 'bairro', 'cidade', 'numero', 'cep',
            'latitude', 'longitude', 'telefone', 'email', 'contato_direto', 'site',
            'facebook', 'instagram', 'horario_semana', 'horario_sabado', 'horario_domingo',
            'horario_observacoes', 'cnpj', 'cadastrur', 'app_url', 'sem_telefone', 'sem_email',
            'imagem_inicial'
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
            'latitude': forms.TextInput(attrs={'placeholder': 'Latitude', 'inputmode': 'decimal'}),
            'longitude': forms.TextInput(attrs={'placeholder': 'Longitude', 'inputmode': 'decimal'}),
            'horario_semana': forms.TextInput(attrs={'placeholder': 'Ex: 08:00 - 18:00'}),
            'horario_sabado': forms.TextInput(attrs={'placeholder': 'Ex: 08:00 - 12:00 ou Fechado'}),
            'horario_domingo': forms.TextInput(attrs={'placeholder': 'Ex: Fechado'}),
            'horario_observacoes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Fechamos para almoço das 12h às 13h30.'}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if instance and instance.pk: 
            self.fields.pop('imagem_inicial', None)
        else: 
            self.fields.pop('novas_imagens', None)
            self.fields['imagem_inicial'].required = True
        
        for name, field in self.fields.items():
            if name == 'tags': continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-lg'})
            elif not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput, forms.FileInput, forms.ClearableFileInput)):
                field.widget.attrs.update({'class': 'form-control form-control-lg'})

    def clean_novas_imagens(self):
        novas_imagens = self.files.getlist('novas_imagens')
        if self.instance and self.instance.pk:
            imagens_atuais_count = self.instance.imagens.count()
            if (imagens_atuais_count + len(novas_imagens)) > 5:
                raise ValidationError(f"Você só pode ter no máximo 5 imagens. Você já tem {imagens_atuais_count} e está tentando adicionar mais {len(novas_imagens)}.")
        return novas_imagens
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            cleaned_cnpj = ''.join(filter(str.isdigit, cnpj))
            
            query = Empresa.objects.filter(cnpj=cleaned_cnpj).exclude(pk=self.instance.pk)
            
            if query.exists():
                raise forms.ValidationError("Já existe uma empresa cadastrada com este CNPJ.")
        return cnpj
    
    # Suas outras funções de validação (clean_*, etc.) permanecem aqui...
    def clean_cep(self):
        return _clip_model(Empresa, 'cep', _digits(self.cleaned_data.get('cep')))
    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone and not self.cleaned_data.get('sem_telefone'):
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
        sem_telefone = cleaned.get('sem_telefone')
        sem_email = cleaned.get('sem_email')
        telefone = cleaned.get('telefone')
        email = cleaned.get('email')
        if not sem_telefone and not telefone:
            self.add_error('telefone', 'Este campo é obrigatório ou marque "Sem Telefone".')
        if not sem_email and not email:
            self.add_error('email', 'Este campo é obrigatório ou marque "Sem Email".')
        if sem_telefone: cleaned['telefone'] = ''
        if sem_email: cleaned['email'] = ''
        return cleaned
    
class CpfUpdateForm(forms.Form):
    cpf_cnpj = forms.CharField(
        label="CPF", max_length=14,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "000.000.000-00", "inputmode": "numeric", "autocomplete": "off", "aria-describedby": "cpfHelp"})
    )
    password = forms.CharField(
        label="Senha atual",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Digite sua senha atual", "autocomplete": "current-password"})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_cpf_cnpj(self):
        raw = self.cleaned_data.get("cpf_cnpj", "")
        digits = _only_digits(raw)
        if len(digits) != 11 or not _cpf_is_valid(digits):
            raise forms.ValidationError("CPF inválido.")
        qs = PerfilUsuario.objects.filter(cpf_cnpj=digits).exclude(user=self.user)
        if qs.exists():
            raise forms.ValidationError("Este CPF já está em uso por outra conta.")
        return digits

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        if not pwd or not self.user.check_password(pwd):
            raise forms.ValidationError("Não foi possível validar sua senha.")
        return cleaned
    
class AvaliacaoForm(forms.ModelForm):
    nota = forms.ChoiceField(
        choices=[(i, f'{i} Estrela' + ('s' if i > 1 else '')) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'star-rating'}),
        label="Sua nota"
    )

    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Conte como foi sua experiência (opcional)...'
            })
        }
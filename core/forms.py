# core/forms.py
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

User = get_user_model()

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
class UserRegistrationForm(UserCreationForm):
    # Campos customizados que NÃO vêm do UserCreationForm
    full_name = forms.CharField(label="Nome Completo", max_length=255)
    email = forms.EmailField(label="Email", required=True)
    cpf_cnpj = forms.CharField(label="CPF ou CNPJ", max_length=18)
    
    # <--- REMOVA as declarações de 'password' e 'confirm_password' daqui

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dicionário de placeholders com os NOMES CORRETOS
        placeholders = {
            'full_name': 'Digite seu nome completo',
            'username': 'Digite seu usuário',
            'email': 'Digite seu email',
            'cpf_cnpj': 'Digite o CPF ou CNPJ',
            'password1': 'Crie sua senha',      # <--- AJUSTE AQUI
            'password2': 'Confirme sua senha',   # <--- AJUSTE AQUI
        }
        
        # Define os rótulos amigáveis para os campos
        self.fields['username'].label = 'Usuário'
        self.fields['password1'].label = 'Senha' # <--- AJUSTE AQUI
        self.fields['password2'].label = 'Confirmar Senha'

        # Loop para adicionar classes e placeholders
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso.')
        return email

    def clean_cpf_cnpj(self):
        cpf_cnpj_raw = self.cleaned_data.get('cpf_cnpj', '')
        digits_cpf = re.sub(r"\D", "", cpf_cnpj_raw)
        
        if PerfilUsuario.objects.filter(cpf_cnpj=digits_cpf).exists():
            raise ValidationError('Este CPF/CNPJ já está em uso.')
            
        return digits_cpf

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').lower()
        user.first_name = (self.cleaned_data.get('full_name') or '').split(' ')[0]
        
        if commit:
            user.save()
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.cpf_cnpj = self.cleaned_data['cpf_cnpj']
            perfil.full_name = self.cleaned_data.get('full_name')
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
        raw = (self.cleaned_data.get('cpf_cnpj') or '').strip()
        digits = _only_digits(raw)  # <= só dígitos
        if not digits:
            raise forms.ValidationError("Informe o CPF ou CNPJ.")
        if len(digits) not in (11, 14):
            raise forms.ValidationError("Digite um CPF (11) ou CNPJ (14) válido.")
        return digits

class CustomLoginForm(forms.Form):
    identificador = forms.CharField(label="E-mail, CPF ou usuário", max_length=150)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        ident = (cleaned.get("identificador") or "").strip()
        pwd = cleaned.get("password") or ""

        if not ident or not pwd:
            raise forms.ValidationError(_("Informe e-mail/CPF/usuário e a senha."), code="missing")

        user = None

        # 1) Busca por e-mail
        if "@" in ident:
            try:
                EmailValidator()(ident)
            except forms.ValidationError:
                raise forms.ValidationError(_("E-mail inválido."), code="invalid_email")
            
            user = User.objects.filter(email__iexact=ident).first()
            if not user:
                raise forms.ValidationError(_("Usuário não encontrado para este e-mail."), code="user_not_found")

        # 2) Busca por CPF
        elif _only_digits(ident).isdigit():
            if not cpf_valido(ident):
                raise forms.ValidationError(_("CPF inválido."), code="invalid_cpf")
            
            perfil = PerfilUsuario.objects.select_related("user").filter(cpf_cnpj=_only_digits(ident)).first()
            if not perfil:
                raise forms.ValidationError(_("CPF não vinculado a nenhuma conta."), code="user_not_found")
            user = perfil.user

        # 3) Busca por username
        else:
            user = User.objects.filter(username__iexact=ident).first()
            if not user:
                raise forms.ValidationError(_("Usuário não encontrado."), code="user_not_found")

        # Se encontrou um usuário, verifica se está ativo
        if not user.is_active:
            raise forms.ValidationError(_("Conta inativa. Entre em contato com o suporte."), code="inactive")

        # Tenta autenticar
        authd = authenticate(username=user.username, password=pwd)
        if not authd:
            raise forms.ValidationError(_("Senha incorreta."), code="bad_password")

        # Sucesso! Anexa o usuário ao formulário
        self.user = authd
        return cleaned

# =========================================================
# Empresas — Form público (cadastro rápido) 
#  - usado nas suas telas atuais de cadastrar/editar
# =========================================================
class EmpresaForm(forms.ModelForm):
    # ADICIONADO: Campo para selecionar múltiplas tags.
    # Ele substitui a antiga lógica de dropdown de 'categoria'.
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.order_by('nome'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Categorias / Tags"
    )

    # MANTIDO: Seus campos de flags continuam iguais
    imagem = forms.ImageField(required=False, label="Imagem da Empresa")
    sem_telefone = forms.BooleanField(required=False, label="Sem Telefone")
    sem_email = forms.BooleanField(required=False, label="Sem Email")

    class Meta:
        model = Empresa
        # ALTERADO: Trocamos 'categoria' por 'tags' na lista de campos
        fields = [
            'nome', 'tags', 'descricao',
            'rua', 'bairro', 'cidade', 'numero', 'cep',
            'telefone', 'email',
            'site', 'facebook', 'instagram',
            'imagem',
            'latitude', 'longitude',
            'sem_telefone', 'sem_email',
        ]
        # ALTERADO: O widget e label de 'categoria' foram removidos daqui
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Digite o nome da empresa'}),
            'descricao': forms.Textarea(attrs={'placeholder': 'Descreva a empresa', 'rows': 4}),
            'rua': forms.TextInput(attrs={'placeholder': 'Rua'}),
            'bairro': forms.TextInput(attrs={'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'placeholder': 'Cidade'}),
            'numero': forms.TextInput(attrs={'placeholder': 'Número'}),
            'cep': forms.TextInput(attrs={'placeholder': 'Apenas números'}),
            'telefone': forms.TextInput(attrs={'placeholder': 'Ex: 48912345678'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contato@empresa.com'}),
            'site': forms.URLInput(attrs={'placeholder': 'https://suaempresa.com'}),
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com/suaempresa'}),
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com/suaempresa'}),
            'imagem': forms.ClearableFileInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        labels = {
            'nome': 'Nome da Empresa',
            'descricao': 'Descrição',
            'rua': 'Rua',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'numero': 'Número',
            'cep': 'CEP',
            'telefone': 'Telefone',
            'email': 'E-mail de contato',
            'site': 'Site',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'imagem': 'Imagem',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == 'tags':  # Ignora o campo de checkboxes
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select form-select-lg')
            elif not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput, forms.ClearableFileInput)):
                field.widget.attrs.setdefault('class', 'form-control form-control-lg')

        # MANTIDO: Sua lógica de valores iniciais para latitude/longitude
        if not self.initial.get('latitude'):
            self.initial['latitude'] = Empresa._meta.get_field('latitude').default
        if not self.initial.get('longitude'):
            self.initial['longitude'] = Empresa._meta.get_field('longitude').default

    # MANTIDO: Todas as suas validações customizadas ('clean_...') permanecem intactas
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero and not numero.isdigit():
            raise ValidationError("O número deve conter apenas dígitos.")
        return _clip_model(Empresa, 'numero', numero)

    def clean_cep(self):
        cep = _digits(self.cleaned_data.get('cep'))
        return _clip_model(Empresa, 'cep', cep)

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            tel = _digits(telefone)
            if len(tel) not in (10, 11):
                raise ValidationError("O telefone deve ter 10 ou 11 dígitos (com DDD).")
            return _clip_model(Empresa, 'telefone', tel)
        return telefone

    def clean_site(self):
        return _clip_model(Empresa, 'site', self.cleaned_data.get('site'))

    def clean_facebook(self):
        url = self.cleaned_data.get('facebook')
        if url and 'facebook.com' not in url.lower():
            raise ValidationError("Informe uma URL válida do Facebook.")
        return _clip_model(Empresa, 'facebook', url)

    def clean_instagram(self):
        url = self.cleaned_data.get('instagram')
        if url and 'instagram.com' not in url.lower():
            raise ValidationError("Informe uma URL válida do Instagram.")
        return _clip_model(Empresa, 'instagram', url)

    # MANTIDO: Sua validação global ('clean') permanece intacta
    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('latitude'):
            cleaned['latitude'] = Empresa._meta.get_field('latitude').default
        if not cleaned.get('longitude'):
            cleaned['longitude'] = Empresa._meta.get_field('longitude').default
        telefone = (cleaned.get('telefone') or '').strip()
        email = (cleaned.get('email') or '').strip()
        sem_tel = cleaned.get('sem_telefone')
        sem_mail = cleaned.get('sem_email')
        if not sem_tel and not telefone:
            self.add_error('telefone', 'Obrigatório ou marque "Sem Telefone".')
        if not sem_mail and not email:
            self.add_error('email', 'Obrigatório ou marque "Sem Email".')
        if sem_tel:
            cleaned['telefone'] = ''
        if sem_mail:
            cleaned['email'] = ''
        if not cleaned.get('descricao'):
            cleaned['descricao'] = _clip_model(
                Empresa, 'descricao',
                'Estabelecimento cadastrado no sistema.'
            )
        for field in ['nome', 'rua', 'bairro', 'cidade', 'descricao', 'facebook', 'instagram']:
            cleaned[field] = _clip_model(Empresa, field, cleaned.get(field))
        return cleaned


# =========================================================
# Empresas — Form COMPLETO (edição avançada com todos campos)
#   Use este form na página de edição “completa”
# =========================================================
class EmpresaFullForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.order_by('nome'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Categorias / Tags"
    )
    
    # MANTIDO: Seus campos de flags
    sem_telefone = forms.BooleanField(required=False, label="Sem Telefone")
    sem_email = forms.BooleanField(required=False, label="Sem Email")

    class Meta:
        model = Empresa
        # ALTERADO: Trocamos 'categoria' por 'tags'
        fields = [
            'nome', 'tags', 'descricao',
            'cnpj', 'cadastrur',
            'rua', 'bairro', 'cidade', 'numero', 'cep', 'endereco_full',
            'latitude', 'longitude',
            'telefone', 'email', 'contato_direto',
            'site', 'digital', 'maps_url', 'app_url', 'facebook', 'instagram',
            'imagem',
            'sem_telefone', 'sem_email',
        ]
        # MANTIDO: Seus widgets, a referência a 'categoria' não estava aqui
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

        for name, field in self.fields.items():
            if name == 'tags':
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-lg'})
            elif not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput, forms.ClearableFileInput)):
                field.widget.attrs.update({'class': 'form-control form-control-lg'})

        # MANTIDO: Lógica de valores iniciais
        if not self.initial.get('latitude'):
            self.initial['latitude'] = Empresa._meta.get_field('latitude').default
        if not self.initial.get('longitude'):
            self.initial['longitude'] = Empresa._meta.get_field('longitude').default

    # MANTIDO: Suas validações customizadas
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

    # MANTIDO: Sua validação global
    def clean(self):
        cleaned = super().clean()
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
        max_length=14,
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
        # Você precisa ter a função _only_digits e _cpf_is_valid no topo do seu arquivo
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
    
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': 'Nome da nova tag'
            })
        }
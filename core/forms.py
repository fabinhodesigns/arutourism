from __future__ import annotations
import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
# Removido import duplicado de cpf utils
from .models import Tag, PerfilUsuario, Empresa, Avaliacao, ImagemEmpresa # Adicionado ImagemEmpresa
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from django.utils.html import format_html
from django.urls import reverse

User = get_user_model()

# --- Funções de Validação (Movidas para um local único para evitar duplicação) ---
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

# --- Formulários ---

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(label="Nome Completo", max_length=150, required=True)
    email = forms.EmailField(label="Email", required=True)
    cpf_cnpj = forms.CharField(label="CPF ou CNPJ", max_length=18, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('full_name', 'username', 'email', 'cpf_cnpj') # Removido password1 e password2 daqui

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona os campos de senha explicitamente se necessário (UserCreationForm já faz isso)
        # self.fields['password'] = forms.CharField(label="Senha", widget=forms.PasswordInput)
        # self.fields['password2'] = forms.CharField(label="Confirmar Senha", widget=forms.PasswordInput)
        
        placeholders = {
            'full_name': 'Digite seu nome completo',
            'username': 'Crie um nome de usuário (sem espaços)',
            'email': 'Digite seu email',
            'cpf_cnpj': 'Digite o CPF ou CNPJ (apenas números)',
            'password': 'Crie uma senha segura',      
            'password2': 'Confirme sua senha',   
        }
        
        # Ajustando labels se UserCreationForm não fizer
        self.fields['username'].label = 'Nome de Usuário'
        # self.fields['password'].label = 'Senha' 
        # self.fields['password2'].label = 'Confirmar Senha'

        for field_name, field in self.fields.items():
            # Aplica classes do Bootstrap
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                 field.widget.attrs.setdefault('class', 'form-control form-control-lg')
            
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
            
        return digits # Retorna apenas os dígitos

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
            # Usamos update_or_create para evitar erro se o perfil já existir
            perfil, created = PerfilUsuario.objects.update_or_create(
                user=user,
                defaults={
                    'cpf_cnpj': self.cleaned_data.get('cpf_cnpj'),
                    'full_name': full_name
                }
            )
        return user    

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=False, label="Nome de exibição (apelido)")

    class Meta:
        model = PerfilUsuario
        # Removido 'cpf_cnpj' daqui, pois é editado separadamente
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
            # ✅ CORREÇÃO: Usar o widget correto aqui também ✅
            if not isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs.setdefault('class', 'form-control')
            else: # Para o campo avatar
                 field.widget.attrs.setdefault('class', 'form-control form-control-sm')


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
        digits = clean_digits(raw)  
        if not digits:
            raise forms.ValidationError("Informe o CPF ou CNPJ.")
        if len(digits) not in (11, 14):
            raise forms.ValidationError("Digite um CPF (11) ou CNPJ (14) válido.")
        
        # Corrigido: A validação de existência não deve estar aqui, pois o objetivo é recuperar
        # if PerfilUsuario.objects.filter(cpf_cnpj=digits).exists():
        #     raise forms.ValidationError(...)
            
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
            {'placeholder': 'Digite seu e-mail, CPF ou usuário', 'class': 'form-control form-control-lg'}
        )
        self.fields['password'].widget.attrs.update(
            {'placeholder': 'Digite sua senha', 'class': 'form-control form-control-lg'}
        )

    def clean(self):
        cleaned_data = super().clean()
        ident = cleaned_data.get("identificador", "").strip()
        pwd = cleaned_data.get("password")

        if not ident or not pwd:
            return cleaned_data

        user_obj = None
        
        if "@" in ident:
            user_obj = User.objects.filter(email__iexact=ident).first()
        elif len(clean_digits(ident)) in (11, 14):
            digits = clean_digits(ident)
            perfil = PerfilUsuario.objects.select_related("user").filter(cpf_cnpj=digits).first()
            if perfil:
                user_obj = perfil.user
        else:
            user_obj = User.objects.filter(username__iexact=ident).first()

        if not user_obj:
            raise ValidationError("Nenhuma conta encontrada com este identificador.")

        authenticated_user = authenticate(username=user_obj.username, password=pwd)
        
        if not authenticated_user:
            raise ValidationError("A senha está incorreta. Tente novamente.")
            
        self.user = authenticated_user
        return cleaned_data
            
class EmpresaForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all().order_by('nome'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Categorias e Tags"
    )

    # Campo de imagem inicial para criação
    imagem = forms.ImageField( 
        label="Imagem Principal da Empresa",
        required=False, # Será obrigatório na view se for criação
        # ✅ CORREÇÃO: Usar ClearableFileInput ✅
        widget=forms.ClearableFileInput() 
    )
    
    # Campo para adicionar mais imagens na edição (definido no __init__)
    novas_imagens = None # Inicializa como None

    class Meta:
        model = Empresa
        # ✅ LISTA DE CAMPOS CORRIGIDA ✅
        fields = [
            'nome', 'tags', 'descricao', 
            'rua', 'bairro', 'cidade', 'numero', 'cep',
            'latitude', 'longitude', 
            'telefone', 'email', 'contato_direto', 
            'site', 'facebook', 'instagram', 
            'cnpj', 'cadastrur', 
            'sem_telefone', 'sem_email',
            # 'imagem' e 'novas_imagens' são tratados separadamente no __init__
        ]
        
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva o estabelecimento'}),
            'cnpj': forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
            'cadastrur': forms.TextInput(attrs={'placeholder': 'Código Cadastur (se houver)'}),
            'contato_direto': forms.TextInput(attrs={'placeholder': 'Nome/WhatsApp da pessoa de contato'}),
            'site': forms.URLInput(attrs={'placeholder': 'https://seuwebsite.com'}),
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com/suaempresa'}),
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com/suaempresa'}),
            'latitude': forms.TextInput(attrs={'placeholder': 'Latitude', 'inputmode': 'decimal'}),
            'longitude': forms.TextInput(attrs={'placeholder': 'Longitude', 'inputmode': 'decimal'}),
            'tags': forms.CheckboxSelectMultiple(), # Redundante, mas garante
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        is_editing = instance and instance.pk
        
        super().__init__(*args, **kwargs)

        # Adiciona os campos de imagem condicionalmente
        if is_editing:
             self.fields['novas_imagens'] = forms.ImageField(
                label="Adicionar novas imagens (até 5 no total)",
                required=False,
                # ✅ CORREÇÃO: Usar ClearableFileInput, mas o template adicionará 'multiple' ✅
                widget=forms.ClearableFileInput(attrs={'multiple': True}) # O attr multiple aqui é só para o HTML
            )
        else: # Criação
            self.fields['imagem'] = forms.ImageField(
                label="Imagem Principal da Empresa",
                required=True, # Imagem é obrigatória na criação
                 # ✅ CORREÇÃO: Usar ClearableFileInput ✅
                widget=forms.ClearableFileInput()
            )
        
        # Aplica classes CSS aos widgets
        for name, field in self.fields.items():
            if name == 'tags': continue # Já estilizado no template
            
            base_class = 'form-control'
            size_class = 'form-control-lg' 
            
            if isinstance(field.widget, forms.Select):
                base_class = 'form-select'
            elif isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                 base_class = 'form-check-input'
                 size_class = ''
            # ✅ CORREÇÃO: Voltar a usar ClearableFileInput ✅
            elif isinstance(field.widget, forms.ClearableFileInput): 
                size_class = 'form-control-sm'

            current_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{base_class} {size_class} {current_classes}'.strip()

    # ... (resto do seu EmpresaForm clean methods) ...
    def clean_novas_imagens(self):
        # Validação movida para a view onde temos acesso ao request.FILES
        return self.cleaned_data.get('novas_imagens')
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            cleaned_cnpj = clean_digits(cnpj)
            if not is_valid_cnpj(cleaned_cnpj):
                 raise forms.ValidationError("CNPJ inválido.")
            
            # Verifica unicidade apenas se estiver editando
            if self.instance and self.instance.pk:
                query = Empresa.objects.filter(cnpj=cleaned_cnpj).exclude(pk=self.instance.pk)
            else: # Se for criação
                 query = Empresa.objects.filter(cnpj=cleaned_cnpj)

            if query.exists():
                raise forms.ValidationError("Já existe uma empresa cadastrada com este CNPJ.")
            return cleaned_cnpj # Salva apenas dígitos
        return cnpj # Retorna None ou vazio se não foi preenchido
    
    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if cep:
            return _clip_model(Empresa, 'cep', clean_digits(cep))
        return cep

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone and not self.cleaned_data.get('sem_telefone'):
            tel = clean_digits(telefone)
            if len(tel) not in (10, 11):
                raise ValidationError("O telefone deve ter 10 ou 11 dígitos (com DDD).")
            return _clip_model(Empresa, 'telefone', tel) # Salva apenas dígitos
        return None # Retorna None se 'sem_telefone' ou vazio

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        # Permitir caracteres não numéricos como 'S/N' ou 'apto 101'
        # if numero and not numero.isdigit():
        #     raise ValidationError("O número deve conter apenas dígitos.")
        return _clip_model(Empresa, 'numero', numero)

    def clean(self):
        cleaned = super().clean()
        sem_telefone = cleaned.get('sem_telefone')
        sem_email = cleaned.get('sem_email')
        telefone = cleaned.get('telefone')
        email = cleaned.get('email')
        
        # Ajuste: A validação de obrigatoriedade deve ser feita no modelo ou na view
        # if not sem_telefone and not telefone:
        #     self.add_error('telefone', 'Informe o telefone ou marque "Sem Telefone".')
        # if not sem_email and not email:
        #     self.add_error('email', 'Informe o e-mail ou marque "Sem Email".')
            
        if sem_telefone: cleaned['telefone'] = None # Garante None se marcado
        if sem_email: cleaned['email'] = None # Garante None se marcado
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
        digits = clean_digits(raw)
        if len(digits) != 11 or not is_valid_cpf(digits):
            raise forms.ValidationError("CPF inválido.")
        qs = PerfilUsuario.objects.filter(cpf_cnpj=digits).exclude(user=self.user)
        if qs.exists():
            raise forms.ValidationError("Este CPF já está em uso por outra conta.")
        return digits # Retorna apenas dígitos

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        if not pwd or not self.user.check_password(pwd):
            self.add_error('password', "Senha atual incorreta.") # Adiciona erro ao campo específico
        return cleaned
    
class AvaliacaoForm(forms.ModelForm):
    nota = forms.ChoiceField(
        choices=[(i, f'{i}') for i in range(1, 6)], # Simplificado
        widget=forms.RadioSelect, # Deixa o template controlar a aparência
        label="Sua nota (de 1 a 5 estrelas)"
    )

    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'rows': 3, # Menos linhas por padrão
                'placeholder': 'Conte como foi sua experiência (opcional)...'
            })
        }
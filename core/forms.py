import re
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Categoria, PerfilUsuario, Empresa
from django.contrib.auth import authenticate

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
        email = self.cleaned_data.get('email')
        email = email.lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso.')
        return email

    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if PerfilUsuario.objects.filter(cpf_cnpj=cpf_cnpj).exists():
            raise ValidationError('Este CPF/CNPJ já está em uso.')
        return cpf_cnpj

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise ValidationError('As senhas não correspondem.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.email = user.email.lower()
        if commit:
            user.save()
            PerfilUsuario.objects.create(
                user=user,
                cpf_cnpj=self.cleaned_data['cpf_cnpj'],
                full_name=self.cleaned_data['full_name']
            )
        return user

class EmpresaForm(forms.ModelForm):
    sem_telefone = forms.BooleanField(required=False, label="Sem Telefone")
    sem_email = forms.BooleanField(required=False, label="Sem Email")

    class Meta:
        model = Empresa
        fields = [
            'nome', 'categoria', 'descricao', 'rua', 'bairro', 'cidade', 
            'numero', 'cep', 'telefone', 'email', 'site', 'imagem', 
            'latitude', 'longitude', 'facebook', 'instagram',
            'sem_telefone', 'sem_email'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Digite o nome da empresa'}),
            'categoria': forms.Select(),
            'descricao': forms.Textarea(attrs={'placeholder': 'Digite a descrição da empresa'}),
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
        # Adicionando labels amigáveis para os campos
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
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput, forms.ClearableFileInput, forms.Select)):
                field.widget.attrs.update({'class': 'form-control form-control-lg'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-lg'})

    # --- NOVAS VALIDAÇÕES ---

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero and not numero.isdigit():
            raise ValidationError("O número deve conter apenas dígitos.")
        return numero

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove todos os caracteres que não são números
            telefone_limpo = re.sub(r'\D', '', telefone)
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
                raise ValidationError("O telefone deve ter 10 ou 11 dígitos (com DDD).")
            return telefone_limpo
        return telefone

    def clean_facebook(self):
        url = self.cleaned_data.get('facebook')
        if url and 'facebook.com' not in url.lower():
            raise ValidationError("Por favor, insira um link válido do Facebook.")
        return url

    def clean_instagram(self):
        url = self.cleaned_data.get('instagram')
        if url and 'instagram.com' not in url.lower():
            raise ValidationError("Por favor, insira um link válido do Instagram.")
        return url

    # 4. Lógica de validação central, agora CORRIGIDA
    def clean(self):
        cleaned_data = super().clean()
        
        sem_telefone = cleaned_data.get('sem_telefone')
        sem_email = cleaned_data.get('sem_email')
        
        telefone = cleaned_data.get('telefone')
        email = cleaned_data.get('email')

        # Se "Sem Telefone" NÃO estiver marcado e o campo telefone estiver vazio, gera um erro.
        if not sem_telefone and not telefone:
            self.add_error('telefone', 'Este campo é obrigatório ou marque "Sem Telefone".')

        # Se "Sem Email" NÃO estiver marcado e o campo email estiver vazio, gera um erro.
        if not sem_email and not email:
            self.add_error('email', 'Este campo é obrigatório ou marque "Sem Email".')
        
        # Se o checkbox estiver marcado, garantimos que o valor seja salvo como nulo/vazio.
        if sem_telefone:
            cleaned_data['telefone'] = ''
        
        if sem_email:
            cleaned_data['email'] = ''

        return cleaned_data
     
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
        identificador = self.cleaned_data.get('identificador')
        password = self.cleaned_data.get('password')

        identificador = identificador.lower()

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
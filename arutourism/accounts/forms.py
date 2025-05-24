from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import PerfilUsuario, Empresa

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
        if commit:
            user.save()
            PerfilUsuario.objects.create(
                user=user,
                cpf_cnpj=self.cleaned_data['cpf_cnpj'],
                full_name=self.cleaned_data['full_name']
            )
        return user


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nome', 'categoria', 'descricao', 'endereco', 'telefone', 'email', 'site', 'imagem']
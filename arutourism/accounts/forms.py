from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Empresa

import re

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    cpf_cnpj = forms.CharField(max_length=18)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    # Validação de email único
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso.')
        return email

    # Validação de CPF ou CNPJ
    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if re.match(r'^\d{11}$', cpf_cnpj):  # CPF
            if User.objects.filter(profile__cpf=cpf_cnpj).exists():  # Verifique se o CPF existe no modelo de perfil
                raise ValidationError('Este CPF já está em uso.')
        elif re.match(r'^\d{14}$', cpf_cnpj):  # CNPJ
            if User.objects.filter(profile__cnpj=cpf_cnpj).exists():  # Verifique se o CNPJ existe no modelo de perfil
                raise ValidationError('Este CNPJ já está em uso.')
        else:
            raise ValidationError('Por favor, insira um CPF ou CNPJ válido.')
        return cpf_cnpj

    # Validar se as senhas coincidem
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError('As senhas não correspondem.')

        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    
    
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nome', 'categoria', 'descricao', 'endereco', 'telefone', 'email', 'site', 'imagem']
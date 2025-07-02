# arutourism/core/tests.py

import time
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import PerfilUsuario, Categoria, Empresa

class PaginaLoginTest(TestCase):

    def test_pagina_login_carrega_corretamente(self):
        print("\n🧪 Testando se a página de login carrega (GET)...")
        url = reverse('login')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        print("✅ OK: Página de login retornou status 200.")

    def test_pagina_login_usa_template_correto(self):
        print("\n🧪 Testando se a página de login usa o template correto...")
        url = reverse('login')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response, 'core/login.html')
        print("✅ OK: Template 'core/login.html' foi utilizado.")

class TestesFuncionalidadesCRUD(TestCase):

    def setUp(self):
        print("\n⚙️  CONFIGURANDO AMBIENTE DE TESTE (setUp)...")
        self.categoria = Categoria.objects.create(nome='Restaurante')
        self.user = User.objects.create_user(username='testuser', password='password123')
        PerfilUsuario.objects.create(user=self.user, cpf_cnpj='12345678900', full_name='Test User')
        print(" -> Categoria 'Restaurante' e usuário 'testuser' criados.")

    def test_cadastro_de_usuario_sucesso(self):
        print("\n🧪 Testando fluxo de cadastro de um novo usuário (POST)...")
        form_data = {
            'username': 'novousuario',
            'email': 'novo@email.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'cpf_cnpj': '98765432100',
            'full_name': 'Novo Usuario'
        }
        url = reverse('register')
        response = self.client.post(url, data=form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='novousuario').exists())
        self.assertTrue(PerfilUsuario.objects.filter(cpf_cnpj='98765432100').exists())
        print("✅ OK: Usuário 'novousuario' criado e redirecionado para login.")

    def test_cadastro_de_empresa_sucesso(self):
        print("\n🧪 Testando cadastro de nova empresa por usuário logado (POST AJAX)...")
        self.client.login(username='testuser', password='password123')
        print(" -> Usuário 'testuser' logado.")
        
        form_data = {
            'nome': 'Pizzaria Teste',
            'categoria': self.categoria.id,
            'descricao': 'Melhor pizza da cidade.',
            'rua': 'Rua dos Testes', 'bairro': 'Centro', 'cidade': 'Araranguá',
            'numero': '123', 'cep': '88900000',
            'telefone': '48999998888', 'email': 'contato@pizzaria.com'
        }
        
        url = reverse('cadastrar_empresa')
        response = self.client.post(url, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Empresa.objects.filter(nome='Pizzaria Teste').exists())
        self.assertEqual(response.json()['status'], 'success')
        print("✅ OK: Empresa 'Pizzaria Teste' criada com sucesso via JSON.")
        
    def test_edicao_de_empresa_sucesso(self):
        print("\n🧪 Testando edição de empresa por usuário logado (POST)...")
        self.client.login(username='testuser', password='password123')
        print(" -> Usuário 'testuser' logado.")

        empresa_para_editar = Empresa.objects.create(
            user=self.user, nome='Nome Antigo', categoria=self.categoria,
            descricao='Desc antiga', rua='Rua Antiga', bairro='Bairro Antigo',
            cidade='Cidade Antiga', numero='1', cep='12345678',
            telefone='11111111111', email='antigo@email.com'
        )
        print(f" -> Empresa 'Nome Antigo' (ID: {empresa_para_editar.id}) criada para edição.")
        
        form_data_atualizado = {
            'nome': 'Nome Novo Editado', 'categoria': self.categoria.id,
            'descricao': 'Descrição nova e atualizada.', 'rua': 'Rua Nova',
            'bairro': 'Bairro Novo', 'cidade': 'Cidade Nova', 'numero': '2',
            'cep': '87654321', 'telefone': '22222222222', 'email': 'novo@email.com'
        }

        url = reverse('editar_empresa', kwargs={'empresa_id': empresa_para_editar.id})
        response = self.client.post(url, data=form_data_atualizado)

        self.assertEqual(response.status_code, 302)
        empresa_para_editar.refresh_from_db()
        self.assertEqual(empresa_para_editar.nome, 'Nome Novo Editado')
        print("✅ OK: Empresa atualizada para 'Nome Novo Editado' e redirecionada.")
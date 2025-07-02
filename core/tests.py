from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import PerfilUsuario, Categoria, Empresa

class PaginaLoginTest(TestCase):

    def test_pagina_login_carrega_corretamente(self):
        """
            Testa se a página de login retorna o status code 200,
            indicando que foi carregada com sucesso.
        """
        # Acessamos a URL usando o nome 'login' que está no seu urls.py
        # linha: path('login/', views.login_view, name='login')
        url = reverse('login')
        
        # O cliente de teste faz uma requisição GET para a URL
        response = self.client.get(url)
        
        # Verificamos se o status da resposta é 200 (OK)
        self.assertEqual(response.status_code, 200)

    def test_pagina_login_usa_template_correto(self):
        """
        Testa se a view de login está renderizando o template correto.
        """
        # Novamente, acessamos a URL pelo nome 'login'
        url = reverse('login')
        response = self.client.get(url)
        
        # Verificamos se o template usado para renderizar a página
        # é exatamente o 'core/login.html' que está na sua view.
        # linha: return render(request, 'core/login.html', {'form': form})
        self.assertTemplateUsed(response, 'core/login.html')

class TestesFuncionalidadesCRUD(TestCase):

    # O método setUp roda ANTES de cada teste nesta classe.
    # Usamos para criar objetos que serão usados em múltiplos testes.
    def setUp(self):
        # Criamos uma categoria para usar no cadastro de empresas
        self.categoria = Categoria.objects.create(nome='Restaurante')
        
        # Criamos um usuário que será usado para logar e criar/editar empresas
        self.user = User.objects.create_user(username='testuser', password='password123')
        PerfilUsuario.objects.create(user=self.user, cpf_cnpj='12345678900', full_name='Test User')

    def test_cadastro_de_usuario_sucesso(self):
        """
            Testa se um novo usuário pode se registrar com sucesso.
        """
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

    def test_cadastro_de_empresa_sucesso(self):
        """
            Testa se um usuário logado pode cadastrar uma nova empresa.
            A sua view retorna JSON, então o teste será um pouco diferente.
        """
        self.client.login(username='testuser', password='password123')
        form_data = {
            'nome': 'Pizzaria Teste',
            'categoria': self.categoria.id,
            'descricao': 'Melhor pizza da cidade.',
            'rua': 'Rua dos Testes',
            'bairro': 'Centro',
            'cidade': 'Araranguá',
            'numero': '123',
            'cep': '88900000',
            'telefone': '48999998888',
            'email': 'contato@pizzaria.com'
        }
        url = reverse('cadastrar_empresa')
        response = self.client.post(url, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Empresa.objects.filter(nome='Pizzaria Teste').exists())
        json_response = response.json()
        self.assertEqual(json_response['status'], 'success')
        
    def test_edicao_de_empresa_sucesso(self):
        """
            Testa se o dono de uma empresa pode editá-la com sucesso.
        """
        self.client.login(username='testuser', password='password123')
        
        # Corrigindo a criação da empresa para ser mais explícita
        empresa_para_editar = Empresa.objects.create(
            user=self.user,
            nome='Nome Antigo',
            categoria=self.categoria,
            descricao='Desc antiga',
            rua='Rua Antiga',
            bairro='Bairro Antigo',
            cidade='Cidade Antiga',
            numero='1',
            cep='12345678', # Usando string para CEP
            telefone='11111111111', # Adicionando os campos obrigatórios
            email='antigo@email.com'
        )
        
        # Dados atualizados do formulário - AGORA COM TODOS OS CAMPOS OBRIGATÓRIOS
        form_data_atualizado = {
            'nome': 'Nome Novo Editado',
            'categoria': self.categoria.id,
            'descricao': 'Descrição nova e atualizada.',
            'rua': 'Rua Nova',
            'bairro': 'Bairro Novo',
            'cidade': 'Cidade Nova',
            'numero': '2',
            'cep': '87654321',
            'telefone': '22222222222',  # <-- CAMPO ADICIONADO
            'email': 'novo@email.com'  # <-- CAMPO ADICIONADO
        }

        url = reverse('editar_empresa', kwargs={'empresa_id': empresa_para_editar.id})
        response = self.client.post(url, data=form_data_atualizado)

        # 1. Agora esta verificação deve passar!
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('suas_empresas'))

        empresa_para_editar.refresh_from_db()
        
        # 2. Verifica se o nome da empresa foi realmente atualizado
        self.assertEqual(empresa_para_editar.nome, 'Nome Novo Editado')
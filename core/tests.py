from __future__ import annotations
import re  # ✅ necessário para extrair a URL do email
import io
from pathlib import Path
import time

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django import forms

from core.forms import UserRegistrationForm, CustomLoginForm, EmpresaForm
from core.models import PerfilUsuario, Empresa, Categoria

# Para gerar XLSX em memória
from openpyxl import Workbook

# ========= Helpers =========

def make_image_file(name="test.jpg", content=b"\xFF\xD8\xFF\xD9"):
    # JPEG mínimo (SOI + EOI)
    return SimpleUploadedFile(name, content, content_type="image/jpeg")

def make_text_file(name="note.txt", content=b"not an image"):
    return SimpleUploadedFile(name, content, content_type="text/plain")

def make_xlsx_bytes(headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.getvalue()


# ========== Decorator padrão para todos os testes ==========
# Evita crash de staticfiles (manifest) e warnings de diretórios ausentes
TEST_OVERRIDES = dict(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    STATICFILES_DIRS=[],
)

# ========= Testes =========

@override_settings(**TEST_OVERRIDES)
class PaginaLoginTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n\n🔵  SUITE: PÁGINA DE LOGIN")

    def test_pagina_login_carrega_corretamente(self):
        print("🧪 GET /login/ ...", end=" ")
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        print("✅ 200 OK")

    def test_pagina_login_usa_template_correto(self):
        print("🧪 Template correto em /login/ ...", end=" ")
        url = reverse('login')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'core/login.html')
        print("✅ template ok")


@override_settings(**TEST_OVERRIDES)
class TestesFuncionalidadesCRUD(TestCase):
    def setUp(self):
        print("\n\n🟣  SUITE: CRUD BÁSICO")
        self.categoria = Categoria.objects.create(nome='Restaurante')
        self.user = User.objects.create_user(username='testuser', password='password123')
        PerfilUsuario.objects.create(user=self.user, cpf_cnpj='12345678900', full_name='Test User')
        print("⚙️  setUp -> categoria 'Restaurante' e usuário 'testuser' prontos.")

    def test_cadastro_de_usuario_sucesso(self):
        print("🧪 Cadastro de usuário (POST) ...", end=" ")
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
        print("✅ ok (redireciona p/ login)")

    def test_cadastro_de_empresa_sucesso(self):
        print("🧪 Cadastro de empresa via JSON (POST) ...", end=" ")
        self.client.login(username='testuser', password='password123')
        form_data = {
            'nome': 'Pizzaria Teste',
            'categoria': self.categoria.id,
            'descricao': 'Melhor pizza da cidade.',
            'rua': 'Rua dos Testes', 'bairro': 'Centro', 'cidade': 'Araranguá',
            'numero': '123', 'cep': '88900000',
            'telefone': '48999998888', 'email': 'contato@pizzaria.com'
        }
        url = reverse('cadastrar_empresa')
        # ✅ AVISA que quer JSON (a view verifica Accept, não X-Requested-With)
        response = self.client.post(
            url,
            data=form_data,
            HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(Empresa.objects.filter(nome='Pizzaria Teste').exists())
        self.assertEqual(response.json().get('status'), 'success')
        print("✅ ok (200 + JSON)")

    def test_edicao_de_empresa_sucesso(self):
        print("🧪 Edição de empresa (POST) ...", end=" ")
        self.client.login(username='testuser', password='password123')
        empresa = Empresa.objects.create(
            user=self.user, nome='Nome Antigo', categoria=self.categoria,
            descricao='Desc antiga', rua='Rua Antiga', bairro='Bairro Antigo',
            cidade='Cidade Antiga', numero='1', cep='12345678',
            telefone='11111111111', email='antigo@email.com'
        )
        form_data_atualizado = {
            'nome': 'Nome Novo Editado', 'categoria': self.categoria.id,
            'descricao': 'Descrição nova e atualizada.', 'rua': 'Rua Nova',
            'bairro': 'Bairro Novo', 'cidade': 'Cidade Nova', 'numero': '2',
            'cep': '87654321', 'telefone': '22222222222', 'email': 'novo@email.com'
        }
        url = reverse('editar_empresa', kwargs={'empresa_id': empresa.id})
        response = self.client.post(url, data=form_data_atualizado)
        self.assertEqual(response.status_code, 302)
        empresa.refresh_from_db()
        self.assertEqual(empresa.nome, 'Nome Novo Editado')
        print("✅ ok (302 + atualizado)")


# ========= Base de usuários/objetos =========

@override_settings(**TEST_OVERRIDES)
class BaseSetup(TestCase):
    def setUp(self):
        self.client = Client()
        # Usuário 1
        self.user = User.objects.create_user(
            username="teste", email="teste@example.com", password="Senha@123"
        )
        PerfilUsuario.objects.create(user=self.user, cpf_cnpj="12345678900", full_name="Teste Um")

        # Usuário 2
        self.user2 = User.objects.create_user(
            username="outro", email="outro@example.com", password="Senha@123"
        )
        PerfilUsuario.objects.create(user=self.user2, cpf_cnpj="98765432100", full_name="Teste Dois")

        # Categoria
        self.cat = Categoria.objects.create(nome="Pousada")


# ========= Registro & Login =========

@override_settings(**TEST_OVERRIDES)
class AuthTests(BaseSetup):
    def test_registration_unique_email_and_cpf(self):
        # e-mail já usado
        form = UserRegistrationForm(data={
            "username": "novo",
            "email": "teste@example.com",
            "password": "Abc12345!",
            "confirm_password": "Abc12345!",
            "cpf_cnpj": "11111111111",
            "full_name": "Novo Usuário"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

        # cpf já usado
        form = UserRegistrationForm(data={
            "username": "novo2",
            "email": "novo2@example.com",
            "password": "Abc12345!",
            "confirm_password": "Abc12345!",
            "cpf_cnpj": "12345678900",  # já existe
            "full_name": "Novo Usuário"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("cpf_cnpj", form.errors)

        # senhas não correspondem
        form = UserRegistrationForm(data={
            "username": "novo3",
            "email": "novo3@example.com",
            "password": "Abc12345!",
            "confirm_password": "Abc12345!X",
            "cpf_cnpj": "22222222222",
            "full_name": "Outro"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

        # registro OK
        form = UserRegistrationForm(data={
            "username": "ok",
            "email": "ok@example.com",
            "password": "Abc12345!",
            "confirm_password": "Abc12345!",
            "cpf_cnpj": "33333333333",
            "full_name": "Valido"
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(User.objects.filter(username="ok").exists())
        self.assertTrue(PerfilUsuario.objects.filter(user=user, cpf_cnpj="33333333333").exists())

    def test_login_by_username_email_cpf(self):
        # username
        form = CustomLoginForm(data={"identificador": "teste", "password": "Senha@123"})
        self.assertTrue(form.is_valid())

        # email
        form = CustomLoginForm(data={"identificador": "teste@example.com", "password": "Senha@123"})
        self.assertTrue(form.is_valid())

        # cpf
        form = CustomLoginForm(data={"identificador": "12345678900", "password": "Senha@123"})
        self.assertTrue(form.is_valid())

        # errado
        form = CustomLoginForm(data={"identificador": "teste", "password": "errada"})
        self.assertFalse(form.is_valid())


# ========= EmpresaForm validações =========

@override_settings(**TEST_OVERRIDES)
class EmpresaFormTests(BaseSetup):
    def test_numero_digits_only(self):
        form = EmpresaForm(data={
            "nome": "E1", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12A",
            "cep": "88900000", "telefone": "48999999999", "email": "e@e.com",
            "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("numero", form.errors)

    def test_telefone_len_and_clean(self):
        form = EmpresaForm(data={
            "nome": "E1", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12",
            "cep": "88900000", "telefone": "(48) 99999-9999", "email": "e@e.com",
            "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertTrue(form.is_valid(), form.errors)
        # clean_telefone retorna apenas dígitos (11)
        self.assertEqual(form.cleaned_data["telefone"], "48999999999")

    def test_sem_telefone_email_logic(self):
        form = EmpresaForm(data={
            "nome": "E1", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12",
            "cep": "88900000", "telefone": "", "sem_telefone": "on",
            "email": "e@e.com", "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["telefone"], "")

        form = EmpresaForm(data={
            "nome": "E2", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12",
            "cep": "88900000", "telefone": "48999999999", "email": "",
            "sem_email": "on", "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "")

        form = EmpresaForm(data={
            "nome": "E3", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12",
            "cep": "88900000", "telefone": "", "email": "",
            "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)
        self.assertIn("email", form.errors)

    def test_social_urls(self):
        form = EmpresaForm(data={
            "nome": "E1", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12",
            "cep": "88900000", "telefone": "48999999999", "email": "e@e.com",
            "facebook": "https://x.com/abc", "instagram": "https://instagram.com/ok",
            "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("facebook", form.errors)

        form = EmpresaForm(data={
            "nome": "E1", "categoria": self.cat.id, "descricao": "",
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "12",
            "cep": "88900000", "telefone": "48999999999", "email": "e@e.com",
            "facebook": "https://facebook.com/ok", "instagram": "https://site.com/abc",
            "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("instagram", form.errors)


# ========= Views de Empresa (CRUD / Listas) =========

@override_settings(**TEST_OVERRIDES)
class EmpresaViewsTests(BaseSetup):
    def login(self, which=1):
        user = self.user if which == 1 else self.user2
        self.client.login(username=user.username, password="Senha@123")
        return user

    def test_create_empresa_ok(self):
        print("\n🧪 POST /empresas/cadastrar/ ...", end=" ")
        self.login(1)
        url = reverse("cadastrar_empresa")
        resp = self.client.post(url, {
            "nome": "Hotel Azul",
            "categoria": self.cat.id,
            "descricao": "desc",
            "rua": "Av",
            "bairro": "Centro",
            "cidade": "Araranguá",
            "numero": "100",
            "cep": "88900000",
            "telefone": "48999999999",
            "email": "h@hotel.com",
            "latitude": "-28.9371",
            "longitude": "-49.4840",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Empresa.objects.filter(nome="Hotel Azul", user=self.user).exists())
        print("✅ ok")

    def test_create_empresa_without_name_fails(self):
        self.login(1)
        url = reverse("cadastrar_empresa")
        resp = self.client.post(url, {
            "nome": "",
            "categoria": self.cat.id,
            "rua": "Av", "bairro": "B", "cidade": "C", "numero": "1",
            "cep": "88900000", "telefone": "48999999999", "email": "e@e.com",
            "latitude": "-28.9", "longitude": "-49.48"
        })
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "Este campo", status_code=400)

    def test_edit_empresa_only_owner(self):
        self.login(1)
        e = Empresa.objects.create(
            user=self.user, nome="X", categoria=self.cat,
            rua="R", bairro="B", cidade="C", numero="1", cep="88900000",
            telefone="48999999999", email="e@e.com",
            latitude="-28.9", longitude="-49.48"
        )
        # dono consegue
        url = reverse("editar_empresa", args=[e.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # não-dono -> 404
        self.client.logout()
        self.login(2)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_image_upload_invalid_type(self):
        self.login(1)
        url = reverse("cadastrar_empresa")
        data = {
            "nome": "ComArquivo",
            "categoria": self.cat.id,
            "rua": "R", "bairro": "B", "cidade": "C", "numero": "1",
            "cep": "88900000", "telefone": "48999999999", "email": "e@e.com",
            "latitude": "-28.9", "longitude": "-49.48",
            # arquivo "não imagem"
            "imagem": make_text_file(),   # <<< aqui, dentro do data
        }
        resp = self.client.post(url, data, follow=False)  # não seguir redirect
        # espera 400 porque ImageField/validação deve falhar
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "imagem", status_code=400)

    def test_minhas_empresas_paginacao_ajax(self):
        self.login(1)
        for i in range(7):
            Empresa.objects.create(
                user=self.user, nome=f"E{i}", categoria=self.cat,
                rua="R", bairro="B", cidade="C", numero="1", cep="88900000",
                telefone="48999999999", email="e@e.com",
                latitude="-28.9", longitude="-49.48"
            )
        url = reverse("suas_empresas")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # ajax page 2
        resp = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest", data={"page": 2})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("html", resp.json())
        self.assertIn("has_next", resp.json())


# ========= Importação XLSX =========

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", **TEST_OVERRIDES)
class ImportacaoTests(BaseSetup):
    def test_importar_xlsx_ok(self):
        self.client.login(username="teste", password="Senha@123")
        url = reverse("importar_empresas_arquivo")

        headers = [
            "CNPJ", "CATEGORIA (RAMO ATIVIDADE)", "NOME", "BAIRRO",
            "ENDEREÇO COMPLETO", "TELEFONE", "CONTATO DIRETO",
            "DIGITAL (site/redes)", "CADASTUR", "MAPS (link)", "APP",
            "DESCRIÇÃO", "NÚMERO", "CEP", "CIDADE"
        ]
        rows = [[
            "12.345.678/0001-99", "Pousada", "Pousada Teste", "Centro",
            "Av. Central, 123", "(48) 99999-9999", "Maria",
            "https://exemplo.com", "", "https://maps.google.com/?q=-28.93,-49.48",
            "", "Desc", "123", "88900000", "Araranguá"
        ]]
        content = make_xlsx_bytes(headers, rows)
        up = SimpleUploadedFile(
            "empresas.xlsx", content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resp = self.client.post(url, {"arquivo": up})
        self.assertEqual(resp.status_code, 200, resp.content)
        j = resp.json()
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("importados"), 1)
        self.assertTrue(Empresa.objects.filter(nome="Pousada Teste").exists())


# ========= Password: troca e reset =========

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", **TEST_OVERRIDES)
class PasswordFlowTests(BaseSetup):
    def test_password_change_authenticated(self):
        print("\n🧪 Troca de senha autenticado ...", end=" ")
        self.client.login(username="teste", password="Senha@123")
        url = reverse("trocar_senha")
        resp = self.client.post(url, {
            "old_password": "Senha@123",
            "new_password1": "NovaSenha@123",
            "new_password2": "NovaSenha@123",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
        ok = self.client.login(username="teste", password="NovaSenha@123")
        self.assertTrue(ok)
        print("✅ ok")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@testserver",
    **TEST_OVERRIDES,
)
class PasswordResetEmailFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teste",
            email="teste@example.com",
            password="SenhaAntiga!123",
        )

    def _extract_reset_url(self, body: str) -> str:
        """
        Procura a 1ª URL gerada pelo template de e-mail:
        /senha/redefinir/<uidb64>/<token>/set-password/
        """
        m = re.search(r"https?://[^\s]+", body)
        if not m:
            self.fail(f"Não encontrei nenhuma URL no corpo do e-mail:\n{body}")
        return m.group(0)

def test_password_reset_email_flow_generates_link_and_works(self):
        # 1) dispara o e-mail de reset
        url = reverse("esqueci_senha_email")
        resp = self.client.post(url, {"email": "teste@example.com"}, follow=True)
        self.assertEqual(resp.status_code, 200)

        # 2) foi enviado 1 e-mail com link
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        reset_url = self._extract_reset_url(body)
        # Aceita o formato sem 'set-password/'
        self.assertIn("/senha/redefinir/", reset_url)

        # 3) abre a página de "definir nova senha"
        resp = self.client.get(reset_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Definir nova senha")

        # 4) define a nova senha
        nova = "NovaSenha@123!"
        resp = self.client.post(
            reset_url,
            {"new_password1": nova, "new_password2": nova},
            follow=True,
        )
        # deve ir para a página de "concluído"
        self.assertEqual(resp.status_code, 200)
        final_path = resp.request.get("PATH_INFO", "")
        self.assertEqual(final_path, reverse("password_reset_complete"))

        # 5) a senha mudou
        self.client.logout()
        self.assertFalse(self.client.login(username="teste", password="SenhaAntiga!123"))
        self.assertTrue(self.client.login(username="teste", password=nova))

        # 6) o mesmo link não deve mais funcionar depois do uso
        resp = self.client.get(reset_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Link inválido", status_code=200)

class EmpresaForm(forms.ModelForm):
    ...
    def clean_imagem(self):
        f = self.cleaned_data.get("imagem")
        if not f:
            return f
        # alguns storages usam content_type "", por via das dúvidas cheque a extensão também
        ct = getattr(f, "content_type", "")
        if ct and not ct.startswith("image/"):
            raise forms.ValidationError("Envie um arquivo de imagem válido (JPEG/PNG, etc.).")
        # tamanho opcional:
        # if f.size > 5 * 1024 * 1024:
        #     raise forms.ValidationError("Imagem muito grande (máx 5MB).")
        return f
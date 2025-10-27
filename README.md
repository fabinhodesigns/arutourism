# AruTourism - Sistema de Inventário Turístico Municipal

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-FFFFFF?style=for-the-badge&logo=postgresql)
![Heroku](https://img.shields.io/badge/Heroku-430098?style=for-the-badge&logo=heroku)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

O AruTourism é uma plataforma web projetada para solucionar o problema da informação turística dispersa e inacessível em municípios. O sistema centraliza dados de atrativos e serviços em um inventário acessível e responsivo, demonstrando um modelo viável e replicável para o fortalecimento do turismo local com foco na inclusão digital.

---

###  Tela Inicial

![Demonstração do AruTourism]([https://res.cloudinary.com/diqrjhtod/image/upload/v1720023414/git-readme/tela_cadastro_git_y9o0u2.png](https://res-console.cloudinary.com/diqrjhtod/thumbnails/v1/image/upload/v1751473772/QVJVVE9VUklTTV9JTklDSUFMX3JqZ3lwNA==/drilldown))

---

### 📜 Sobre o Projeto

O turismo é um catalisador fundamental para o desenvolvimento, mas seu potencial é frequentemente subutilizado devido à carência de informação organizada. Em muitos municípios, dados sobre atrativos e serviços encontram-se dispersos, dificultando o acesso para visitantes e moradores. Agrava-se a este cenário a falta de recursos de acessibilidade digital, comprometendo a inclusão de pessoas com deficiência.

O AruTourism nasceu para resolver este problema, oferecendo uma solução tecnológica que centraliza, organiza e divulga o inventário turístico municipal de forma moderna, inclusiva e sustentável.

### ✨ Principais Funcionalidades

-   **Gestão Completa de Empresas (CRUD):** Usuários autenticados podem cadastrar, visualizar, editar e excluir seus próprios estabelecimentos turísticos.
-   **Sistema de Autenticação:** Cadastro e login de usuários com perfis distintos.
-   **Geolocalização Interativa:** Integração com API de mapas (Leaflet.js) que permite ao usuário selecionar a localização exata do seu estabelecimento arrastando um marcador no mapa, que captura automaticamente a latitude e longitude.
-   **Design Responsivo:** Interface adaptável para uma experiência de usuário consistente em desktops, tablets e smartphones.
-   **Validação por Testes:** O projeto conta com testes automatizados para garantir a estabilidade das funcionalidades críticas.
-   **Deploy em Nuvem:** A aplicação está implantada na plataforma Heroku, com banco de dados e arquivos de mídia na nuvem.

### 🏛️ Estrutura do Banco de Dados

O banco de dados foi modelado com quatro entidades principais para garantir a organização e o relacionamento correto dos dados:

-   **User:** Modelo padrão do Django para autenticação.
-   **PerfilUsuario:** Estende o modelo User, armazenando informações adicionais como CPF/CNPJ. (Relacionamento 1-para-1 com User).
-   **Categoria:** Tabela para categorizar os tipos de estabelecimentos (ex: Restaurante, Hotel, Ponto Turístico).
-   **Empresa:** Entidade central que armazena todas as informações do estabelecimento, como nome, descrição, endereço e coordenadas. (Relacionamento N-para-1 com User e com Categoria).

### 🗺️ Uso da API de Mapas

Para a funcionalidade de geolocalização, o projeto utiliza a biblioteca de JavaScript **Leaflet.js** com os mapas do **OpenStreetMap**. Ao cadastrar ou editar uma empresa, um mapa interativo é exibido. O usuário pode navegar e arrastar um marcador (`marker`) para a localização exata. O evento de "soltar o marcador" (`dragend`) dispara uma função em JavaScript que captura as novas coordenadas (`latitude` e `longitude`) e as insere em campos ocultos no formulário, que são então enviados e salvos no banco de dados.

### 🛠️ Tecnologias Utilizadas

O projeto foi construído com as seguintes tecnologias:

-   **Backend:**
    -   Python 3.11
    -   Django 4.2
    -   Gunicorn (Servidor WSGI para produção)
-   **Frontend:**
    -   HTML5
    -   CSS3
    -   JavaScript
    -   Bootstrap 5 (Para responsividade)
-   **Banco de Dados:**
    -   PostgreSQL (em produção)
    -   SQLite3 (em desenvolvimento)
-   **Deploy:**
    -   Heroku (Hospedagem da Aplicação)
    -   Cloudinary (Armazenamento de imagens e mídias)
    -   WhiteNoise (Servir arquivos estáticos)

---

### 🚀 Instalação e Execução Local

Siga os passos abaixo para rodar o projeto em sua máquina local.

**1. Pré-requisitos**

-   [Python 3.11](https://www.python.org/downloads/)
-   [Git](https://git-scm.com/downloads)
-   PostgreSQL (Recomendado para simular o ambiente de produção)

**2. Clone o Repositório**

```bash
git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
cd SEU-REPOSITORIO
```

**3. Crie e Ative a Virtualenv**

```bash
# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Para Windows
python -m venv venv
.\venv\Scripts\activate
```

**4. Instale as Dependências**

```bash
pip install -r requirements.txt
```

**5. Configure as Variáveis de Ambiente**

Crie um arquivo chamado `.env` na raiz do projeto. Ele guardará suas chaves secretas. **NUNCA** envie este arquivo para o GitHub.

Primeiro, crie um arquivo `.env.example` para servir de modelo:
```
# .env.example
SECRET_KEY=
DEBUG=
DATABASE_URL=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```
Agora, crie seu arquivo `.env` e preencha com seus valores:
```
# .env
SECRET_KEY='sua-secret-key-super-segura-aqui'
DEBUG=True
DATABASE_URL='sqlite:///db.sqlite3' # Para usar SQLite localmente
# Se for usar PostgreSQL localmente, o formato é: postgres://USER:PASSWORD@HOST:PORT/DBNAME
CLOUDINARY_CLOUD_NAME='seu_cloud_name_do_cloudinary'
CLOUDINARY_API_KEY='sua_api_key_do_cloudinary'
CLOUDINARY_API_SECRET='seu_api_secret_do_cloudinary'
```
**Importante:** Modifique seu arquivo `settings.py` para ler essas variáveis em vez de deixá-las no código. Instale `python-decouple` (`pip install python-decouple`) e use assim:

```python
# settings.py
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# No lugar das suas credenciais do Cloudinary:
cloudinary.config(
  cloud_name = config('CLOUDINARY_CLOUD_NAME'),  
  api_key = config('CLOUDINARY_API_KEY'),       
  api_secret = config('CLOUDINARY_API_SECRET')   
)
```

**6. Aplique as Migrações do Banco de Dados**

```bash
python3 manage.py migrate
```

**7. Crie um Superusuário**

Você precisará de um superusuário para acessar o painel de administração do Django.

```bash
python3 manage.py createsuperuser
```
Siga as instruções para criar seu usuário e senha.

**8. Inicie o Servidor de Desenvolvimento**

```bash
python3 manage.py runserver
```

Abra seu navegador e acesse `http://127.0.0.1:8000`. Pronto! O projeto está rodando localmente.

---

### 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

### 👨‍💻 Autor

-   **Fabiano Daros Freitas**
-   **Email:** freitasfabiano08@gmail.com
-   **LinkedIn:** [https://www.linkedin.com/in/fabinhofreitas/])

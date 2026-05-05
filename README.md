# CraftAI

CraftAI é uma plataforma de marketplace para produtos personalizados e regulares, com integração de IA para geração de imagens e sugestões de produtos. A plataforma permite que vendedores criem suas lojas, cadastrem produtos e recebam pedidos personalizados ou regulares de clientes.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Stack Tecnológico](#stack-tecnológico)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Executando Localmente](#executando-localmente)
- [Docker](#docker)
- [API Endpoints](#api-endpoints)
- [Testes](#testes)
- [Deploy](#deploy)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Autores](#autores)

---

## 🎯 Visão Geral

CraftAI é uma plataforma completa de e-commerce focada em produtos personalizados, com as seguintes características principais:

- **Marketplace de produtos personalizados**: Clientes podem solicitar produtos personalizados com iterações de IA
- **Produtos regulares**: Vendedores podem oferecer produtos regulares com compra direta
- **Gestão de pedidos**: Sistema completo de gerenciamento de pedidos com múltiplos status
- **Integração com IA**: Geração de imagens usando OpenAI DALL-E
- **Sistema de carrinho**: Carrinho de compras para produtos regulares
- **Autenticação segura**: Sistema de autenticação com JWT e verificação de email

---

## ✨ Funcionalidades

### Para Clientes

- **Registro e Login**: Criação de conta com verificação de email
- **Explorar Lojas**: Navegação por lojas e produtos
- **Pedidos Personalizados**: Solicitação de produtos personalizados com iterações de IA
- **Compra de Produtos Regulares**: Adição ao carrinho e checkout
- **Gerenciamento de Pedidos**: Acompanhamento do status dos pedidos
- **Confirmação de Entrega**: Confirmação de recebimento de pedidos
- **Avaliação de Pedidos**: Marcar pedidos como concluídos

### Para Vendedores

- **Criação de Loja**: Configuração de perfil de vendedor
- **Gestão de Produtos**: Cadastro e edição de produtos
- **Gerenciamento de Pedidos**: Aceitação, rejeição e atualização de status
- **Iterações de IA**: Geração de imagens para pedidos personalizados
- **Dashboard**: Visão geral de vendas e pedidos
- **Filtros de Pedidos**: Filtragem por status e tipo de pedido

### Funcionalidades Técnicas

- **API RESTful**: API completa com FastAPI
- **Validação de Dados**: Validação com Pydantic
- **Banco de Dados Relacional**: PostgreSQL com SQLAlchemy ORM
- **Migrações**: Gerenciamento de migrations com Alembic
- **Upload de Imagens**: Integração com S3 ou armazenamento local
- **Testes Automatizados**: Testes unitários e de integração com pytest
- **Coverage de Testes**: Relatórios de coverage com pytest-cov

---

## 🛠 Stack Tecnológico

### Backend

- **Python 3.12+**: Linguagem principal
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para banco de dados
- **Alembic**: Gerenciamento de migrations
- **Pydantic**: Validação de dados
- **Pydantic Settings**: Gerenciamento de configurações
- **python-jose**: Autenticação JWT
- **bcrypt**: Hash de senhas
- **zxcvbn**: Verificação de força de senhas
- **OpenAI**: API para geração de imagens
- **boto3**: Cliente AWS S3
- **python-multipart**: Upload de arquivos
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **psycopg2-binary**: Driver PostgreSQL
- **requests**: Cliente HTTP

### Frontend

- **React**: Biblioteca UI
- **TypeScript**: Tipagem estática
- **Vite**: Build tool e dev server
- **React Router**: Roteamento
- **TailwindCSS**: Estilização
- **Lucide React**: Ícones
- **Axios**: Cliente HTTP

### Banco de Dados

- **PostgreSQL**: Banco de dados relacional

### DevOps

- **Docker**: Containerização
- **Docker Compose**: Orquestração de containers
- **Git**: Controle de versão

### Testes

- **pytest**: Framework de testes
- **pytest-cov**: Coverage de testes
- **pytest-asyncio**: Testes assíncronos
- **httpx**: Cliente HTTP assíncrono

---

## 📁 Estrutura do Projeto

```
CraftAI/
├── alembic/                          # Migrations do banco de dados
│   ├── versions/                     # Arquivos de migração
│   └── env.py                        # Configuração do Alembic
├── config/                           # Configurações
│   ├── logger.py                     # Configuração de logging
│   └── settings.py                   # Configurações da aplicação
├── scripts/                          # Scripts utilitários
├── src/                              # Código fonte
│   ├── api/                          # Backend FastAPI
│   │   ├── ai/                       # Integração com IA
│   │   │   ├── __init__.py
│   │   │   └── client.py             # Cliente OpenAI
│   │   ├── dependencies/             # Dependências da API
│   │   │   └── auth.py               # Dependências de autenticação
│   │   ├── main.py                   # Entry point da API
│   │   ├── models/                   # Modelos Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Modelos de autenticação
│   │   │   ├── cart.py               # Modelos de carrinho
│   │   │   ├── order.py              # Modelos de pedidos
│   │   │   └── seller.py             # Modelos de vendedores
│   │   ├── repositories/             # Repositories (acesso a dados)
│   │   │   ├── __init__.py
│   │   │   ├── auth_repository.py    # Repository de autenticação
│   │   │   ├── cart_repository.py    # Repository de carrinho
│   │   │   ├── order_repository.py   # Repository de pedidos
│   │   │   └── seller_repository.py  # Repository de vendedores
│   │   ├── routes/                   # Rotas da API
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Rotas de autenticação
│   │   │   ├── cart.py               # Rotas de carrinho
│   │   │   ├── orders.py             # Rotas de pedidos
│   │   │   └── sellers.py            # Rotas de vendedores
│   │   └── services/                 # Serviços de negócio
│   │       ├── __init__.py
│   │       └── email_service.py      # Serviço de email
│   ├── database/                     # Camada de banco de dados
│   │   ├── models/                   # Modelos SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Modelo base
│   │   │   ├── cart.py               # Modelo de carrinho
│   │   │   ├── order.py              # Modelo de pedido
│   │   │   ├── project_iteration.py # Modelo de iteração
│   │   │   ├── product_spec.py       # Modelo de produto
│   │   │   ├── seller.py             # Modelo de vendedor
│   │   │   └── user.py               # Modelo de usuário
│   │   ├── enums/                     # Enums
│   │   │   ├── __init__.py
│   │   │   ├── iteration_status.py   # Status de iteração
│   │   │   ├── order_status.py       # Status de pedido
│   │   │   ├── seller_category.py    # Categorias de vendedor
│   │   │   └── user_role.py          # Papéis de usuário
│   │   └── session.py                # Sessão do banco de dados
│   ├── storage/                      # Serviço de armazenamento
│   │   ├── __init__.py
│   │   ├── image_service.py          # Serviço de imagens
│   │   └── local_storage.py         # Armazenamento local
│   └── web/                          # Frontend React
│       ├── public/                   # Arquivos estáticos
│       ├── src/
│       │   ├── components/           # Componentes React
│       │   │   ├── CreateOrderModal.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── Toast.tsx
│       │   │   └── Tooltip.tsx
│       │   ├── hooks/                 # Custom hooks
│       │   │   ├── useAuth.ts
│       │   │   ├── useCart.ts
│       │   │   └── useOrders.ts
│       │   ├── lib/                   # Utilitários
│       │   │   ├── api.ts             # Cliente API
│       │   │   └── auth.ts            # Funções de autenticação
│       │   ├── pages/                 # Páginas
│       │   │   ├── Cart.tsx
│       │   │   ├── Login.tsx
│       │   │   ├── MyOrders.tsx
│       │   │   ├── OrderDetail.tsx
│       │   │   ├── Register.tsx
│       │   │   ├── SellerDashboard.tsx
│       │   │   ├── SellerDetail.tsx
│       │   │   └── Sellers.tsx
│       │   ├── types/                 # Tipos TypeScript
│       │   │   └── api.ts
│       │   ├── App.tsx
│       │   ├── index.css
│       │   └── main.tsx
│       ├── index.html
│       ├── package.json
│       ├── tailwind.config.js
│       └── vite.config.ts
├── tests/                            # Testes
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures compartilhadas
│   ├── test_cart_routes.py            # Testes de rotas de carrinho
│   ├── test_database_models.py        # Testes de modelos de banco de dados
│   ├── test_models.py                 # Testes de modelos Pydantic
│   ├── test_orders_routes.py          # Testes de rotas de pedidos
│   ├── test_repositories.py           # Testes de repositories
│   └── test_sellers_routes.py         # Testes de rotas de vendedores
├── .dockerignore
├── .env.example                      # Exemplo de variáveis de ambiente
├── .gitignore
├── alembic.ini                        # Configuração do Alembic
├── docker-compose.yml                 # Compose Docker
├── Dockerfile.api                    # Dockerfile da API
├── Dockerfile.web                    # Dockerfile do Frontend
├── pyproject.toml                    # Configuração do projeto Python
├── pytest.ini                        # Configuração do pytest
├── README.md
└── uv.lock                           # Lock file do uv
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.12 ou superior
- Node.js 18 ou superior
- PostgreSQL 14 ou superior
- Docker e Docker Compose (opcional)

### Backend

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/CraftAI.git
cd CraftAI

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instale as dependências
pip install -e .

# Instale as dependências de teste
pip install -e ".[test]"
```

### Frontend

```bash
cd src/web
npm install
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado em `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/craftai

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@craftai.com
EMAIL_FROM_NAME=CraftAI

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# AWS S3 (opcional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Storage
STORAGE_TYPE=local  # ou 's3'
LOCAL_STORAGE_PATH=./storage/uploads

# Frontend
VITE_API_URL=http://localhost:8000
```

### Banco de Dados

```bash
# Execute as migrations
alembic upgrade head
```

---

## 🏃 Executando Localmente

### Backend

```bash
# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Execute a API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`

### Frontend

```bash
cd src/web
npm run dev
```

O frontend estará disponível em `http://localhost:5173`

### Acessando a Documentação da API

Com o backend rodando, acesse:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🐳 Docker

### Usando Docker Compose

```bash
# Construa e inicie todos os serviços
docker-compose up --build

# Apenas inicie os serviços
docker-compose up

# Pare os serviços
docker-compose down

# Remova volumes e redes
docker-compose down -v
```

Serviços incluídos:

- **api**: Backend FastAPI
- **web**: Frontend React
- **db**: PostgreSQL

---

## 📡 API Endpoints

### Autenticação

- `POST /auth/register` - Registro de usuário
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Obter usuário atual
- `POST /auth/verify-email/{token}` - Verificar email
- `POST /auth/resend-verification` - Reenviar email de verificação
- `POST /auth/forgot-password` - Solicitar recuperação de senha
- `POST /auth/reset-password` - Redefinir senha

### Vendedores

- `POST /sellers/me/profile` - Criar perfil de vendedor
- `GET /sellers/me/profile` - Obter perfil do vendedor
- `PATCH /sellers/me/profile` - Atualizar perfil
- `POST /sellers/me/profile/logo` - Upload de logo
- `POST /sellers/me/profile/banner` - Upload de banner
- `GET /sellers/{id}` - Obter vendedor por ID
- `GET /sellers/by-slug/{slug}` - Obter vendedor por slug
- `GET /sellers/` - Listar vendedores
- `POST /sellers/me/products` - Criar produto
- `GET /sellers/me/products` - Listar produtos do vendedor
- `PATCH /sellers/me/products/{id}` - Atualizar produto
- `DELETE /sellers/me/products/{id}` - Deletar produto
- `POST /sellers/me/products/{id}/cover` - Upload de capa de produto

### Pedidos

- `POST /orders/` - Criar pedido
- `GET /orders/` - Listar pedidos do usuário
- `GET /orders/{id}` - Obter pedido por ID
- `PATCH /orders/{id}` - Atualizar pedido
- `PATCH /orders/{id}/status` - Atualizar status
- `POST /orders/{id}/approve` - Aprovar pedido
- `POST /orders/{id}/reject` - Rejeitar pedido
- `POST /orders/{id}/cancel` - Cancelar pedido
- `POST /orders/{id}/confirm-delivery` - Confirmar entrega
- `POST /orders/{id}/complete` - Completar pedido
- `POST /orders/{id}/iterations` - Criar iteração
- `GET /orders/{id}/iterations` - Listar iterações
- `POST /orders/{id}/iterations/{iteration_id}/approve` - Aprovar iteração

### Carrinho

- `GET /cart` - Obter carrinho
- `POST /cart/items` - Adicionar item ao carrinho
- `PATCH /cart/items/{id}` - Atualizar quantidade
- `DELETE /cart/items/{id}` - Remover item
- `DELETE /cart` - Limpar carrinho
- `POST /cart/checkout` - Checkout
- `GET /cart/total` - Obter total do carrinho

---

## 🧪 Testes

### Executar todos os testes

```bash
pytest
```

### Executar com coverage

```bash
pytest --cov=src/api --cov-report=html --cov-report=term-missing
```

### Executar testes específicos

```bash
# Testes de modelos
pytest tests/test_models.py

# Testes de rotas
pytest tests/test_orders_routes.py

# Testes de repositories
pytest tests/test_repositories.py
```

### Executar com verbose

```bash
pytest -v
```

### Relatório de Coverage

O relatório HTML será gerado em `htmlcov/index.html`

---

## 📦 Deploy

### Backend

#### Heroku

```bash
# Instale o Heroku CLI
heroku create craftai-api

# Defina as variáveis de ambiente
heroku config:set DATABASE_URL=your-database-url
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key

# Deploy
git push heroku main
```

#### Railway/Render

Siga as instruções do provedor para configurar as variáveis de ambiente e fazer o deploy.

### Frontend

#### Vercel/Netlify

1. Conecte seu repositório
2. Configure as variáveis de ambiente
3. Defina o diretório de build como `src/web`
4. Deploy automático

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

## 👥 Autores

- **Eduarda Fernandes Pires**
- **Igor Samuel Candido de Souza**

---

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através das issues do GitHub.

# Shipay Back-end Challenge

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)]()
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-FF2D20?logo=sqlalchemy&logoColor=white)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)]()
[![Alembic](https://img.shields.io/badge/Alembic-006400?logo=alembic&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)]()

API REST desenvolvida como resposta ao desafio técnico back-end da Shipay. Inclui consultas SQL, ORM com SQLAlchemy, endpoints FastAPI, testes automatizados com PostgreSQL e documentação de deploy em produção na AWS.

---

## Pré-requisitos

| Ferramenta                                   | Versão mínima |
| -------------------------------------------- | --------------- |
| Git                                          | 2+              |
| Docker                                       | 24+             |
| Docker Compose                               | 2.24+           |
| Python*(opcional, testes locais sem Docker)* | 3.12+           |

---

## Instalação e execução

### 1. Clonar o repositório

```bash
git clone https://github.com/cicero-lucas/Shipay-Backend-Challenge.git
cd Shipay-Backend-Challenge
```

### 2. Subir o ambiente

```bash
docker compose up --build
```

Isso irá:

1. Subir um container **PostgreSQL 16**
2. Aplicar as migrations via `alembic upgrade head` automaticamente
3. Subir a **API FastAPI** na porta `8000` com roles e claims pré-cadastrados

### 3. Acessar a documentação interativa

```
http://localhost:8000/docs
```

---

## Endpoints

### `GET /roles/{role_id}`

Retorna um papel pelo ID.

```bash
curl http://localhost:8000/roles/1
# {"id": 1, "description": "admin"}
```

### `POST /users/`

Cria um usuário. A senha é opcional — gerada automaticamente se não informada.

```bash
# Sem senha (gerada automaticamente)
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "role_id": 1}'

# Com senha definida manualmente
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Lucas", "email": "lucas@example.com", "role_id": 1, "password": "12345"}'
```

| Campo        | Tipo                    | Obrigatório              |
| ------------ | ----------------------- | ------------------------- |
| `name`     | string                  | ✅                        |
| `email`    | string (e-mail válido) | ✅                        |
| `role_id`  | integer                 | ✅                        |
| `password` | string                  | ❌ gerado automaticamente |

Resposta `201 Created`:

```json
{"id": 1, "name": "Alice", "email": "alice@example.com", "role_id": 1, "password": "abc123..."}
```

### `GET /users/{user_id}`

Retorna os dados de um usuário pelo ID.

```bash
curl http://localhost:8000/users/1
# {"id": 1, "name": "Alice", "email": "alice@example.com", "role_id": 1, "password": "abc123..."}
```

---

## Testes

Os testes rodam contra um banco **PostgreSQL dedicado** (`shipay_test`), garantindo paridade total com o ambiente de produção.

### Via Docker (recomendado)

```bash
docker compose build test && docker compose run --rm test
```

Sobe um PostgreSQL isolado na porta `5433`, cria o schema, executa todos os testes e encerra.

### Localmente (com PostgreSQL rodando)

```bash
cd api
pip install -r requirements.txt
TEST_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/shipay_test pytest -v
```

### Rodando testes específicos

```bash
# Apenas os testes de roles
docker compose run --rm test pytest tests/test_roles.py -v

# Apenas os testes de usuários
docker compose run --rm test pytest tests/test_users.py -v

# Um teste específico
docker compose run --rm test pytest tests/test_users.py::test_create_user_success -v
```

### O que é testado

| Arquivo           | Casos de teste                                                                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_roles.py` | GET role existente (200) · GET role inexistente (404)                                                                                               |
| `test_users.py` | POST com sucesso · POST com senha gerada automaticamente · role inexistente (404) · e-mail inválido (422) · campos obrigatórios ausentes (422) |

### Saída esperada

```
tests/test_roles.py::test_get_role_success                    PASSED
tests/test_roles.py::test_get_role_not_found                  PASSED
tests/test_users.py::test_create_user_success                 PASSED
tests/test_users.py::test_create_user_auto_password           PASSED
tests/test_users.py::test_create_user_invalid_role            PASSED
tests/test_users.py::test_create_user_invalid_email           PASSED
tests/test_users.py::test_create_user_missing_required_fields PASSED

7 passed in 0.60s
```

---

## Estrutura do projeto

```
.
├── database/
│   ├── 1_create_database_ddl.sql           # DDL original de referência
│   └── ER_diagram.png
│
├── sql/
│   ├── questao-01.sql                      # Consulta SQL pura (Q1)
│   └── questao-02.py                       # Consulta SQLAlchemy Expression Language (Q2)
│
├── api/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 0001_initial_schema.py      # DDL das tabelas
│   │   │   └── 0002_seed_initial_data.py   # Roles e claims iniciais
│   │   └── env.py
│   ├── alembic.ini
│   ├── src/
│   │   ├── db/
│   │   │   ├── engine.py                   # create_engine + DATABASE_URL
│   │   │   ├── tables.py                   # Definição das tabelas (SQLAlchemy Core)
│   │   │   ├── base.py                     # Re-exporta engine, metadata e tabelas
│   │   │   └── session.py                  # Dependência Connection para FastAPI
│   │   ├── routers/
│   │   │   ├── roles.py                    # GET /roles/{role_id}
│   │   │   └── users.py                    # POST /users/ · GET /users/{user_id}
│   │   ├── schemas/
│   │   │   └── schemas.py                  # Schemas Pydantic v2
│   │   └── main.py                         # Entrypoint FastAPI
│   ├── tests/
│   │   ├── conftest.py                     # PostgreSQL + fixtures compartilhadas
│   │   ├── test_roles.py                   # Testes do GET /roles/{role_id}
│   │   └── test_users.py                   # Testes do POST /users/
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
│
├── bot/                                    # Código original do robô (Q7)
│   ├── settings/config.ini
│   ├── bot.py
│   └── Pipfile
│
├── docs/
│   ├── questao-05-deploy.md                # Execução local e deploy (Q5)
│   ├── questao-06-bug-analysis.md          # Análise do erro de produção (Q6)
│   ├── questao-07-code-review.md           # Code review do bot (Q7)
│   └── questao-08-design-patterns.md       # Design patterns (Q8)
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Índice de respostas

| # | Tema                                        | Local                                                                                          |
| - | ------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 1 | Consulta SQL                                | [`sql/questao-01.sql`](sql/questao-01.sql)                                                      |
| 2 | ORM — SQLAlchemy Expression Language       | [`sql/questao-02.py`](sql/questao-02.py)                                                        |
| 3 | API REST — GET /roles/{role_id}            | [`api/src/routers/roles.py`](api/src/routers/roles.py)                                          |
| 4 | API REST — POST /users/                    | [`api/src/routers/users.py`](api/src/routers/users.py)                                          |
| 5 | Execução local e deploy produtivo         | [`docs/questao-05-deploy.md`](docs/questao-05-deploy.md)                                        |
| 6 | Análise da falha nos logs de produção    | [`docs/questao-06-bug-analysis.md`](docs/questao-06-bug-analysis.md)                            |
| 7 | Code review do bot                          | [`docs/questao-07-code-review.md`](docs/questao-07-code-review.md) · [`bot/bot.py`](bot/bot.py) |
| 8 | Design patterns para serviços de terceiros | [`docs/questao-08-design-patterns.md`](docs/questao-08-design-patterns.md)                      |

---

## Decisões técnicas

### Migrations com Alembic

O schema é versionado via **Alembic**, executado automaticamente no startup do container antes da API subir.

| Migration                     | Conteúdo                                   |
| ----------------------------- | ------------------------------------------- |
| `0001_initial_schema.py`    | DDL original fornecido pela Shipay          |
| `0002_seed_initial_data.py` | Roles e claims iniciais para demonstração |

Comandos úteis:

```bash
cd api

# Aplicar todas as migrations
alembic upgrade head

# Reverter a última migration
alembic downgrade -1

# Ver histórico
alembic history
```

O Alembic não era obrigatório para o desafio — o schema é fixo. Foi adicionado por ser o padrão de mercado em projetos FastAPI + SQLAlchemy, tornando o schema auditável, reversível e pronto para evoluir sem `DROP/CREATE`.

### Testes com PostgreSQL

Os testes utilizam um banco PostgreSQL dedicado em vez de SQLite, garantindo que constraints, tipos de dados e comportamento de autoincrement sejam idênticos ao ambiente de produção.

### Pydantic v2

Os schemas utilizam `ConfigDict` em vez do `class Config` depreciado, seguindo as boas práticas do Pydantic v2.

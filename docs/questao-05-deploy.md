# Questão 05 — Execução Local e Deploy em Produção

## Pré-requisitos

| Ferramenta                                   | Versão mínima |
| -------------------------------------------- | --------------- |
| Docker                                       | 24+             |
| Docker Compose                               | 2.24+           |
| Python*(opcional, testes locais sem Docker)* | 3.12+           |

---

## Execução Local

### 1. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/shipay-challenge.git
cd shipay-challenge
```

### 2. Subir o ambiente com Docker Compose

```bash
docker compose up --build
```

O Compose irá:

1. Subir um container **PostgreSQL 16** e aplicar o DDL automaticamente via `docker-entrypoint-initdb.d`.
2. Aguardar o banco ficar saudável (*healthcheck*).
3. Subir a **API FastAPI** na porta `8000`.

### 3. Verificar a API

```bash
# Health check
curl http://localhost:8000/health

# Documentação interativa (Swagger UI)
http://localhost:8000/docs
```

### 4. Rodar os testes

Os testes usam **SQLite em memória** — não é necessário o banco Postgres rodando.

```bash
cd api
pip install -r requirements.txt
pytest tests/ -v
```

---

## Deploy em Produção

### Estratégia recomendada: AWS ECS (Fargate) + RDS PostgreSQL

<img src="img/arquitetura_aws.png" alt="Arquitetura AWS" width="600">

| Serviço | Função |
| ------- | ------ |
| **CloudFront** | CDN opcional na borda — reduz latência para usuários distantes e absorve picos de tráfego antes de chegar ao ALB |
| **Application Load Balancer (ALB)** | Distribui as requisições HTTPS entre as tasks Fargate, faz health check e termina o TLS |
| **ECS Fargate** | Executa os containers da API sem necessidade de gerenciar servidores — escala horizontalmente adicionando tasks |
| **RDS PostgreSQL Multi-AZ** | Banco gerenciado com failover automático para uma réplica em outra zona de disponibilidade, garantindo alta disponibilidade |

### Passo a passo

#### 1. Build e push da imagem Docker

```bash
# Autenticar no ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com

# Build e push
docker build -t shipay-api ./api
docker tag shipay-api:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/shipay-api:latest
docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/shipay-api:latest
```

#### 2. Variáveis de ambiente sensíveis

Armazene no **AWS Secrets Manager** ou **Parameter Store** e injete na task definition do ECS:

```json
{
  "secrets": [
    {
      "name": "DATABASE_URL",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:<account_id>:secret:shipay/db-url"
    }
  ]
}
```

#### 3. Pipeline CI/CD sugerido (GitHub Actions)

```yaml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r api/requirements.txt
      - run: pytest api/tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: |
          docker build -t shipay-api ./api
          docker tag shipay-api:latest <ecr_uri>:latest
          docker push <ecr_uri>:latest
          aws ecs update-service --cluster shipay --service api --force-new-deployment
```

#### 4. Migrações de banco em produção

Execute as migrações **antes** de atualizar o serviço, usando um ECS Task de inicialização separado ou via pipeline CI/CD, garantindo *zero downtime*.

---

## Variáveis de Ambiente

| Variável        | Descrição                  | Padrão (local)                                            |
| ---------------- | ---------------------------- | ---------------------------------------------------------- |
| `DATABASE_URL` | Connection string PostgreSQL | `postgresql+psycopg2://postgres:postgres@db:5432/shipay` |

---

## Infraestrutura como Código (Terraform)

Alternativa ao passo a passo manual acima. O Terraform provisiona toda a infraestrutura AWS de forma declarativa, versionada e reproduzível.

### Estrutura sugerida

```
infra/
├── main.tf        # Provider e configurações globais
├── variables.tf   # Variáveis de entrada
├── outputs.tf     # Outputs (URL do ALB, endpoint do RDS, etc.)
├── ecr.tf         # Repositório de imagens
├── ecs.tf         # Cluster, Task Definition e Service Fargate
├── rds.tf         # Instância PostgreSQL
├── network.tf     # VPC, subnets, security groups
└── secrets.tf     # Secrets Manager para DATABASE_URL
```

### Exemplo dos recursos principais

**`ecr.tf`** — repositório da imagem:

```hcl
resource "aws_ecr_repository" "api" {
  name                 = "shipay-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
```

**`rds.tf`** — banco PostgreSQL gerenciado:

```hcl
resource "aws_db_instance" "postgres" {
  identifier        = "shipay-db"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "shipay"
  username          = "postgres"
  password          = var.db_password
  multi_az          = true
  skip_final_snapshot = false

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}
```

**`ecs.tf`** — serviço Fargate:

```hcl
resource "aws_ecs_service" "api" {
  name            = "shipay-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
}
```

**`secrets.tf`** — credenciais sem hardcode:

```hcl
resource "aws_secretsmanager_secret" "db_url" {
  name = "shipay/database-url"
}

resource "aws_secretsmanager_secret_version" "db_url" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+psycopg2://${var.db_user}:${var.db_password}@${aws_db_instance.postgres.endpoint}/shipay"
}
```

### Comandos de deploy

```bash
cd infra

# Inicializar providers
terraform init

# Visualizar o plano antes de aplicar
terraform plan -var="db_password=<senha>"

# Provisionar a infraestrutura
terraform apply -var="db_password=<senha>"

# Destruir ambiente (ex.: homologação)
terraform destroy
```

### Por que Terraform?

| Benefício        | Descrição                                                           |
| ----------------- | --------------------------------------------------------------------- |
| Versionamento     | Infraestrutura revisada em pull requests como qualquer código        |
| Reproduzibilidade | Mesmo comando cria ambientes idênticos (dev, homolog, prod)          |
| Rastreabilidade   | `terraform plan` mostra exatamente o que vai mudar antes de aplicar |
| Rollback          | Revertir infraestrutura é reverter o código no git                  |

---

### Pipeline CI/CD para o Terraform (GitHub Actions)

O Terraform também deve ser executado via pipeline — nunca manualmente em produção. A estratégia usa dois fluxos distintos: **PR** (plan) e **merge na main** (apply).

```
Pull Request  →  terraform plan   (só mostra o que vai mudar, não aplica)
Merge na main →  terraform apply  (aplica após aprovação humana)
```

Crie o arquivo `.github/workflows/terraform.yml`:

```yaml
name: Terraform

on:
  pull_request:
    paths:
      - 'infra/**'
  push:
    branches:
      - main
    paths:
      - 'infra/**'

env:
  TF_VERSION: 1.8.0
  AWS_REGION: us-east-1

jobs:
  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    defaults:
      run:
        working-directory: infra/

    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - run: terraform init
      - run: terraform validate
      - run: terraform fmt --check

      - name: Terraform Plan
        run: terraform plan -var="db_password=${{ secrets.DB_PASSWORD }}" -out=tfplan

      - name: Publica o plano no PR
        uses: actions/github-script@v7
        with:
          script: |
            const output = `#### Terraform Plan
            \`\`\`
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            `
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })

  apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production        # exige aprovação manual no GitHub
    defaults:
      run:
        working-directory: infra/

    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - run: terraform init
      - run: terraform apply -auto-approve -var="db_password=${{ secrets.DB_PASSWORD }}"
```

#### Secrets necessários no repositório GitHub

| Secret                    | Descrição                                  |
| ------------------------- | -------------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | Chave de acesso IAM com permissões de infra |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta IAM                            |
| `DB_PASSWORD`           | Senha do banco RDS                           |

#### Boas práticas aplicadas no pipeline

- **`terraform fmt --check`** — rejeita o PR se o código não estiver formatado
- **`terraform validate`** — valida a sintaxe antes de qualquer operação
- **Plan publicado no PR** — o revisor vê exatamente o que vai mudar na infra antes de aprovar
- **`environment: production`** — exige aprovação manual no GitHub antes do apply em produção
- **`paths: infra/**`** — o pipeline só dispara quando arquivos de infra mudam, não em todo push
- **State remoto** — em produção o `terraform.tfstate` deve ser armazenado em S3 com lock via DynamoDB, nunca local:

```hcl
# infra/main.tf
terraform {
  backend "s3" {
    bucket         = "shipay-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "shipay-terraform-lock"
  }
}
```

---

## Estimativa de Custos (AWS Pricing Calculator)

> Estimativa gerada para a região **us-east-1 (N. Virginia)**.
> Simulações detalhadas podem ser geradas em: https://calculator.aws

### Recursos e configurações consideradas

| Serviço        | Configuração                              | Justificativa                                         |
| --------------- | ------------------------------------------- | ----------------------------------------------------- |
| ECS Fargate     | 2 tasks × 0.25 vCPU × 0.5 GB RAM, 24h/dia | Mínimo para alta disponibilidade (2 AZs)             |
| RDS PostgreSQL  | `db.t3.micro`, 20 GB SSD, Multi-AZ        | Menor instância gerenciada com failover automático  |
| ALB             | 1 load balancer + 10 GB processados/mês    | Distribui tráfego entre as 2 tasks Fargate           |
| ECR             | 1 GB armazenado                             | Armazenamento da imagem Docker da API                 |
| Secrets Manager | 1 secret + 10.000 requisições/mês        | `DATABASE_URL` armazenado com rotação automática |
| S3 + DynamoDB   | State Terraform (uso mínimo)               | Backend remoto para Terraform                         |

### Estimativa mensal

| Serviço                        | Custo estimado/mês (USD) |
| ------------------------------- | ------------------------- |
| ECS Fargate (2 tasks)           | ~ $14,00                  |
| RDS PostgreSQL Multi-AZ         | ~ $48,00                  |
| Application Load Balancer       | ~ $18,00                  |
| ECR                             | ~ $0,10                   |
| Secrets Manager                 | ~ $0,40                   |
| S3 + DynamoDB (Terraform state) | ~ $0,50                   |
| **Total estimado**        | **~ $81,00 / mês** |

### Como reduzir custos em homologação

| Ação                                                                        | Economia estimada    |
| ----------------------------------------------------------------------------- | -------------------- |
| RDS sem Multi-AZ em homolog                                                   | - $24,00/mês        |
| 1 task Fargate em vez de 2                                                    | - $7,00/mês         |
| Desligar ambiente fora do horário comercial (`terraform destroy` agendado) | - 60% do custo total |

> Para simular cenários específicos de tráfego, instâncias maiores ou outras regiões, acesse:
> **https://calculator.aws**

---

## Alternativa: Google Cloud Platform (GCP)

A mesma estratégia pode ser aplicada no GCP com serviços equivalentes:

| AWS | GCP | Função |
| --- | --- | ------ |
| CloudFront | Cloud CDN | CDN na borda |
| Application Load Balancer | Cloud Load Balancing | Distribuição de tráfego e terminação TLS |
| ECS Fargate | Cloud Run | Execução de containers sem gerenciar servidores |
| RDS PostgreSQL Multi-AZ | Cloud SQL PostgreSQL (HA) | Banco gerenciado com failover automático |
| ECR | Artifact Registry | Repositório de imagens Docker |
| Secrets Manager | Secret Manager | Armazenamento de credenciais |
| S3 + DynamoDB | GCS + Firestore | Backend remoto para Terraform |

### Passo a passo no GCP

#### 1. Build e push da imagem

```bash
# Autenticar no Artifact Registry
gcloud auth configure-docker <region>-docker.pkg.dev

# Build e push
docker build -t shipay-api ./api
docker tag shipay-api:latest <region>-docker.pkg.dev/<project_id>/shipay/shipay-api:latest
docker push <region>-docker.pkg.dev/<project_id>/shipay/shipay-api:latest
```

#### 2. Variáveis de ambiente sensíveis

Armazene no **Secret Manager** e referencie no deploy do Cloud Run:

```bash
gcloud secrets create database-url --data-file=- <<< "postgresql+psycopg2://..."
```

#### 3. Deploy no Cloud Run

```bash
gcloud run deploy shipay-api \
  --image <region>-docker.pkg.dev/<project_id>/shipay/shipay-api:latest \
  --region us-central1 \
  --set-secrets DATABASE_URL=database-url:latest \
  --allow-unauthenticated
```

#### 4. Pipeline CI/CD (GitHub Actions)

```yaml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r api/requirements.txt
      - run: pytest api/tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_CREDENTIALS }}
      - uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: shipay-api
          image: <region>-docker.pkg.dev/<project_id>/shipay/shipay-api:latest
          region: us-central1
```

### Por que Cloud Run em vez de GKE?

O **Cloud Run** é o equivalente mais próximo do ECS Fargate — serverless, escala para zero quando não há tráfego e não exige gerenciamento de cluster. O **GKE Autopilot** seria a escolha para workloads mais complexos que exijam controle fino de rede ou múltiplos serviços.

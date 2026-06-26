# Questão 06 — Análise do Erro em Produção/Homologação

## Log relevante

```
[2020-07-06 20:34:49,723: ERROR/ForkPoolWorker-1]
Task tasks.wallet_oauth.renew_wallet_x_access_tokens[ee561a2e-...]
raised unexpected: AttributeError("module 'core.settings' has no attribute 'WALLET_X_TOKEN_MAX_AGE'")

File "/opt/worker/src/tasks/wallet_oauth.py", line 15, in renew_wallet_x_access_tokens
    expire_at = now - settings.WALLET_X_TOKEN_MAX_AGE
AttributeError: module 'core.settings' has no attribute 'WALLET_X_TOKEN_MAX_AGE'
```

---

## Causa Raiz

O atributo `WALLET_X_TOKEN_MAX_AGE` **não está definido no módulo `core.settings`** do ambiente de Homologação/Produção.

O erro **não ocorre localmente** porque o arquivo de configurações local provavelmente define essa variável, enquanto o ambiente de não-desenvolvimento utiliza um arquivo de settings diferente, ou depende de **variáveis de ambiente** que não foram provisionadas.

As causas mais prováveis, em ordem de probabilidade:

### 1. Variável de ambiente não configurada no ambiente (mais provável)

Em ambientes de container (Kubernetes, ECS), as configurações são injetadas como variáveis de ambiente. Se `WALLET_X_TOKEN_MAX_AGE` é lida via `os.environ` dentro de `core.settings`, basta não ter sido adicionada ao manifesto/secret do ambiente:

```python
# core/settings.py — leitura que falha silenciosamente se a var não existe
WALLET_X_TOKEN_MAX_AGE = os.environ.get("WALLET_X_TOKEN_MAX_AGE")  # retorna None
# ou pior — lança KeyError se usar os.environ["WALLET_X_TOKEN_MAX_AGE"]
```

### 2. Arquivo de settings separado por ambiente

O projeto pode ter `settings/local.py`, `settings/production.py`. A variável foi adicionada apenas em `local.py` e esquecida nos demais.

### 3. Deploy desatualizado (imagem antiga em uso)

A task `renew_wallet_x_access_tokens` é nova e referencia `WALLET_X_TOKEN_MAX_AGE`, mas o módulo `core.settings` deployado ainda é uma versão anterior que não contém o atributo — indicando que o deploy do worker e do módulo de settings não foram feitos de forma atômica/sincronizada.

---

## Como Corrigir

1. **Verificar as variáveis de ambiente** do Pod/Container do worker:

   ```bash
   kubectl exec -it <pod-name> -- env | grep WALLET
   # ou
   kubectl describe pod <pod-name>
   ```
2. **Adicionar a variável ausente** no ConfigMap, Secret ou manifesto de deploy:

   ```yaml
   env:
     - name: WALLET_X_TOKEN_MAX_AGE
       value: "3600"
   ```
3. **Adicionar validação explícita** em `core/settings.py` para falhar rápido (fail-fast) na inicialização:

   ```python
   import os

   WALLET_X_TOKEN_MAX_AGE = int(os.environ["WALLET_X_TOKEN_MAX_AGE"])  # KeyError claro na startup
   ```

   Dessa forma o container falha ao iniciar — antes de aceitar tarefas — em vez de falhar silenciosamente durante a execução.
4. **Sincronizar deploys**: garantir que settings e worker sejam deployados juntos na mesma pipeline.

---

## Observação adicional nos logs

```
[2020-07-66 20:34:49,801: INFO/ForkPoolWorker-2] [expire_orders]
```

A data `2020-07-**66**` é inválida — indica um possível problema de formatação/corrupção no sistema de logging do ambiente, o que pode dificultar a rastreabilidade de outros erros. Vale investigar a configuração do formatter do logger.

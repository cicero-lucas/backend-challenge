# Questão 07 — Code Review: `bot/bot.py`

Revisão do robô de exportação de dados da tabela `users`.
Os problemas encontrados estão categorizados por tipo e severidade.

---

## Resumo dos Problemas

| ID    | Severidade         | Categoria      | Descrição resumida                                                          |
| ----- | ------------------ | -------------- | ----------------------------------------------------------------------------- |
| CR-01 | Baixa              | Código morto  | Imports não utilizados (`traceback`, `timedelta`, `timezone`)          |
| CR-02 | Baixa              | Estilo         | Múltiplos imports em uma linha (viola PEP 8)                                 |
| CR-03 | Média             | Arquitetura    | Flask desnecessário em um worker/robô                                       |
| CR-04 | **Alta**     | Segurança     | Credencial de banco hardcoded no código                                      |
| CR-05 | Média             | Portabilidade  | Caminho absoluto hardcoded para o config                                      |
| CR-06 | Baixa              | Boas práticas | Uso de`print` em vez de `logging`                                         |
| CR-07 | **Alta**     | Bug            | Job nunca é agendado — função chamada em vez de referenciada              |
| CR-08 | Baixa              | Código morto  | Variável`task1_instance` atribuída e nunca utilizada                      |
| CR-09 | **Alta**     | Robustez       | Ausência de tratamento de exceções em`task1`                             |
| CR-10 | Média             | Boas práticas | SQL raw sem uso de ORM ou queries parametrizadas                              |
| CR-11 | **Crítico** | Segurança     | Senha dos usuários exportada para planilha e impressa no stdout              |
| CR-12 | Baixa              | Estilo         | `index = index + 1` em vez de `index += 1`                                |
| CR-13 | Média             | Performance    | `print` por linha em loop — polui stdout em larga escala                   |
| CR-14 | Média             | Robustez       | `workbook.close()` fora de `try/finally` — arquivo pode ficar corrompido |

---

## Detalhamento

### CR-01 — Imports não utilizados

`traceback`, `timedelta` e `timezone` são importados mas não utilizados em nenhuma parte do código. Além de poluir o namespace, podem causar confusão sobre a intenção do código.

---

### CR-02 — Múltiplos imports em uma linha

```python
# Atual
import os, sys, traceback, logging, configparser

# Correto (PEP 8)
import os
import sys
import logging
import configparser
```

---

### CR-03 — Flask desnecessário

O robô utiliza `Flask` e `flask_sqlalchemy` exclusivamente para obter uma instância do SQLAlchemy e o sistema de logging. Um worker/scheduler não precisa de um servidor web. O correto é usar `SQLAlchemy` standalone e o módulo `logging` nativo do Python.

---

### CR-04 — Credencial hardcoded ⚠️

```python
# ❌ Credencial exposta no código-fonte
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:123mudar@127.0.0.1:5432/bot_db'

# ✅ Ler de variável de ambiente
import os
DATABASE_URL = os.environ["DATABASE_URL"]
```

Credenciais no código-fonte são expostas em repositórios, logs e histórico do git. Utilizar variáveis de ambiente ou um gerenciador de segredos (AWS Secrets Manager, HashiCorp Vault).

---

### CR-05 — Caminho absoluto hardcoded

```python
# ❌ Não funciona fora de /tmp/bot/
config.read('/tmp/bot/settings/config.ini')

# ✅ Relativo ao diretório do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(BASE_DIR, 'settings', 'config.ini'))
```

---

### CR-06 — `print` em vez de `logging`

Mensagens de diagnóstico devem usar o módulo `logging` com níveis apropriados (`DEBUG`, `INFO`, `WARNING`). O uso de `print` não permite controle de nível, formatação padronizada ou envio para sistemas externos (CloudWatch, Datadog, etc.).

---

### CR-07 — Bug crítico: job nunca agendado ⚠️

```python
# ❌ task1(db) EXECUTA a função agora e registra o retorno (None) como callable
scheduler.add_job(task1(db), 'interval', id='task1_job', minutes=var1)

# ✅ Passa a referência da função e os argumentos separadamente
scheduler.add_job(task1, 'interval', args=[db], id='task1_job', minutes=var1)
```

Esse bug faz o job rodar uma única vez na inicialização e nunca mais ser agendado.

---

### CR-09 — Ausência de tratamento de exceções

Se ocorrer qualquer erro durante a exportação (timeout de banco, disco cheio, linha inválida), o job falha silenciosamente sem notificar, sem retry e sem liberar o arquivo Excel. O scheduler pode entrar em estado inconsistente.

---

### CR-11 — Exportação da senha dos usuários ⚠️ CRÍTICO

```python
# ❌ Exporta e imprime a senha de cada usuário
worksheet.write('D{}'.format(index), order[3])  # coluna 'password'
print('Password: {}'.format(order[3]))
```

Esta é a falha mais grave. Senhas **nunca** devem ser exportadas, independentemente de estarem hasheadas. O `SELECT *` deve ser substituído por uma query que selecione explicitamente apenas as colunas não-sensíveis necessárias.

---

### CR-08 — Variável `task1_instance` não utilizada

```python
# ❌ Atribuída mas nunca referenciada
task1_instance = scheduler.add_job(...)
```

O retorno de `add_job` é armazenado em `task1_instance`, mas a variável nunca é usada para pausar, cancelar ou inspecionar o job. Pode ser removida sem impacto.

---

### CR-10 — SQL raw sem queries parametrizadas

```python
# ❌ Query sem parâmetros explícitos
orders = db.engine.execute("SELECT * FROM users")
```

Além de expor colunas sensíveis (ver CR-11), o uso de SQL raw sem parametrização abre espaço para SQL injection caso filtros dinâmicos sejam adicionados futuramente. O correto é usar o ORM ou `text()` com parâmetros vinculados:

```python
# ✅ Usando SQLAlchemy text com parâmetros
from sqlalchemy import text
result = conn.execute(text("SELECT id, name, email FROM users WHERE active = :active"), {"active": True})
```

---

### CR-12 — Incremento de índice não idiomático

```python
# ❌
index = index + 1

# ✅
index += 1
```

Pequena questão de estilo, mas o operador `+=` é o padrão Python e melhora a legibilidade.

---

### CR-13 — `print` por linha dentro de loop

```python
# ❌ Um print por linha de usuário
for order in orders:
    print('Name: {}'.format(order[1]))
    print('Password: {}'.format(order[3]))
```

Em tabelas com muitos registros, isso polui completamente o stdout e degrada a performance. O ideal é logar apenas um resumo ao final (`logging.info("%d registros exportados", total)`) e nunca logar dados sensíveis.

---

### CR-14 — `workbook.close()` sem `try/finally`

```python
# ❌ Se uma exceção ocorrer no loop, o arquivo fica aberto/corrompido
for order in orders:
    ...
workbook.close()

# ✅ Garantir fechamento sempre
try:
    for order in orders:
        ...
finally:
    workbook.close()
```

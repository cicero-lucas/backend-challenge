# Questão 08 — Design Patterns para Normalização de Serviços de Terceiros

## Contexto

Precisamos integrar múltiplos provedores externos com interfaces distintas (ex.: SendGrid, Amazon SES, Mailgun para e-mail; Twilio, Zenvia, AWS SNS para SMS) e expô-los de forma uniforme para o restante da aplicação.

---

## Padrões Recomendados

### 1. Strategy Pattern (principal)

O **Strategy** é o padrão central para este problema. Define uma **interface comum** (contrato) para uma família de algoritmos/serviços intercambiáveis, permitindo trocar a implementação em tempo de execução sem alterar o código cliente.

```
«interface»
EmailProvider
──────────────
+ send(to, subject, body) → void

SendGridProvider          SESProvider           MailgunProvider
─────────────────         ───────────           ───────────────
+ send(...)               + send(...)            + send(...)
  └─ chama API SendGrid     └─ chama AWS SES       └─ chama API Mailgun
```

**Por que Strategy?**

- Cada provedor é uma estratégia concreta que implementa o mesmo contrato.
- O código cliente (`NotificationService`) depende apenas da interface — nunca de uma implementação específica.
- Adicionar um novo provedor exige apenas criar uma nova classe; nenhum código existente é alterado (**Open/Closed Principle**).
- Permite troca de provedor por configuração (variável de ambiente, feature flag) sem recompilar/redesployar a lógica de negócio.

---

### 2. Adapter Pattern (complementar)

Quando um provedor externo tem uma interface muito diferente do nosso contrato (ex.: SDK com assinatura de método incompatível), o **Adapter** envolve o SDK e traduz a chamada para o formato esperado pela interface comum.

```
EmailProvider (interface)
       ▲
       │ implementa
SendGridAdapter
  └─ internamente usa sendgrid.SendGridAPIClient().send(...)
```

**Por que Adapter?**

- Isola completamente o código da aplicação das particularidades de cada SDK.
- Se o SDK mudar de versão e quebrar a interface, só o Adapter precisa ser atualizado.
- Funciona em conjunto com o Strategy: cada Strategy *pode ser* um Adapter.

---

### 3. Factory Pattern (suporte)

Uma **Factory** (ou **Factory Method**) é usada para instanciar o provedor correto com base em configuração, sem expor a lógica de criação ao código cliente.

```python
# Exemplo conceitual
def email_provider_factory(provider_name: str) -> EmailProvider:
    providers = {
        "sendgrid": SendGridAdapter,
        "ses":      SESAdapter,
        "mailgun":  MailgunAdapter,
    }
    return providers[provider_name]()
```

**Por que Factory?**

- Centraliza a lógica de seleção do provedor em um único lugar.
- O código cliente não precisa conhecer as classes concretas.
- Facilita testes: basta configurar `provider_name = "mock"` para usar um provedor fake.

---

## Combinação dos Padrões

```Shell
Configuração (env var)
        │
        ▼
  ProviderFactory  ──cria──▶  SendGridAdapter  ──implementa──▶  EmailProvider (Strategy)
                              SESAdapter                              ▲
                              MailgunAdapter                          │
                                                               NotificationService
                                                               (depende apenas da interface)
```

O **Strategy** define o contrato, o **Adapter** traduz SDKs incompatíveis, e a **Factory** resolve qual implementação usar — os três trabalham juntos de forma natural e são amplamente reconhecidos pela indústria para este tipo de integração.

---

## Benefícios consolidados

| Benefício                                         | Strategy | Adapter | Factory |
| -------------------------------------------------- | :------: | :-----: | :-----: |
| Troca de provedor sem alterar código de negócio  |    ✅    |        |   ✅   |
| Isolamento de SDKs de terceiros                    |          |   ✅   |        |
| Testabilidade (mock/stub fácil)                   |    ✅    |   ✅   |   ✅   |
| Adição de novo provedor sem modificar existentes |    ✅    |   ✅   |   ✅   |
| Centralização da lógica de seleção            |          |        |   ✅   |

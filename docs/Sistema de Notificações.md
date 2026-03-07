# Sistema de Notificações

[[Índice|← Índice]]

---

## Visão Geral

O sistema envia **emails de lembrete** automaticamente quando um vencimento se aproxima. Usa Celery com Redis como broker — o email é enviado de forma assíncrona via SMTP.

```
Celery Beat (09h, São Paulo)
    └─ checar_vencimentos_e_notificar()
         ├─ Query: rateios PENDENTE com vencimento em até 3 dias
         └─ Para cada um: enfileira disparar_email_lembrete()
                              └─ send_email_sync() → aiosmtplib → SMTP
```

---

## Celery

**Configuração** (`app/celery_app.py`):

```python
celery_app = Celery(
    "gestor_custos",
    broker=settings.REDIS_URL,       # redis://redis:6379/0
    backend=settings.REDIS_URL,
    include=["app.notificacao.tasks"],
)
```

| Configuração | Valor |
|-------------|-------|
| Serializer | JSON |
| Timezone | America/Sao_Paulo |
| Task time limit | 300s (5 min) |
| Worker prefetch | 1 (processa uma task por vez) |

**Beat Schedule:**

```python
"checar-vencimentos-diariamente": {
    "task": "app.notificacao.tasks.checar_vencimentos_e_notificar",
    "schedule": crontab(hour=9, minute=0),  # todo dia às 09:00
}
```

---

## Tarefas

### `checar_vencimentos_e_notificar`

Executa diariamente às 09h. Busca todos os pagamentos próximos de vencer e enfileira um email para cada um.

**Query executada:**
```sql
SELECT PagamentoRateio, Custo, Usuario
FROM pagamento_rateio
JOIN custo ON custo.id = pagamento_rateio.custo_id
JOIN usuario ON usuario.id = pagamento_rateio.usuario_id
WHERE pagamento_rateio.status = 'PENDENTE'
  AND custo.status = 'PENDENTE'
  AND custo.data_vencimento >= HOJE
  AND custo.data_vencimento <= HOJE + 3 dias
```

**Retorno:**
```python
{
    "notificacoes_encontradas": 5,
    "enviados": 5,
    "erros": 0,
}
```

**Configuração:** `DAYS_BEFORE_DUE_NOTIFICATION` (default: 3 dias) definido em `.env`.

---

### `disparar_email_lembrete`

Envia um email de lembrete para um usuário específico sobre um pagamento pendente.

**Parâmetros** (todos strings — serialização JSON do Celery):

| Param | Exemplo |
|-------|---------|
| `email` | `"joao@email.com"` |
| `nome` | `"João Silva"` |
| `valor` | `"R$ 480,00"` |
| `descricao` | `"Aluguel"` |
| `vencimento` | `"05/03/2026"` |

**Assunto:** `"Lembrete: Pagamento pendente - Aluguel"`

**Corpo:** HTML + texto plano.

---

## Email Service

**Arquivo:** `app/notificacao/email_service.py`

### `send_email_async` (para uso direto)

```python
async def send_email_async(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    # Monta MIMEMultipart com HTML + texto
    # Envia via aiosmtplib (async)
    # Retorna True/False
```

### `send_email_sync` (wrapper para Celery)

```python
def send_email_sync(...) -> bool:
    # asyncio.run(send_email_async(...))
    # Celery tasks são síncronas, mas o email é assíncrono
```

**Configurações SMTP** (`.env`):
```env
SMTP_HOST=mailpit        # "mailpit" em dev, host real em prod
SMTP_PORT=1025
SMTP_FROM_EMAIL=noreply@gestorcustos.local
```

---

## Mailpit (Ambiente de Desenvolvimento)

Mailpit é um servidor SMTP fake — captura todos os emails enviados sem entregá-los de verdade.

| Serviço | URL |
|---------|-----|
| SMTP | `mailpit:1025` |
| Interface Web | `http://localhost:8025` |

Acesse `http://localhost:8025` para ver todos os emails capturados durante o desenvolvimento.

---

## Containers Celery

Ver [[Arquitetura de Containers]] para detalhes dos serviços Docker.

```yaml
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info

celery-beat:
  command: celery -A app.celery_app beat --loglevel=info
```

**Logs:**
```bash
task celery-logs
```

---

Ver também: [[Arquitetura de Containers]] | [[Ambiente de Desenvolvimento]]

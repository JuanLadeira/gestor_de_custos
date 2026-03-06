# Pendências e Issues

[[Índice|← Índice]]

---

## Bugs Conhecidos

### Typo em `auth/schemas.py`

**Arquivo:** `app/auth/schemas.py`

```python
class Token(BaseModel):
    acess_token: str   # ❌ faltando "c": acess → access
    token_type: str
```

**Impacto:** Clientes que esperam `access_token` no padrão OAuth2 receberão um campo diferente.
**Fix:** Renomear `acess_token` → `access_token` (breaking change — atualizar frontend junto).

---

## Migrations Desatualizadas

**Arquivo:** `alembic/versions/404af90b75eb_recuperando_migrations.py`

A migration atual referencia tabelas antigas (`user`, `todo`) que não existem mais no projeto. O schema real tem tabelas diferentes.

**Solução:**
```bash
# Dentro do container
task bash
# Deletar a migration antiga
rm alembic/versions/404af90b75eb_*.py
# Gerar nova migration a partir dos models atuais
task revision -m "Create initial schema"
task head
```

---

## Frontend Incompleto

As views existem mas estão na estrutura básica. Falta implementar:

| Funcionalidade | Prioridade |
|---------------|-----------|
| Formulário de criação de custo | Alta |
| Modal de distribuição de rateio (com barra de progresso ≤ 100%) | Alta |
| Gestão de Meses (abrir mês, fechar mês) | Alta |
| Listagem e criação de Tenants | Média |
| Gestão de Usuários | Média |
| Dashboard com resumo mensal | Média |
| Feedback de erros na UI | Alta |
| Design responsivo | Média |
| Estado de loading nas requisições | Média |

---

## Melhorias de Segurança

### Multi-tenancy não enforçado na API

Atualmente qualquer usuário autenticado pode acessar dados de qualquer tenant. A regra de negócio de isolamento (`usuario.tenant_id == recurso.tenant_id`) não está sendo validada nos endpoints.

**Solução sugerida:** Criar um middleware ou dependência que filtra automaticamente por `tenant_id` do `current_user`.

### Sem controle de papéis (roles)

Não há distinção entre admin e usuário comum — todos têm os mesmos poderes.

---

## Melhorias de Produto

| Item | Descrição |
|------|-----------|
| Fechamento de mês | Endpoint para marcar `MesReferencia.status = FECHADO` e impedir edições |
| Relatório mensal | Endpoint que retorna resumo total por usuário no mês |
| Histórico de pagamentos | Endpoint para listar pagamentos de um usuário ao longo dos meses |
| Re-importação seletiva | Importar apenas custos fixos novos (não todos) quando mês já tem dados |
| Dashboard de totais | Quanto cada usuário deve pagar no mês atual |
| Notificação de 100% rateado | Avisar quando todos os custos do mês estão completamente rateados |

---

## Documentação

| Item | Status |
|------|--------|
| README.md | Desatualizado — ainda referencia projeto To-Do |
| Swagger UI | Automático via FastAPI — disponível em `/docs` |
| Esta documentação Obsidian | Criada em 2026-03-04 |

---

## Issues Resolvidos

### Obsidian CLI no WSL2

**Problema:** `obsidian` (snap) saía com exit code 1 sem output visível.

**Causa:** MESA/GPU error (`ZINK: failed to choose pdev`) dentro do sandbox snap impedia o Electron de criar janela. O snap também bloqueava flags como `--disable-gpu`.

**Solução:** Instalar via `.deb` oficial (sem sandbox restritivo):
```bash
wget https://github.com/obsidianmd/obsidian-releases/releases/download/v1.12.4/obsidian_1.12.4_amd64.deb -O /tmp/obsidian.deb
sudo snap remove obsidian
sudo dpkg -i /tmp/obsidian.deb
sudo apt-get install -f -y
```

---

Ver também: [[Visão Geral]] | [[Frontend]] | [[Módulos da API]]

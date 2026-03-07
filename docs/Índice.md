# Gestor de Custos Compartilhados — Índice

Sistema web assíncrono para gestão de despesas compartilhadas entre grupos (repúblicas, casas, famílias). FastAPI + Vue.js + PostgreSQL + Celery.

---

## Notas de Arquitetura

| Nota | Descrição |
|------|-----------|
| [[Visão Geral]] | Objetivo do sistema, stack tecnológica e fluxo de uso |
| [[Modelos de Dados]] | Entidades, campos, relacionamentos e diagramas |
| [[Regras de Negócio]] | Validação de rateio (100%), criação automática de meses, fluxos principais |
| [[Autenticação]] | JWT, hashing de senha, fluxo de login, dependências do FastAPI |
| [[Módulos da API]] | Todos os endpoints REST organizados por domínio |
| [[Sistema de Notificações]] | Celery, tarefas agendadas, envio de emails |
| [[Frontend]] | Vue.js 3, Pinia, roteamento, cliente HTTP |
| [[Arquitetura de Containers]] | Docker Compose, serviços, healthchecks, entrypoint |
| [[Testes]] | Pytest, TestContainers, factories, marcadores |
| [[Ambiente de Desenvolvimento]] | Tarefas disponíveis, variáveis de ambiente, migrações |
| [[Pendências e Issues]] | TODOs conhecidos, bugs, itens a implementar |

---

## Diagrama Rápido

```
Frontend (Vue 3)
    ↓ HTTP/REST
FastAPI (app/)
    ├── Auth (JWT)
    ├── Tenant ← Multi-tenancy
    ├── Usuario
    ├── MesReferencia → auto-importa CustoFixo
    ├── Custo (FIXO | VARIAVEL)
    └── PagamentoRateio (validação ≤ 100%)
    ↓
PostgreSQL (asyncpg)

Celery Worker + Beat
    └── 09h diário: checa vencimentos → envia emails (Mailpit/SMTP)
```

---

> Repositório: `homo` branch | Main: `main`
> Última atualização: 2026-03-04

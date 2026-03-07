# Regras de Negócio

[[Índice|← Índice]]

---

## Validação de Rateio

A regra mais crítica do sistema: a soma das porcentagens de todos os `PagamentoRateio` de um mesmo custo **nunca pode ultrapassar 100%**.

### Na criação

```
POST /api/rateios/
{ custo_id: 1, usuario_id: X, porcentagem: 60 }
```

1. Service busca soma atual: `SELECT SUM(porcentagem) FROM pagamento_rateio WHERE custo_id = 1`
2. Calcula total: `soma_atual + nova_porcentagem`
3. Se `total > 100` → lança `HTTPException 400`:
   ```json
   {
     "detail": "Soma das porcentagens excede 100%. Atual: 60%, Tentando adicionar: 50%, Total seria: 110%"
   }
   ```
4. Se válido → calcula `valor_calculado = (custo.valor * porcentagem) / 100`
5. Salva o registro

### Na atualização

```
PUT /api/rateios/{id}
{ porcentagem: 70 }
```

1. Service busca soma **excluindo** o registro sendo atualizado
2. Verifica se `soma_restante + 70 <= 100`
3. Se válido → recalcula `valor_calculado` e salva

### Validação de schema (Pydantic)

Antes mesmo do service, o schema valida individualmente:
- `porcentagem` deve ser `> 0` e `<= 100`
- Falha com `422 Unprocessable Entity`

---

## Criação Automática do Mês

**Endpoint:** `GET /api/meses/tenant/{tenant_id}/atual`

### Fluxo

```
1. Pega data atual (hoje)
2. Busca MesReferencia onde tenant_id=X AND ano=2026 AND mes=3
3. Se encontrado → retorna o existente
4. Se não encontrado:
   a. Cria MesReferencia(ano=2026, mes=3, status=ABERTO)
   b. Chama importar_custos_fixos_para_mes()
   c. Retorna o novo mês com custos importados
```

### Importação de Custos Fixos

```
importar_custos_fixos_para_mes(mes_referencia_id, tenant_id):
  1. SELECT * FROM custo_fixo WHERE tenant_id=X AND ativo=True
  2. Para cada CustoFixo:
     a. data_vencimento = date(ano, mes, dia_vencimento)
        → edge case: dia 31 em fevereiro → usa último dia do mês
     b. Cria Custo(
          descricao=custo_fixo.descricao,
          valor=custo_fixo.valor,
          data_vencimento=data_vencimento,
          tipo=FIXO,
          status=PENDENTE,
          mes_referencia_id=...,
          custo_fixo_origem_id=custo_fixo.id
        )
  3. session.flush() — persiste em lote
  4. Retorna lista de custos criados
```

**Idempotência:** A constraint única `(tenant_id, ano, mes)` previne duplicação de meses.

---

## Fluxo de Criação de Custo Variável

```
POST /api/custos/
{
  descricao: "Encanador",
  valor: 350.00,
  data_vencimento: "2026-03-15",
  tipo: "VARIAVEL",
  mes_referencia_id: 5
}
```

- `custo_fixo_origem_id` é `null` (não tem template)
- Pode ser rateado normalmente após criação

---

## Regras de Validação por Entidade

### MesReferencia
- `mes` deve ser entre 1 e 12
- `ano` deve ser entre 2000 e 2100
- Combinação `(tenant_id, ano, mes)` deve ser única

### CustoFixo
- `dia_vencimento` deve ser entre 1 e 31
- `valor` deve ser > 0

### Custo
- `valor` deve ser > 0

### PagamentoRateio
- `porcentagem` deve ser > 0 e ≤ 100 (schema)
- Soma total por `custo_id` ≤ 100% (service)
- Um usuário pode ter apenas um rateio por custo (constraint único)

### Usuario
- `username` deve ser único no banco
- `email` deve ser único no banco
- Validado via `EmailStr` do Pydantic

---

## Fluxo Completo de Uso Mensal

```
Março 2026 — João acessa o sistema:

1. GET /api/meses/tenant/1/atual
   → Cria MesReferencia(2026, 3)
   → Importa: Aluguel R$1200, Internet R$99

2. POST /api/custos/                        ← custo variável
   { descricao: "Encanador", valor: 150 }

3. POST /api/rateios/                       ← distribuição
   { custo_id: 1, usuario_id: 1, porcentagem: 40 }  → João: R$480
   { custo_id: 1, usuario_id: 2, porcentagem: 60 }  → Maria: R$720

4. POST /api/rateios/                       ← internet: 50/50
   { custo_id: 2, usuario_id: 1, porcentagem: 50 }  → João: R$49,50
   { custo_id: 2, usuario_id: 2, porcentagem: 50 }  → Maria: R$49,50

5. Celery às 09h verifica vencimentos
   → Manda email para João e Maria 3 dias antes
```

---

Ver também: [[Modelos de Dados]] | [[Sistema de Notificações]] | [[Módulos da API]]

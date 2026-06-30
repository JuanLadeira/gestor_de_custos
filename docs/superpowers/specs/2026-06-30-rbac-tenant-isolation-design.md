# RBAC + Isolamento de Tenant — Design

**Data:** 2026-06-30
**Status:** Aprovado, pronto para plano de implementação

## Problema

Dois problemas de autorização, acoplados:

1. **Furo de segurança (isolamento de tenant):** os routers de domínio de custos
   (`tenant`, `usuario`, `mes_referencia`, `custo`, `custo_fixo`, `pagamento_rateio`)
   não têm nenhuma dependência de autenticação. Qualquer chamador lê/escreve dados de
   qualquer tenant passando `tenant_id`/`mes_referencia_id` como query param ou no body.
   O frontend envia `authStore.tenantId`, mas o backend nunca valida. Apenas
   `whatsapp`, `campanha` e `assinatura` usam `CurrentUser` e escopam por
   `current_user.tenant_id`.

2. **Falta de RBAC:** a autorização hoje é um enum binário `UsuarioRole(OWNER, MEMBER)`
   com a dependência `CurrentOwner` (checa `role == OWNER`). Não há granularidade para
   definir o que cada usuário pode fazer.

Este design resolve os dois: isolamento de tenant (qual linha você pode tocar —
horizontal) e RBAC (qual ação você pode executar — vertical).

## Decisões (travadas no brainstorming)

- RBAC de **roles → permissions granulares** (não roles fixas, não permissões soltas no user).
- **Permissions** = catálogo **global**, definido em código. Não se cria ação nova sem deploy.
- **Roles + RoleProfiles** = **por tenant**, OWNER faz CRUD, compostos a partir do catálogo global.
- Usuário recebe permissões via **um único RoleProfile** (FK). Sem roles avulsas.
- Permissions a **nível de tipo de recurso** (`recurso:ação`). Sem distinção own/any.
- **Tenant derivado sempre do JWT** (`current_user.tenant_id`). Remove `tenant_id` de query
  params e bodies. É breaking na API, aceito (frontend é nosso).
- Escopo: **backend (enforcement real) + frontend gating** (esconde botões/rotas) + `/me`
  expõe permissões.
- **Anti-lockout:** cada tenant tem um RoleProfile **"Dono"** `is_protected`, não editável e
  não deletável, com todas as permissões. Não se pode remover o último usuário com Dono.
- Admin global (`app/admin`) fica **intocado** — realm separado de superusuário.

## Modelo conceitual

```
Permission   (global, código)      custo:create, rateio:pay, ...
   ▲ N:N (role_permission)
Role         (por tenant, CRUD)    "Financeiro", "Atendimento", ...
   ▲ N:N (role_profile_role)
RoleProfile  (por tenant, CRUD)    "Dono"(protegido), "Gestor", "Membro"
   ▲ 1:N (usuario.role_profile_id)
Usuario
```

Permissões efetivas de um usuário = `DISTINCT permission.code` percorrendo
`usuario → role_profile → roles → permissions`.

O conceito "OWNER" deixa de ser enum e passa a ser "quem tem o RoleProfile Dono".

## 1. Data model

### Tabelas novas

**`permission`** (global, sem `tenant_id`):

| coluna | tipo | notas |
|---|---|---|
| id | int PK | |
| code | str(100) | unique, ex: `custo:create` |
| grupo | str(50) | ex: `custo` |
| descricao | str(255) | nullable |

Seedada do catálogo em código. App-wide.

**`role`** (por tenant):

| coluna | tipo | notas |
|---|---|---|
| id | int PK | |
| tenant_id | int FK → tenant.id (CASCADE) | |
| nome | str(100) | |
| descricao | str(255) | nullable |
| is_system | bool | default False; defaults seedados = True |

Unique `(tenant_id, nome)`.

**`role_permission`** (N:N): `role_id FK (CASCADE)`, `permission_id FK (CASCADE)`,
unique `(role_id, permission_id)`.

**`role_profile`** (por tenant):

| coluna | tipo | notas |
|---|---|---|
| id | int PK | |
| tenant_id | int FK → tenant.id (CASCADE) | |
| nome | str(100) | |
| descricao | str(255) | nullable |
| is_system | bool | default False |
| is_protected | bool | default False; só o Dono = True |

Unique `(tenant_id, nome)`.

**`role_profile_role`** (N:N): `role_profile_id FK (CASCADE)`, `role_id FK (CASCADE)`,
unique `(role_profile_id, role_id)`.

### Alteração em `usuario`

- Remove coluna `role` (enum `UsuarioRole`) e dropa o tipo enum `usuariorole`.
- Adiciona `role_profile_id` int FK → `role_profile.id`, `ondelete RESTRICT`
  (não apagar profile em uso), NOT NULL após backfill.

Todas as tabelas herdam `id/created_at/updated_at` da `Base` existente.

## 2. Catálogo de permissions (código)

`app/authz/catalog.py` — **dados puros**, sem import de models (a migration importa este
módulo). Conjunto inicial:

| Grupo | Codes |
|---|---|
| tenant | `tenant:read`, `tenant:update` |
| usuario | `usuario:read`, `usuario:create`, `usuario:update`, `usuario:delete` |
| authz | `role:read`, `role:manage`, `profile:read`, `profile:manage`, `profile:assign` |
| custo | `custo:read`, `custo:create`, `custo:update`, `custo:delete` |
| custo_fixo | `custo_fixo:read`, `custo_fixo:create`, `custo_fixo:update`, `custo_fixo:delete` |
| mes | `mes:read`, `mes:create`, `mes:update`, `mes:import_fixos` |
| rateio | `rateio:read`, `rateio:create`, `rateio:update`, `rateio:delete`, `rateio:pay`, `comprovante:upload` |
| whatsapp | `whatsapp:read`, `whatsapp:manage`, `whatsapp:send` |
| campanha | `campanha:read`, `campanha:create`, `campanha:update`, `campanha:delete`, `campanha:activate` |
| inbox | `inbox:read`, `inbox:reply`, `inbox:manage` |
| assinatura | `assinatura:read` |

Semântica de codes "manage": `role:manage` cobre create/update/delete de roles;
`profile:manage` idem profiles; `profile:assign` = trocar o profile de um membro;
`whatsapp:manage` = criar/deletar instância; `inbox:manage` = encerrar conversa.

## 3. Defaults seedados por tenant

Definidos como dados em `catalog.py`. Ao criar um tenant, geram-se:

**Roles default** (`is_system=True`):

| Role | Permissions |
|---|---|
| Administração | `tenant:*`, `usuario:*`, `role:*`, `profile:*`, `assinatura:read` |
| Financeiro | `custo:*`, `custo_fixo:*`, `mes:*`, `rateio:*`, `comprovante:upload` |
| Atendimento | `whatsapp:*`, `campanha:*`, `inbox:*` |
| Leitura | todos os `*:read` |

(`*` expandido para os codes concretos do grupo, não armazenado como wildcard.)

**Profiles default** (`is_system=True`):

| Profile | Roles | Flags |
|---|---|---|
| Dono | todas | `is_protected=True` |
| Gestor | Financeiro + Atendimento + Leitura (+ `usuario:read`, `profile:assign` via role auxiliar) | |
| Membro | Leitura + `rateio:pay` + `comprovante:upload` + `inbox:reply` + `campanha:read` | |
| Leitor | Leitura | |

Onde um profile precisa de permissões que não casam exatamente com uma role default,
o seed cria roles auxiliares de granularidade adequada (ex.: uma role "Membro Base" com
`rateio:pay`, `comprovante:upload`, `inbox:reply`, `campanha:read`). O critério: o profile
sempre se compõe de roles; nunca aponta permission direto.

OWNER fundador recebe **Dono**. Demais profiles editáveis pelo OWNER (menos Dono).

## 4. Anti-lockout

- RoleProfile **Dono** (`is_protected=True`): update e delete → **409 Conflict**.
- Roles/profiles `is_system=True`: não deletáveis (409); editáveis exceto o Dono.
  Apenas roles/profiles criados pelo OWNER (`is_system=False`) são deletáveis.
- `profile:assign`: bloquear (409) qualquer operação que deixe o tenant com **zero**
  usuários ativos com o profile Dono. Garante sempre ≥1 administrador.

## 5. Enforcement (backend)

Pacote novo `app/authz/`:

- `catalog.py` — constants/dados puros (permissions + defaults de roles/profiles).
- `models.py` — `Permission`, `Role`, `RoleProfile` + tabelas de associação.
- `service.py` — `AuthzService`:
  - `resolve_permissions(user) -> set[str]` — uma query com joins.
  - `seed_global_permissions()` — upsert idempotente do catálogo.
  - `seed_tenant_defaults(tenant_id)` — cria roles/profiles default do tenant (idempotente).
  - CRUD de roles e profiles (escopado a tenant).
  - `assign_profile(user_id, profile_id)` — com checagem anti-lockout.
- `dependencies.py`:
  - `get_current_permissions(current_user) -> set[str]` — resolve via uma query, cacheia em
    `request.state.permissions` para reuso no mesmo request.
  - `require(*codes)` — factory que retorna uma dependency FastAPI; **403** se faltar qualquer
    code. Uso: `_: None = Depends(require("custo:create"))`.
- `schemas.py`, `router.py` — endpoints OWNER (seção 8).

A dependência `CurrentOwner` (checa o enum antigo) é **removida**; cada uso vira um
`require(<perm>)` específico. `CurrentUser` permanece.

## 6. Isolamento de tenant

Regra única: **`tenant_id` vem sempre de `current_user.tenant_id`**.

Mudanças por router:

- Remove `tenant_id`/`mes_referencia_id` como query param onde servia de filtro de tenant;
  deriva do usuário.
- Remove `tenant_id` dos bodies de entrada (`UsuarioCreate`, `MesReferenciaCreate`,
  `CustoFixoCreate`) — injetado server-side a partir do usuário.
- Recurso aninhado validado por join contra o tenant do usuário:
  - `custo` → via `mes_referencia.tenant_id`
  - `rateio` → via `custo → mes_referencia.tenant_id` **e** `usuario.tenant_id`
- Helpers em service (`assert_tenant_owns_mes`, `assert_tenant_owns_custo`, ...) retornam
  **404** se o recurso não pertence ao tenant (404, não 403, para não vazar existência).

Routers afetados (hoje abertos): `tenant`, `usuario`, `mes_referencia`, `custo`,
`custo_fixo`, `pagamento_rateio`. Cada endpoint recebe `CurrentUser` + `require(<perm>)` +
escopo de tenant.

**Caso especial `/api/tenants`:** create e delete de tenant são operações de plataforma →
restritas ao **admin global** (movidas para `app/admin` ou exigindo o realm de admin).
`tenant:read`/`tenant:update` permanecem para o próprio tenant do usuário.

**Campanha tasks:** já chamam endpoints internos (`/api/usuarios/`, `/api/rateios/`,
`/api/custos/`) com JWT do owner via `use_system_token`. Com o tenant derivado do token e o
param `tenant_id` removido, continuam funcionando sem regressão — passam a respeitar
isolamento automaticamente. O token de serviço gerado deve pertencer a um owner com as
permissões necessárias (o Dono cobre).

### Mapa endpoint → permission (referência)

| Endpoint | Permission |
|---|---|
| `GET /api/usuarios` | `usuario:read` |
| `POST /api/usuarios` | `usuario:create` |
| `PUT /api/usuarios/{id}` | `usuario:update` |
| `DELETE /api/usuarios/{id}` | `usuario:delete` |
| `GET /api/meses*` | `mes:read` |
| `POST /api/meses` | `mes:create` |
| `PUT /api/meses/{id}` | `mes:update` |
| `POST /api/meses/{id}/importar-custos-fixos` | `mes:import_fixos` |
| `GET /api/custos*` | `custo:read` |
| `POST /api/custos` | `custo:create` |
| `PUT /api/custos/{id}` | `custo:update` |
| `DELETE /api/custos/{id}` | `custo:delete` |
| `GET /api/custos-fixos*` | `custo_fixo:read` |
| `POST /api/custos-fixos` | `custo_fixo:create` |
| `PUT /api/custos-fixos/{id}` | `custo_fixo:update` |
| `DELETE /api/custos-fixos/{id}` | `custo_fixo:delete` |
| `GET /api/rateios*` | `rateio:read` |
| `POST /api/rateios` | `rateio:create` |
| `PUT /api/rateios/{id}` (status=PAGO) | `rateio:pay` (senão `rateio:update`) |
| `DELETE /api/rateios/{id}` | `rateio:delete` |
| `POST /api/rateios/{id}/comprovante` | `comprovante:upload` |
| `GET /api/tenants/{meu}` | `tenant:read` |
| `PUT /api/tenants/{meu}` | `tenant:update` |
| `POST/DELETE /api/tenants` | admin global |

Os routers `whatsapp`/`campanha`/`inbox` (já scoped por tenant) ganham os `require(<perm>)`
correspondentes (`whatsapp:*`, `campanha:*`, `inbox:*`) — enforcement de permission sobre o
isolamento que já existe.

## 7. Endpoints novos (OWNER CRUD + /me)

Prefixo `/api/authz` (todos exigem permission e são escopados ao tenant do usuário):

- `GET /permissions` — `role:read` ou `profile:read` — retorna catálogo (para montar UI).
- `GET /roles`, `POST /roles`, `PUT /roles/{id}`, `DELETE /roles/{id}` —
  `role:read` / `role:manage`. Body de role inclui lista de `permission_id`/`code`.
- `GET /profiles`, `POST /profiles`, `PUT /profiles/{id}`, `DELETE /profiles/{id}` —
  `profile:read` / `profile:manage`. Body inclui lista de `role_id`. PUT/DELETE no Dono → 409.
- `PUT /usuarios/{id}/profile` — `profile:assign`. Com checagem anti-lockout.

`GET /api/usuarios/me` passa a retornar `role_profile` (id/nome) + `permissions: list[str]`.

## 8. Migration (Alembic)

Uma migration `add_rbac` (segue a cadeia após `i7j8k9l0m1n2`):

1. cria as 5 tabelas novas (`permission`, `role`, `role_permission`, `role_profile`,
   `role_profile_role`).
2. `add_column usuario.role_profile_id` (nullable).
3. data migration:
   - `seed_global_permissions()` a partir de `catalog.py`.
   - para cada tenant existente: `seed_tenant_defaults(tenant_id)`.
   - backfill `usuario.role_profile_id`: OWNER → Dono, MEMBER → Membro (por tenant).
4. `alter usuario.role_profile_id` NOT NULL.
5. drop `usuario.role` + drop tipo enum `usuariorole`.

Segue o gotcha de enums em Postgres já documentado no projeto (enum como var de módulo,
usado direto no create_table; `create_type=False` em add_column). O seed na migration reusa
`app/authz/catalog.py` (dados puros, sem dependência circular de models).

### Call-sites atualizados

- `TenantService.create` → chama `AuthzService.seed_tenant_defaults(tenant.id)` na mesma
  transação.
- `app/stripe_webhooks/handlers.py` (`handle_checkout_completed`) → cria o usuário OWNER e
  atribui o profile **Dono** (remove `role=UsuarioRole.OWNER`).
- `app/admin/router.py` (create user em tenant) → recebe/atribui `role_profile_id`.
- `scripts/populate_data.py` → seeda authz por tenant e atribui profiles.

## 9. Frontend (gating)

- `api/client.ts`: `getMe` inclui `permissions`; novos endpoints authz (roles/profiles/assign,
  permissions).
- `stores/auth.ts`: novo estado `permissions: string[]` (persistido em sessionStorage);
  helper `can(code: string): boolean`. Remove `isOwner`/`role`; usos viram `can('usuario:create')` etc.
- `router/index.ts`: suportar `meta.permission?`; guard redireciona se faltar.
- `App.vue`: filtra itens de nav por permission.
- Telas (`Custos`, `Rateios`, `Usuarios`, `Campanhas`, `CampanhaDetalhe`, `Inbox`): botões de
  ação com `v-if="can(...)"`. A API permanece fonte da verdade (403 mesmo se o botão vazar).
- **Membros**: dropdown de RoleProfile ao convidar/editar membro (gated `profile:assign`).
- **Nova tela "Perfis & Papéis"** (gated `role:manage`/`profile:manage`): CRUD de roles
  (marca permissions do catálogo) e de profiles (marca roles). Dono em modo read-only.

## 10. Testes

Marker novo `authz` no pytest (`pyproject.toml`).

- `AuthzService.resolve_permissions` — união correta das permissions via profile→roles.
- `seed_global_permissions` / `seed_tenant_defaults` — idempotentes (rodar 2x não duplica).
- `require()` — 403 sem permission, 200 com.
- Isolamento: usuário do tenant A recebe **404** ao acessar recurso do tenant B, em cada
  router (custo, mes, rateio, usuario, custo_fixo). Padrão de fixture async direto
  (factory_boy não funciona com async — ver memória do projeto).
- Anti-lockout: Dono não editável/deletável (409); não remover o último usuário com Dono.
- Backfill da migration (smoke): OWNER vira Dono, MEMBER vira Membro.

## 11. Fases (entrada para o plano de implementação)

1. **Core authz** — `catalog.py`, `models.py`, migration só com as tabelas, `AuthzService`
   (`resolve_permissions` + `seed_global_permissions`), `dependencies.py`. 
2. **Seed por tenant + backfill** — `seed_tenant_defaults`, data migration migrando usuários
   para profiles, drop do enum, atualização de Stripe/admin/populate.
3. **Fix de segurança** — `require()` + isolamento de tenant em todos os routers abertos +
   testes de isolamento. *(fecha o furo)*
4. **CRUD authz + /me** — endpoints OWNER de roles/profiles/assign, `/me` com permissions.
5. **Frontend** — gating de nav/botões/rotas + tela de gestão de Perfis & Papéis.

## Decisões padrão tomadas (reversíveis)

- `/api/tenants` create/delete → admin global (não é mais público nem do OWNER).
- Recurso fora do tenant retorna **404** (não 403), para não vazar existência.
- `is_system` defaults não são deletáveis; só roles/profiles criados pelo OWNER são.
- Profiles sempre se compõem de roles (nunca de permission direto); seed cria roles
  auxiliares quando necessário.

## Fora de escopo (YAGNI por ora)

- Múltiplas roles/profiles por usuário; roles avulsas além do profile.
- Permissions own/any (nível de objeto).
- CRUD do catálogo de permissions (é fixo em código).
- RBAC para o admin global (continua superusuário único).

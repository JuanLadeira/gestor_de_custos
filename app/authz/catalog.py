"""Global permission catalog and per-tenant default roles/profiles.

Pure data — no imports of app models, so Alembic migrations can import it
without triggering circular imports.
"""

# (code, grupo, descricao)
PERMISSIONS: list[tuple[str, str, str]] = [
    ("tenant:read", "tenant", "Ver dados do tenant"),
    ("tenant:update", "tenant", "Editar dados do tenant"),
    ("usuario:read", "usuario", "Listar/ver usuários"),
    ("usuario:create", "usuario", "Convidar usuários"),
    ("usuario:update", "usuario", "Editar usuários"),
    ("usuario:delete", "usuario", "Remover usuários"),
    ("role:read", "authz", "Ver papéis"),
    ("role:manage", "authz", "Criar/editar/excluir papéis"),
    ("profile:read", "authz", "Ver perfis"),
    ("profile:manage", "authz", "Criar/editar/excluir perfis"),
    ("profile:assign", "authz", "Atribuir perfil a usuários"),
    ("custo:read", "custo", "Ver custos"),
    ("custo:create", "custo", "Criar custos"),
    ("custo:update", "custo", "Editar custos"),
    ("custo:delete", "custo", "Remover custos"),
    ("custo:import", "custo", "Importar fatura de cartão"),
    ("custo_fixo:read", "custo_fixo", "Ver custos fixos"),
    ("custo_fixo:create", "custo_fixo", "Criar custos fixos"),
    ("custo_fixo:update", "custo_fixo", "Editar custos fixos"),
    ("custo_fixo:delete", "custo_fixo", "Remover custos fixos"),
    ("mes:read", "mes", "Ver meses de referência"),
    ("mes:create", "mes", "Criar meses de referência"),
    ("mes:update", "mes", "Editar meses de referência"),
    ("mes:import_fixos", "mes", "Importar custos fixos no mês"),
    ("rateio:read", "rateio", "Ver rateios"),
    ("rateio:create", "rateio", "Criar rateios"),
    ("rateio:update", "rateio", "Editar rateios"),
    ("rateio:delete", "rateio", "Remover rateios"),
    ("rateio:pay", "rateio", "Marcar rateio como pago"),
    ("comprovante:upload", "rateio", "Enviar comprovante"),
    ("whatsapp:read", "whatsapp", "Ver instâncias WhatsApp"),
    ("whatsapp:manage", "whatsapp", "Criar/excluir instâncias WhatsApp"),
    ("whatsapp:send", "whatsapp", "Enviar mensagens WhatsApp"),
    ("campanha:read", "campanha", "Ver campanhas"),
    ("campanha:create", "campanha", "Criar campanhas"),
    ("campanha:update", "campanha", "Editar campanhas"),
    ("campanha:delete", "campanha", "Remover campanhas"),
    ("campanha:activate", "campanha", "Ativar/pausar/concluir campanhas"),
    ("inbox:read", "inbox", "Ver conversas"),
    ("inbox:reply", "inbox", "Responder conversas"),
    ("inbox:manage", "inbox", "Encerrar conversas"),
    ("assinatura:read", "assinatura", "Ver assinatura"),
]


def all_codes() -> list[str]:
    return [code for code, _, _ in PERMISSIONS]


def codes_for_grupos(*grupos: str) -> list[str]:
    wanted = set(grupos)
    return [code for code, grupo, _ in PERMISSIONS if grupo in wanted]


def read_codes() -> list[str]:
    return [code for code in all_codes() if code.endswith(":read")]


# role name -> permission codes
DEFAULT_ROLES: dict[str, list[str]] = {
    "Administração": codes_for_grupos("tenant", "usuario", "authz") + ["assinatura:read"],
    "Financeiro": codes_for_grupos("custo", "custo_fixo", "mes", "rateio"),
    "Atendimento": codes_for_grupos("whatsapp", "campanha", "inbox"),
    "Leitura": read_codes(),
    # auxiliary role so the Membro profile gets exactly the right grants
    "Membro Base": ["rateio:pay", "comprovante:upload", "inbox:reply", "campanha:read"],
    # auxiliary role for Gestor's lighter management grants
    "Gestão Leve": ["usuario:read", "profile:assign"],
}

# profile name -> roles + flags
DEFAULT_PROFILES: dict[str, dict] = {
    "Dono": {
        "roles": ["Administração", "Financeiro", "Atendimento", "Leitura",
                  "Membro Base", "Gestão Leve"],
        "is_protected": True,
    },
    "Gestor": {
        "roles": ["Financeiro", "Atendimento", "Leitura", "Gestão Leve"],
        "is_protected": False,
    },
    "Membro": {
        "roles": ["Leitura", "Membro Base"],
        "is_protected": False,
    },
    "Leitor": {
        "roles": ["Leitura"],
        "is_protected": False,
    },
}

"""drop_role_add_role_profile_id

Revision ID: k9l0m1n2o3p4
Revises: j8k9l0m1n2o3
Create Date: 2026-06-30 23:05:00.000000

Replace the UsuarioRole enum column with a role_profile_id FK.
Tables (permission, role, role_profile, role_permission, role_profile_role)
were already created by revision j8k9l0m1n2o3. This migration:
  1. Adds role_profile_id FK (RESTRICT) to usuario
  2. Seeds global permissions
  3. Creates per-tenant default roles + profiles
  4. Backfills OWNER -> Dono, MEMBER -> Membro
  5. Makes role_profile_id NOT NULL
  6. Drops the old role column + usuariorole enum
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.authz.catalog import DEFAULT_PROFILES, DEFAULT_ROLES, PERMISSIONS

revision: str = "k9l0m1n2o3p4"
down_revision: Union[str, Sequence[str], None] = "j8k9l0m1n2o3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Add role_profile_id as nullable FK (RESTRICT — can't delete a profile in use)
    op.add_column("usuario", sa.Column("role_profile_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_usuario_role_profile",
        "usuario",
        "role_profile",
        ["role_profile_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 2. Seed global permissions (tables are empty — created by j8k9l0m1n2o3)
    bind.execute(
        sa.text(
            "INSERT INTO permission (code, grupo, descricao, created_at, updated_at) "
            "VALUES (:code, :grupo, :descricao, now(), now())"
        ),
        [{"code": c, "grupo": g, "descricao": d} for c, g, d in PERMISSIONS],
    )
    perm_ids = {
        row.code: row.id
        for row in bind.execute(sa.text("SELECT id, code FROM permission"))
    }

    # 3. Per-tenant: create default roles + profiles + backfill
    tenants = list(bind.execute(sa.text("SELECT id FROM tenant")))
    for (tenant_id,) in tenants:
        role_ids: dict[str, int] = {}
        for nome, codes in DEFAULT_ROLES.items():
            res = bind.execute(
                sa.text(
                    "INSERT INTO role (tenant_id, nome, is_system, created_at, updated_at) "
                    "VALUES (:t, :n, true, now(), now()) RETURNING id"
                ),
                {"t": tenant_id, "n": nome},
            )
            rid = res.scalar_one()
            role_ids[nome] = rid
            for code in codes:
                bind.execute(
                    sa.text(
                        "INSERT INTO role_permission (role_id, permission_id) VALUES (:r, :p)"
                    ),
                    {"r": rid, "p": perm_ids[code]},
                )

        profile_ids: dict[str, int] = {}
        for nome, spec in DEFAULT_PROFILES.items():
            res = bind.execute(
                sa.text(
                    "INSERT INTO role_profile "
                    "(tenant_id, nome, is_system, is_protected, created_at, updated_at) "
                    "VALUES (:t, :n, true, :prot, now(), now()) RETURNING id"
                ),
                {"t": tenant_id, "n": nome, "prot": spec["is_protected"]},
            )
            pid = res.scalar_one()
            profile_ids[nome] = pid
            for role_nome in spec["roles"]:
                bind.execute(
                    sa.text(
                        "INSERT INTO role_profile_role (role_profile_id, role_id) "
                        "VALUES (:pf, :r)"
                    ),
                    {"pf": pid, "r": role_ids[role_nome]},
                )

        # 4. Backfill: OWNER -> Dono, MEMBER -> Membro (old role column still present)
        bind.execute(
            sa.text(
                "UPDATE usuario SET role_profile_id = :pf "
                "WHERE tenant_id = :t AND role = 'OWNER'"
            ),
            {"pf": profile_ids["Dono"], "t": tenant_id},
        )
        bind.execute(
            sa.text(
                "UPDATE usuario SET role_profile_id = :pf "
                "WHERE tenant_id = :t AND role = 'MEMBER'"
            ),
            {"pf": profile_ids["Membro"], "t": tenant_id},
        )

    # Defensive: any remaining NULL -> tenant's Dono profile
    bind.execute(
        sa.text(
            "UPDATE usuario u SET role_profile_id = "
            "(SELECT id FROM role_profile p WHERE p.tenant_id = u.tenant_id AND p.nome = 'Dono') "
            "WHERE u.role_profile_id IS NULL"
        )
    )

    # 5. Enforce NOT NULL now that every row is filled
    op.alter_column("usuario", "role_profile_id", nullable=False)

    # 6. Drop the old role enum column and the enum type
    op.drop_column("usuario", "role")
    sa.Enum(name="usuariorole").drop(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()

    # Purge seeded data in FK-dependency order so a subsequent re-upgrade starts clean
    # (link tables first, then profiles/roles restricted to is_system, then all permissions)
    bind.execute(sa.text("DELETE FROM role_profile_role"))
    bind.execute(sa.text("DELETE FROM role_permission"))
    bind.execute(sa.text("DELETE FROM role_profile WHERE is_system = true"))
    bind.execute(sa.text("DELETE FROM role WHERE is_system = true"))
    bind.execute(sa.text("DELETE FROM permission"))

    # Recreate the old enum + column (default MEMBER for existing rows)
    usuariorole = sa.Enum("OWNER", "MEMBER", name="usuariorole")
    usuariorole.create(bind, checkfirst=True)
    op.add_column(
        "usuario",
        sa.Column(
            "role",
            sa.Enum("OWNER", "MEMBER", name="usuariorole", create_type=False),
            nullable=False,
            server_default="MEMBER",
        ),
    )

    # Drop the FK constraint and the column
    op.drop_constraint("fk_usuario_role_profile", "usuario", type_="foreignkey")
    op.drop_column("usuario", "role_profile_id")

"""add_saas_models

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-05 00:02:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

assinaturastatus = sa.Enum("ATIVA", "SUSPENSA", "CANCELADA", name="assinaturastatus")


def upgrade() -> None:
    """Create SaaS tables: admin, plano, assinatura."""

    # ── admin ──────────────────────────────────────────────────────────────
    op.create_table(
        "admin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_email"), "admin", ["email"], unique=True)
    op.create_index(op.f("ix_admin_username"), "admin", ["username"], unique=True)

    # ── plano ──────────────────────────────────────────────────────────────
    op.create_table(
        "plano",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("preco_mensal", sa.Numeric(10, 2), nullable=False),
        sa.Column("preco_anual", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_usuarios", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("stripe_price_id_mensal", sa.String(length=100), nullable=True),
        sa.Column("stripe_price_id_anual", sa.String(length=100), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── assinatura ─────────────────────────────────────────────────────────
    # assinaturastatus enum is created automatically by create_table
    op.create_table(
        "assinatura",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", assinaturastatus, nullable=False, server_default="ATIVA"),
        sa.Column("stripe_subscription_id", sa.String(length=100), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=100), nullable=True),
        sa.Column("data_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_proxima_cobranca", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("plano_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["plano_id"], ["plano.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )


def downgrade() -> None:
    """Drop SaaS tables."""
    op.drop_table("assinatura")
    assinaturastatus.drop(op.get_bind())
    op.drop_table("plano")
    op.drop_index(op.f("ix_admin_username"), table_name="admin")
    op.drop_index(op.f("ix_admin_email"), table_name="admin")
    op.drop_table("admin")

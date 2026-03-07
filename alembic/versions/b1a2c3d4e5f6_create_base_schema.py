"""create_base_schema

Revision ID: b1a2c3d4e5f6
Revises: 404af90b75eb
Create Date: 2026-03-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "404af90b75eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum types used in this migration
custotipo = sa.Enum("FIXO", "VARIAVEL", name="custotipo")
custostatus = sa.Enum("PENDENTE", "PAGO", name="custostatus")
pagamentostatus = sa.Enum("PENDENTE", "PAGO", name="pagamentostatus")


def upgrade() -> None:
    """Create full app base schema."""

    # ── tenant ─────────────────────────────────────────────────────────────
    op.create_table(
        "tenant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── usuario ────────────────────────────────────────────────────────────
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuario_email"), "usuario", ["email"], unique=True)
    op.create_index(op.f("ix_usuario_username"), "usuario", ["username"], unique=True)

    # ── mes_referencia ─────────────────────────────────────────────────────
    op.create_table(
        "mes_referencia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── custo_fixo ─────────────────────────────────────────────────────────
    op.create_table(
        "custo_fixo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── custo ──────────────────────────────────────────────────────────────
    # custotipo and custostatus enums are created here automatically
    op.create_table(
        "custo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("tipo", custotipo, nullable=False),
        sa.Column("status", custostatus, nullable=False, server_default="PENDENTE"),
        sa.Column("mes_referencia_id", sa.Integer(), nullable=False),
        sa.Column("custo_fixo_origem_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["custo_fixo_origem_id"], ["custo_fixo.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mes_referencia_id"], ["mes_referencia.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── pagamento_rateio ───────────────────────────────────────────────────
    # pagamentostatus enum is created here automatically
    op.create_table(
        "pagamento_rateio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("porcentagem", sa.Numeric(5, 2), nullable=False),
        sa.Column("valor_calculado", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", pagamentostatus, nullable=False, server_default="PENDENTE"),
        sa.Column("custo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["custo_id"], ["custo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop full app base schema."""
    op.drop_table("pagamento_rateio")
    op.drop_table("custo")
    op.drop_table("custo_fixo")
    op.drop_table("mes_referencia")
    op.drop_table("usuario")
    op.drop_table("tenant")
    pagamentostatus.drop(op.get_bind())
    custostatus.drop(op.get_bind())
    custotipo.drop(op.get_bind())

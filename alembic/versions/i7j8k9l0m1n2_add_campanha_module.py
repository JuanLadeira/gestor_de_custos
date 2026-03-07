"""add_campanha_module

Revision ID: i7j8k9l0m1n2
Revises: h6i7j8k9l0m1
Create Date: 2026-03-07 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "i7j8k9l0m1n2"
down_revision: Union[str, Sequence[str], None] = "h6i7j8k9l0m1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

campanhastatus = sa.Enum("RASCUNHO", "ATIVA", "PAUSADA", "CONCLUIDA", name="campanhastatus")
contatostatus = sa.Enum(
    "PENDENTE", "ENVIANDO", "ENVIADO", "FALHOU", "RESPONDEU", "EM_ATENDIMENTO",
    name="contatostatus",
)
conversastatus = sa.Enum("AGUARDANDO", "EM_ATENDIMENTO", "ENCERRADA", name="conversastatus")
mensagemtipo = sa.Enum("ENVIADA", "RECEBIDA", name="mensagemtipo")


def upgrade() -> None:
    op.create_table(
        "campanha",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("status", campanhastatus, nullable=False, server_default="RASCUNHO"),
        sa.Column("data_source", JSONB(), nullable=True),
        sa.Column("instancias_ids", JSONB(), nullable=True),
        sa.Column("rate_limit_por_hora", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("horario_inicio", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("horario_fim", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "template_mensagem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campanha_id", sa.Integer(), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campanha_id"], ["campanha.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contato_campanha",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campanha_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(30), nullable=False),
        sa.Column("nome", sa.String(200), nullable=True),
        sa.Column("variaveis", JSONB(), nullable=True),
        sa.Column("status", contatostatus, nullable=False, server_default="PENDENTE"),
        sa.Column("instancia_id", sa.Integer(), nullable=True),
        sa.Column("enviado_em", sa.DateTime(), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campanha_id"], ["campanha.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["instancia_id"], ["whatsapp_instancia.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conversa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("instancia_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(30), nullable=False),
        sa.Column("nome", sa.String(200), nullable=True),
        sa.Column("status", conversastatus, nullable=False, server_default="AGUARDANDO"),
        sa.Column("contato_campanha_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["instancia_id"], ["whatsapp_instancia.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["contato_campanha_id"], ["contato_campanha.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "mensagem_conversa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversa_id", sa.Integer(), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("tipo", mensagemtipo, nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("evolution_id", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversa.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("evolution_id"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("mensagem_conversa")
    op.drop_table("conversa")
    op.drop_table("contato_campanha")
    op.drop_table("template_mensagem")
    op.drop_table("campanha")

    campanhastatus.drop(op.get_bind(), checkfirst=True)
    contatostatus.drop(op.get_bind(), checkfirst=True)
    conversastatus.drop(op.get_bind(), checkfirst=True)
    mensagemtipo.drop(op.get_bind(), checkfirst=True)

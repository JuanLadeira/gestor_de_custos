"""add_whatsapp_instancia

Revision ID: h6i7j8k9l0m1
Revises: g5h6i7j8k9l0
Create Date: 2026-03-06 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h6i7j8k9l0m1"
down_revision: Union[str, Sequence[str], None] = "g5h6i7j8k9l0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

conexaostatus = sa.Enum("CRIADA", "CONECTANDO", "CONECTADA", "DESCONECTADA", name="conexaostatus")


def upgrade() -> None:
    op.create_table(
        "whatsapp_instancia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_name", sa.String(100), nullable=False),
        sa.Column("status", conexaostatus, nullable=False, server_default="CRIADA"),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_name"),
    )
    op.create_index("ix_whatsapp_instancia_instance_name", "whatsapp_instancia", ["instance_name"])


def downgrade() -> None:
    op.drop_index("ix_whatsapp_instancia_instance_name", table_name="whatsapp_instancia")
    op.drop_table("whatsapp_instancia")
    conexaostatus.drop(op.get_bind(), checkfirst=True)

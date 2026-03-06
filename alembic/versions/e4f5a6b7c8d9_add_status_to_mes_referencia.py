"""add_status_to_mes_referencia

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-06 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

statusmes = sa.Enum("ABERTO", "FECHADO", name="statusmes")


def upgrade() -> None:
    statusmes.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "mes_referencia",
        sa.Column(
            "status",
            sa.Enum("ABERTO", "FECHADO", name="statusmes", create_type=False),
            nullable=False,
            server_default="ABERTO",
        ),
    )
    op.create_unique_constraint(
        "uq_tenant_ano_mes", "mes_referencia", ["tenant_id", "ano", "mes"]
    )
    op.create_unique_constraint(
        "uq_custo_usuario", "pagamento_rateio", ["custo_id", "usuario_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_custo_usuario", "pagamento_rateio", type_="unique")
    op.drop_constraint("uq_tenant_ano_mes", "mes_referencia", type_="unique")
    op.drop_column("mes_referencia", "status")
    statusmes.drop(op.get_bind(), checkfirst=True)

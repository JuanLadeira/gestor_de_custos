"""add_cartao_credito_import

Revision ID: l0m1n2o3p4q5
Revises: k9l0m1n2o3p4
Create Date: 2026-07-01 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l0m1n2o3p4q5"
down_revision: Union[str, Sequence[str], None] = "k9l0m1n2o3p4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD VALUE não pode ser usado na mesma transação; roda em autocommit.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipocusto ADD VALUE IF NOT EXISTS 'CARTAO_CREDITO'")

    op.add_column("custo", sa.Column("import_fingerprint", sa.String(64), nullable=True))
    op.create_index("ix_custo_import_fingerprint", "custo", ["import_fingerprint"])
    # dedup: um fingerprint no máximo uma vez por mês
    op.create_index(
        "uq_custo_mes_fingerprint",
        "custo",
        ["mes_referencia_id", "import_fingerprint"],
        unique=True,
        postgresql_where=sa.text("import_fingerprint IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_custo_mes_fingerprint", table_name="custo")
    op.drop_index("ix_custo_import_fingerprint", table_name="custo")
    op.drop_column("custo", "import_fingerprint")
    # valor de enum não é removível sem recriar o tipo; downgrade deixa 'CARTAO_CREDITO'.

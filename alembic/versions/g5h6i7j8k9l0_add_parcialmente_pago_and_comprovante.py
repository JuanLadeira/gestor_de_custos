"""add_parcialmente_pago_and_comprovante

Revision ID: g5h6i7j8k9l0
Revises: f5a6b7c8d9e0
Create Date: 2026-03-06 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g5h6i7j8k9l0"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add PARCIALMENTE_PAGO value to the statuspagamento enum
    op.execute("ALTER TYPE statuspagamento ADD VALUE 'PARCIALMENTE_PAGO'")

    # Add comprovante_url column to pagamento_rateio
    op.add_column(
        "pagamento_rateio",
        sa.Column("comprovante_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    # Remove comprovante_url column
    op.drop_column("pagamento_rateio", "comprovante_url")

    # Revert PARCIALMENTE_PAGO values to PENDENTE before removing the enum value
    op.execute(
        "UPDATE custo SET status = 'PENDENTE' WHERE status = 'PARCIALMENTE_PAGO'"
    )

    # PostgreSQL doesn't support DROP VALUE on enums directly.
    # Recreate the enum without PARCIALMENTE_PAGO.
    op.execute("ALTER TYPE statuspagamento RENAME TO statuspagamento_old")
    op.execute("CREATE TYPE statuspagamento AS ENUM ('PENDENTE', 'PAGO')")
    op.execute(
        "ALTER TABLE custo ALTER COLUMN status TYPE statuspagamento "
        "USING status::text::statuspagamento"
    )
    op.execute("DROP TYPE statuspagamento_old")

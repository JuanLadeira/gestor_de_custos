"""rename_enum_types

Rename enum types to match SQLAlchemy auto-generated names (Python class name lowercased).

  custotipo     → tipocusto
  custostatus   → statuspagamento
  pagamentostatus → statusrateio

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-03-06 00:01:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE custotipo RENAME TO tipocusto")
    op.execute("ALTER TYPE custostatus RENAME TO statuspagamento")
    op.execute("ALTER TYPE pagamentostatus RENAME TO statusrateio")


def downgrade() -> None:
    op.execute("ALTER TYPE tipocusto RENAME TO custotipo")
    op.execute("ALTER TYPE statuspagamento RENAME TO custostatus")
    op.execute("ALTER TYPE statusrateio RENAME TO pagamentostatus")

"""add_role_to_usuario

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-03-05 00:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

usuariorole = sa.Enum("OWNER", "MEMBER", name="usuariorole")


def upgrade() -> None:
    """Add role column to usuario table."""
    usuariorole.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "usuario",
        sa.Column(
            "role",
            sa.Enum("OWNER", "MEMBER", name="usuariorole", create_type=False),
            nullable=False,
            server_default="MEMBER",
        ),
    )


def downgrade() -> None:
    """Remove role column from usuario table."""
    op.drop_column("usuario", "role")
    usuariorole.drop(op.get_bind())

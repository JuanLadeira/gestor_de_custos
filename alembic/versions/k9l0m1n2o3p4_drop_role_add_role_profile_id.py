"""drop_role_add_role_profile_id

Revision ID: k9l0m1n2o3p4
Revises: j8k9l0m1n2o3
Create Date: 2026-06-30 23:05:00.000000

Replace the UsuarioRole enum column with a role_profile_id FK.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k9l0m1n2o3p4"
down_revision: Union[str, Sequence[str], None] = "j8k9l0m1n2o3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role_profile_id FK (nullable — existing rows get NULL)
    op.add_column(
        "usuario",
        sa.Column(
            "role_profile_id",
            sa.Integer(),
            sa.ForeignKey("role_profile.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Drop the old role enum column
    op.drop_column("usuario", "role")

    # Drop the enum type itself
    op.execute("DROP TYPE IF EXISTS usuariorole")


def downgrade() -> None:
    usuariorole = sa.Enum("OWNER", "MEMBER", name="usuariorole")
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
    op.drop_column("usuario", "role_profile_id")

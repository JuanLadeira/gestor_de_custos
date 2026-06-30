from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    pass


role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
)

role_profile_role = Table(
    "role_profile_role",
    Base.metadata,
    Column("role_profile_id", ForeignKey("role_profile.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permission"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Role(Base):
    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_role_tenant_nome"),)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permission, lazy="selectin"
    )


class RoleProfile(Base):
    __tablename__ = "role_profile"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_profile_tenant_nome"),)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_profile_role, lazy="selectin"
    )

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.custo_fixo.models import CustoFixo
    from app.mes_referencia.models import MesReferencia
    from app.usuario.models import Usuario


class Tenant(Base):
    """Represents a household or group that shares costs."""

    __tablename__ = "tenant"

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    meses_referencia: Mapped[list["MesReferencia"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    custos_fixos: Mapped[list["CustoFixo"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

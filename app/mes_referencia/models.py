import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.custo.models import Custo
    from app.tenant.models import Tenant


class StatusMes(str, enum.Enum):
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class MesReferencia(Base):
    """Monthly reference period for costs."""

    __tablename__ = "mes_referencia"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ano", "mes", name="uq_tenant_ano_mes"),
    )

    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StatusMes] = mapped_column(
        Enum(StatusMes), default=StatusMes.ABERTO, nullable=False
    )

    # Foreign key
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="meses_referencia")
    custos: Mapped[list["Custo"]] = relationship(
        back_populates="mes_referencia",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

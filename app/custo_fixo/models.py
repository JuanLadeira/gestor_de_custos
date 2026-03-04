from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.custo.models import Custo
    from app.tenant.models import Tenant


class CustoFixo(Base):
    """Template for recurring monthly costs."""

    __tablename__ = "custo_fixo"

    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Foreign key
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="custos_fixos")
    custos_gerados: Mapped[list["Custo"]] = relationship(
        back_populates="custo_fixo_origem",
        lazy="selectin",
    )

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.custo.models import Custo
    from app.usuario.models import Usuario


class StatusRateio(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"


class PagamentoRateio(Base):
    """Cost sharing entry: percentage assigned to a user for a specific cost."""

    __tablename__ = "pagamento_rateio"
    __table_args__ = (
        UniqueConstraint("custo_id", "usuario_id", name="uq_custo_usuario"),
    )

    porcentagem: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    valor_calculado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[StatusRateio] = mapped_column(
        Enum(StatusRateio), default=StatusRateio.PENDENTE, nullable=False
    )
    comprovante_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Foreign keys
    custo_id: Mapped[int] = mapped_column(
        ForeignKey("custo.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    custo: Mapped["Custo"] = relationship(back_populates="pagamentos_rateio")
    usuario: Mapped["Usuario"] = relationship(back_populates="pagamentos_rateio")

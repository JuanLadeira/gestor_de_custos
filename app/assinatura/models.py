import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.plano.models import Plano
    from app.tenant.models import Tenant


class AssinaturaStatus(enum.Enum):
    ATIVA = "ATIVA"
    SUSPENSA = "SUSPENSA"
    CANCELADA = "CANCELADA"


class Assinatura(Base):
    """Subscription linking a tenant to a plan, managed via Stripe."""

    __tablename__ = "assinatura"

    status: Mapped[AssinaturaStatus] = mapped_column(
        Enum(AssinaturaStatus, name="assinaturastatus"),
        default=AssinaturaStatus.ATIVA,
        nullable=False,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_proxima_cobranca: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Foreign keys
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    plano_id: Mapped[int] = mapped_column(
        ForeignKey("plano.id", ondelete="RESTRICT"), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="assinaturas")
    plano: Mapped["Plano"] = relationship(back_populates="assinaturas")

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.assinatura.models import Assinatura


class Plano(Base):
    """Subscription plan available for tenants."""

    __tablename__ = "plano"

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    preco_mensal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_anual: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_usuarios: Mapped[int] = mapped_column(nullable=False, default=5)
    stripe_price_id_mensal: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_price_id_anual: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    features: Mapped[Any] = mapped_column(JSON, nullable=True)

    # Relationships
    assinaturas: Mapped[list["Assinatura"]] = relationship(
        back_populates="plano", lazy="selectin"
    )

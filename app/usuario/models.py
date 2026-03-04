from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.pagamento_rateio.models import PagamentoRateio
    from app.tenant.models import Tenant


class Usuario(Base):
    """User within a tenant who shares costs."""

    __tablename__ = "usuario"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Foreign key
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="usuarios")
    pagamentos_rateio: Mapped[list["PagamentoRateio"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

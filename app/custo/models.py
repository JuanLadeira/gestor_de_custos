import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.custo_fixo.models import CustoFixo
    from app.mes_referencia.models import MesReferencia
    from app.pagamento_rateio.models import PagamentoRateio


class TipoCusto(str, enum.Enum):
    FIXO = "FIXO"
    VARIAVEL = "VARIAVEL"
    CARTAO_CREDITO = "CARTAO_CREDITO"


class StatusPagamento(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PARCIALMENTE_PAGO = "PARCIALMENTE_PAGO"
    PAGO = "PAGO"


class Custo(Base):
    """Actual cost entry for a specific month."""

    __tablename__ = "custo"
    __table_args__ = (
        # dedup: um fingerprint no máximo uma vez por mês (espelha a migration
        # l0m1n2o3p4q5). Índice parcial: só vale quando há fingerprint.
        Index(
            "uq_custo_mes_fingerprint",
            "mes_referencia_id",
            "import_fingerprint",
            unique=True,
            postgresql_where=text("import_fingerprint IS NOT NULL"),
        ),
    )

    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[TipoCusto] = mapped_column(
        Enum(TipoCusto), default=TipoCusto.VARIAVEL, nullable=False
    )
    status: Mapped[StatusPagamento] = mapped_column(
        Enum(StatusPagamento), default=StatusPagamento.PENDENTE, nullable=False
    )

    # Foreign keys
    mes_referencia_id: Mapped[int] = mapped_column(
        ForeignKey("mes_referencia.id", ondelete="CASCADE"), nullable=False
    )
    custo_fixo_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("custo_fixo.id", ondelete="SET NULL"), nullable=True
    )
    import_fingerprint: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    # Relationships
    mes_referencia: Mapped["MesReferencia"] = relationship(back_populates="custos")
    custo_fixo_origem: Mapped["CustoFixo | None"] = relationship(
        back_populates="custos_gerados"
    )
    pagamentos_rateio: Mapped[list["PagamentoRateio"]] = relationship(
        back_populates="custo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

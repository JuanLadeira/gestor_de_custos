from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.pagamento_rateio.models import StatusRateio


class PagamentoRateioBase(BaseModel):
    porcentagem: Decimal
    custo_id: int
    usuario_id: int

    @field_validator("porcentagem")
    @classmethod
    def validate_porcentagem(cls, v: Decimal) -> Decimal:
        if v <= 0 or v > 100:
            raise ValueError("Porcentagem deve estar entre 0 e 100")
        return v


class PagamentoRateioCreate(PagamentoRateioBase):
    pass


class PagamentoRateioUpdate(BaseModel):
    porcentagem: Decimal | None = None
    status: StatusRateio | None = None

    @field_validator("porcentagem")
    @classmethod
    def validate_porcentagem(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("Porcentagem deve estar entre 0 e 100")
        return v


class PagamentoRateioPublic(PagamentoRateioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    valor_calculado: Decimal
    status: StatusRateio
    created_at: datetime
    updated_at: datetime

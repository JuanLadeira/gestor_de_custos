from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.custo.models import StatusPagamento, TipoCusto


class CustoBase(BaseModel):
    descricao: str
    valor: Decimal
    data_vencimento: date
    tipo: TipoCusto = TipoCusto.VARIAVEL
    mes_referencia_id: int

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class CustoCreate(CustoBase):
    custo_fixo_origem_id: int | None = None


class CustoUpdate(BaseModel):
    descricao: str | None = None
    valor: Decimal | None = None
    data_vencimento: date | None = None
    tipo: TipoCusto | None = None
    status: StatusPagamento | None = None

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class CustoPublic(CustoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusPagamento
    custo_fixo_origem_id: int | None
    created_at: datetime
    updated_at: datetime

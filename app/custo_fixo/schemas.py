from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class CustoFixoBase(BaseModel):
    descricao: str
    valor: Decimal
    dia_vencimento: int = 10
    tenant_id: int

    @field_validator("dia_vencimento")
    @classmethod
    def validate_dia_vencimento(cls, v: int) -> int:
        if not 1 <= v <= 31:
            raise ValueError("Dia de vencimento deve estar entre 1 e 31")
        return v

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class CustoFixoCreate(CustoFixoBase):
    pass


class CustoFixoUpdate(BaseModel):
    descricao: str | None = None
    valor: Decimal | None = None
    dia_vencimento: int | None = None
    ativo: bool | None = None

    @field_validator("dia_vencimento")
    @classmethod
    def validate_dia_vencimento(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 31:
            raise ValueError("Dia de vencimento deve estar entre 1 e 31")
        return v

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class CustoFixoPublic(CustoFixoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    created_at: datetime
    updated_at: datetime

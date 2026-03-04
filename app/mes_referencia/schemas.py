from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.mes_referencia.models import StatusMes


class MesReferenciaBase(BaseModel):
    ano: int
    mes: int
    tenant_id: int

    @field_validator("mes")
    @classmethod
    def validate_mes(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Mes deve estar entre 1 e 12")
        return v

    @field_validator("ano")
    @classmethod
    def validate_ano(cls, v: int) -> int:
        if v < 2000 or v > 2100:
            raise ValueError("Ano deve estar entre 2000 e 2100")
        return v


class MesReferenciaCreate(MesReferenciaBase):
    pass


class MesReferenciaUpdate(BaseModel):
    status: StatusMes | None = None


class MesReferenciaPublic(MesReferenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusMes
    created_at: datetime
    updated_at: datetime

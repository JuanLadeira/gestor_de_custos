from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PlanoBase(BaseModel):
    nome: str
    preco_mensal: float
    preco_anual: float
    max_usuarios: int = 5
    stripe_price_id_mensal: str | None = None
    stripe_price_id_anual: str | None = None
    ativo: bool = True
    features: dict[str, Any] | None = None


class PlanoCreate(PlanoBase):
    pass


class PlanoUpdate(BaseModel):
    nome: str | None = None
    preco_mensal: float | None = None
    preco_anual: float | None = None
    max_usuarios: int | None = None
    stripe_price_id_mensal: str | None = None
    stripe_price_id_anual: str | None = None
    ativo: bool | None = None
    features: dict[str, Any] | None = None


class PlanoPublic(PlanoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

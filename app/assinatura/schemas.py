from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.assinatura.models import AssinaturaStatus


class AssinaturaPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AssinaturaStatus
    stripe_subscription_id: str | None
    stripe_customer_id: str | None
    data_inicio: datetime | None
    data_fim: datetime | None
    data_proxima_cobranca: datetime | None
    tenant_id: int
    plano_id: int
    created_at: datetime
    updated_at: datetime


class AssinaturaCreate(BaseModel):
    plano_id: int
    status: AssinaturaStatus = AssinaturaStatus.ATIVA


class AssinaturaAdminPublic(AssinaturaPublic):
    tenant_nome: str
    plano_nome: str


class AssinaturaUpdate(BaseModel):
    status: AssinaturaStatus | None = None
    data_proxima_cobranca: datetime | None = None

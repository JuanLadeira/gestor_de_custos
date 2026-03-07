from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.campanha.models import CampanhaStatus, ContatoStatus, ConversaStatus, MensagemTipo


# ── Campanha ─────────────────────────────────────────────────────────────────

class CampanhaCreate(BaseModel):
    nome: str
    rate_limit_por_hora: int = 30
    horario_inicio: int = 8
    horario_fim: int = 20
    instancias_ids: list[int] | None = None
    data_source: dict | None = None


class CampanhaUpdate(BaseModel):
    nome: str | None = None
    rate_limit_por_hora: int | None = None
    horario_inicio: int | None = None
    horario_fim: int | None = None
    instancias_ids: list[int] | None = None
    data_source: dict | None = None


class CampanhaPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    nome: str
    status: CampanhaStatus
    data_source: dict | None
    instancias_ids: list[int] | None
    rate_limit_por_hora: int
    horario_inicio: int
    horario_fim: int
    created_at: datetime
    updated_at: datetime
    # stats (computed)
    total_contatos: int = 0
    pendentes: int = 0
    enviados: int = 0
    falhos: int = 0


# ── Template ──────────────────────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    conteudo: str


class TemplateMensagemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campanha_id: int
    conteudo: str
    created_at: datetime


# ── Contato ───────────────────────────────────────────────────────────────────

class ContatoCreate(BaseModel):
    numero: str
    nome: str | None = None
    variaveis: dict | None = None


class ContatoBulkCreate(BaseModel):
    numeros: list[str]


class ContatoPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campanha_id: int
    numero: str
    nome: str | None
    variaveis: dict | None
    status: ContatoStatus
    instancia_id: int | None
    enviado_em: datetime | None
    erro: str | None
    created_at: datetime


# ── Conversa ──────────────────────────────────────────────────────────────────

class ConversaPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    instancia_id: int
    numero: str
    nome: str | None
    status: ConversaStatus
    contato_campanha_id: int | None
    created_at: datetime
    updated_at: datetime
    ultima_mensagem: str | None = None


# ── Mensagem ──────────────────────────────────────────────────────────────────

class MensagemCreate(BaseModel):
    conteudo: str


class MensagemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversa_id: int
    conteudo: str
    tipo: MensagemTipo
    timestamp: datetime
    evolution_id: str | None


# ── Status update ─────────────────────────────────────────────────────────────

class ConversaStatusUpdate(BaseModel):
    status: ConversaStatus

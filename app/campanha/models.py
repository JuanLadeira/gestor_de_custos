import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.whatsapp.models import WhatsappInstancia


class CampanhaStatus(str, enum.Enum):
    RASCUNHO = "RASCUNHO"
    ATIVA = "ATIVA"
    PAUSADA = "PAUSADA"
    CONCLUIDA = "CONCLUIDA"


class ContatoStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    ENVIANDO = "ENVIANDO"
    ENVIADO = "ENVIADO"
    FALHOU = "FALHOU"
    RESPONDEU = "RESPONDEU"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"


class ConversaStatus(str, enum.Enum):
    AGUARDANDO = "AGUARDANDO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    ENCERRADA = "ENCERRADA"


class MensagemTipo(str, enum.Enum):
    ENVIADA = "ENVIADA"
    RECEBIDA = "RECEBIDA"


class Campanha(Base):
    __tablename__ = "campanha"

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[CampanhaStatus] = mapped_column(
        Enum(CampanhaStatus, name="campanhastatus"),
        default=CampanhaStatus.RASCUNHO,
        nullable=False,
    )
    data_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    instancias_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    rate_limit_por_hora: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    horario_inicio: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    horario_fim: Mapped[int] = mapped_column(Integer, default=20, nullable=False)

    templates: Mapped[list["TemplateMensagem"]] = relationship(
        back_populates="campanha",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contatos: Mapped[list["ContatoCampanha"]] = relationship(
        back_populates="campanha",
        cascade="all, delete-orphan",
    )


class TemplateMensagem(Base):
    __tablename__ = "template_mensagem"

    campanha_id: Mapped[int] = mapped_column(
        ForeignKey("campanha.id", ondelete="CASCADE"), nullable=False
    )
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)

    campanha: Mapped["Campanha"] = relationship(back_populates="templates")


class ContatoCampanha(Base):
    __tablename__ = "contato_campanha"

    campanha_id: Mapped[int] = mapped_column(
        ForeignKey("campanha.id", ondelete="CASCADE"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(30), nullable=False)
    nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    variaveis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[ContatoStatus] = mapped_column(
        Enum(ContatoStatus, name="contatostatus"),
        default=ContatoStatus.PENDENTE,
        nullable=False,
    )
    instancia_id: Mapped[int | None] = mapped_column(
        ForeignKey("whatsapp_instancia.id", ondelete="SET NULL"), nullable=True
    )
    enviado_em: Mapped[datetime | None] = mapped_column(nullable=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)

    campanha: Mapped["Campanha"] = relationship(back_populates="contatos")
    instancia: Mapped["WhatsappInstancia | None"] = relationship(lazy="selectin")


class Conversa(Base):
    __tablename__ = "conversa"

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    instancia_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_instancia.id", ondelete="CASCADE"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(30), nullable=False)
    nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[ConversaStatus] = mapped_column(
        Enum(ConversaStatus, name="conversastatus"),
        default=ConversaStatus.AGUARDANDO,
        nullable=False,
    )
    contato_campanha_id: Mapped[int | None] = mapped_column(
        ForeignKey("contato_campanha.id", ondelete="SET NULL"), nullable=True
    )

    instancia: Mapped["WhatsappInstancia"] = relationship(lazy="selectin")
    mensagens: Mapped[list["MensagemConversa"]] = relationship(
        back_populates="conversa",
        cascade="all, delete-orphan",
        order_by="MensagemConversa.timestamp",
        lazy="selectin",
    )


class MensagemConversa(Base):
    __tablename__ = "mensagem_conversa"

    conversa_id: Mapped[int] = mapped_column(
        ForeignKey("conversa.id", ondelete="CASCADE"), nullable=False
    )
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[MensagemTipo] = mapped_column(
        Enum(MensagemTipo, name="mensagemtipo"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    evolution_id: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)

    conversa: Mapped["Conversa"] = relationship(back_populates="mensagens")

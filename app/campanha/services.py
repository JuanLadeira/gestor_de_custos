from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campanha.models import (
    CampanhaStatus,
    ContatoCampanha,
    ContatoStatus,
    Campanha,
    Conversa,
    ConversaStatus,
    MensagemConversa,
    MensagemTipo,
    TemplateMensagem,
)
from app.campanha.schemas import (
    CampanhaCreate,
    CampanhaUpdate,
    ContatoCreate,
    MensagemCreate,
)
from app.database.session import AsyncDBSession
from app.whatsapp.client import EvolutionClientDep
from app.whatsapp.models import WhatsappInstancia
from app.whatsapp.schemas import MensagemTextoRequest


class CampanhaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, tenant_id: int) -> list[Campanha]:
        result = await self.session.execute(
            select(Campanha).where(Campanha.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, campanha_id: int, tenant_id: int) -> Campanha | None:
        result = await self.session.execute(
            select(Campanha).where(
                Campanha.id == campanha_id, Campanha.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, tenant_id: int, data: CampanhaCreate) -> Campanha:
        campanha = Campanha(
            tenant_id=tenant_id,
            nome=data.nome,
            rate_limit_por_hora=data.rate_limit_por_hora,
            horario_inicio=data.horario_inicio,
            horario_fim=data.horario_fim,
            instancias_ids=data.instancias_ids,
            data_source=data.data_source,
        )
        self.session.add(campanha)
        await self.session.flush()
        await self.session.refresh(campanha)
        return campanha

    async def update(self, campanha: Campanha, data: CampanhaUpdate) -> Campanha:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(campanha, field, value)
        await self.session.flush()
        await self.session.refresh(campanha)
        return campanha

    async def delete(self, campanha: Campanha) -> None:
        await self.session.delete(campanha)

    async def set_status(self, campanha: Campanha, status: CampanhaStatus) -> Campanha:
        campanha.status = status
        await self.session.flush()
        await self.session.refresh(campanha)
        return campanha

    # ── Templates ────────────────────────────────────────────────────

    async def add_template(self, campanha_id: int, conteudo: str) -> TemplateMensagem:
        tmpl = TemplateMensagem(campanha_id=campanha_id, conteudo=conteudo)
        self.session.add(tmpl)
        await self.session.flush()
        await self.session.refresh(tmpl)
        return tmpl

    async def get_template(self, template_id: int) -> TemplateMensagem | None:
        return await self.session.get(TemplateMensagem, template_id)

    async def delete_template(self, template: TemplateMensagem) -> None:
        await self.session.delete(template)

    # ── Contatos ─────────────────────────────────────────────────────

    async def get_contatos(self, campanha_id: int) -> list[ContatoCampanha]:
        result = await self.session.execute(
            select(ContatoCampanha).where(ContatoCampanha.campanha_id == campanha_id)
        )
        return list(result.scalars().all())

    async def add_contato(self, campanha_id: int, data: ContatoCreate) -> ContatoCampanha:
        contato = ContatoCampanha(
            campanha_id=campanha_id,
            numero=data.numero,
            nome=data.nome,
            variaveis=data.variaveis,
        )
        self.session.add(contato)
        await self.session.flush()
        await self.session.refresh(contato)
        return contato

    async def bulk_add_contatos(self, campanha_id: int, numeros: list[str]) -> list[ContatoCampanha]:
        contatos = [
            ContatoCampanha(campanha_id=campanha_id, numero=n.strip())
            for n in numeros
            if n.strip()
        ]
        self.session.add_all(contatos)
        await self.session.flush()
        for c in contatos:
            await self.session.refresh(c)
        return contatos

    async def get_contato(self, contato_id: int) -> ContatoCampanha | None:
        return await self.session.get(ContatoCampanha, contato_id)

    async def delete_contato(self, contato: ContatoCampanha) -> None:
        await self.session.delete(contato)

    async def contar_contatos(self, campanha_id: int) -> dict:
        result = await self.session.execute(
            select(ContatoCampanha.status, func.count().label("qtd"))
            .where(ContatoCampanha.campanha_id == campanha_id)
            .group_by(ContatoCampanha.status)
        )
        contagens = {row.status: row.qtd for row in result}
        total = sum(contagens.values())
        return {
            "total_contatos": total,
            "pendentes": contagens.get(ContatoStatus.PENDENTE, 0),
            "enviados": contagens.get(ContatoStatus.ENVIADO, 0),
            "falhos": contagens.get(ContatoStatus.FALHOU, 0),
        }


class InboxService:
    def __init__(self, session: AsyncSession, client: httpx.AsyncClient):
        self.session = session
        self.client = client

    async def get_conversas(
        self, tenant_id: int, status: ConversaStatus | None = None
    ) -> list[Conversa]:
        q = select(Conversa).where(Conversa.tenant_id == tenant_id)
        if status:
            q = q.where(Conversa.status == status)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_conversa(self, conversa_id: int, tenant_id: int) -> Conversa | None:
        result = await self.session.execute(
            select(Conversa).where(
                Conversa.id == conversa_id, Conversa.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def get_mensagens(self, conversa_id: int) -> list[MensagemConversa]:
        result = await self.session.execute(
            select(MensagemConversa)
            .where(MensagemConversa.conversa_id == conversa_id)
            .order_by(MensagemConversa.timestamp)
        )
        return list(result.scalars().all())

    async def update_status(self, conversa: Conversa, status: ConversaStatus) -> Conversa:
        conversa.status = status
        await self.session.flush()
        await self.session.refresh(conversa)
        return conversa

    async def upsert_from_webhook(
        self,
        tenant_id: int,
        instancia_id: int,
        numero: str,
        conteudo: str,
        evolution_id: str | None,
    ) -> tuple[Conversa, MensagemConversa]:
        # Deduplicate by evolution_id
        if evolution_id:
            existing_result = await self.session.execute(
                select(MensagemConversa).where(MensagemConversa.evolution_id == evolution_id)
            )
            existing_msg = existing_result.scalar_one_or_none()
            if existing_msg:
                conversa = await self.session.get(Conversa, existing_msg.conversa_id)
                return conversa, existing_msg

        # Find or create conversa
        result = await self.session.execute(
            select(Conversa).where(
                Conversa.tenant_id == tenant_id,
                Conversa.instancia_id == instancia_id,
                Conversa.numero == numero,
                Conversa.status != ConversaStatus.ENCERRADA,
            )
        )
        conversa = result.scalar_one_or_none()
        if not conversa:
            conversa = Conversa(
                tenant_id=tenant_id,
                instancia_id=instancia_id,
                numero=numero,
                status=ConversaStatus.AGUARDANDO,
            )
            self.session.add(conversa)
            await self.session.flush()
            await self.session.refresh(conversa)

        msg = MensagemConversa(
            conversa_id=conversa.id,
            conteudo=conteudo,
            tipo=MensagemTipo.RECEBIDA,
            timestamp=datetime.now(timezone.utc),
            evolution_id=evolution_id,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return conversa, msg

    async def enviar_mensagem(
        self, conversa: Conversa, data: MensagemCreate
    ) -> MensagemConversa:
        instancia: WhatsappInstancia = conversa.instancia
        r = await self.client.post(
            f"/message/sendText/{instancia.instance_name}",
            json={"number": conversa.numero, "text": data.conteudo},
        )
        r.raise_for_status()

        msg = MensagemConversa(
            conversa_id=conversa.id,
            conteudo=data.conteudo,
            tipo=MensagemTipo.ENVIADA,
            timestamp=datetime.now(timezone.utc),
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg


def get_campanha_service(session: AsyncDBSession) -> CampanhaService:
    return CampanhaService(session)


def get_inbox_service(client: EvolutionClientDep, session: AsyncDBSession) -> InboxService:
    return InboxService(session, client)


CampanhaServiceDep = Annotated[CampanhaService, Depends(get_campanha_service)]
InboxServiceDep = Annotated[InboxService, Depends(get_inbox_service)]

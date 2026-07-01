from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.campanha.models import CampanhaStatus, ConversaStatus
from app.campanha.schemas import (
    CampanhaCreate,
    CampanhaPublic,
    CampanhaUpdate,
    ContatoBulkCreate,
    ContatoCreate,
    ContatoPublic,
    ConversaPublic,
    ConversaStatusUpdate,
    MensagemCreate,
    MensagemPublic,
    TemplateMensagemPublic,
    TemplateCreate,
)
from app.campanha.services import CampanhaServiceDep, InboxServiceDep

router = APIRouter(tags=["Campanhas"])


async def _campanha_or_404(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    c = await service.get_by_id(campanha_id, current_user.tenant_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return c


async def _conversa_or_404(conversa_id: int, current_user: CurrentUser, service: InboxServiceDep):
    c = await service.get_conversa(conversa_id, current_user.tenant_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return c


async def _build_campanha_public(campanha, service: CampanhaServiceDep) -> CampanhaPublic:
    stats = await service.contar_contatos(campanha.id)
    data = CampanhaPublic.model_validate(campanha)
    data.total_contatos = stats["total_contatos"]
    data.pendentes = stats["pendentes"]
    data.enviados = stats["enviados"]
    data.falhos = stats["falhos"]
    return data


# ── Campanhas ─────────────────────────────────────────────────────────────────

@router.get("/api/campanhas", response_model=list[CampanhaPublic],
            dependencies=[Depends(require("campanha:read"))])
async def listar_campanhas(current_user: CurrentUser, service: CampanhaServiceDep):
    campanhas = await service.get_all(current_user.tenant_id)
    result = []
    for c in campanhas:
        result.append(await _build_campanha_public(c, service))
    return result


@router.post("/api/campanhas", response_model=CampanhaPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("campanha:create"))])
async def criar_campanha(data: CampanhaCreate, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await service.create(current_user.tenant_id, data)
    return await _build_campanha_public(campanha, service)


@router.get("/api/campanhas/{campanha_id}", response_model=CampanhaPublic,
            dependencies=[Depends(require("campanha:read"))])
async def obter_campanha(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    return await _build_campanha_public(campanha, service)


@router.put("/api/campanhas/{campanha_id}", response_model=CampanhaPublic,
            dependencies=[Depends(require("campanha:update"))])
async def atualizar_campanha(
    campanha_id: int, data: CampanhaUpdate, current_user: CurrentUser, service: CampanhaServiceDep
):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    campanha = await service.update(campanha, data)
    return await _build_campanha_public(campanha, service)


@router.delete("/api/campanhas/{campanha_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("campanha:delete"))])
async def deletar_campanha(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    await service.delete(campanha)


@router.post("/api/campanhas/{campanha_id}/ativar", response_model=CampanhaPublic,
             dependencies=[Depends(require("campanha:activate"))])
async def ativar_campanha(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    campanha = await service.set_status(campanha, CampanhaStatus.ATIVA)
    if campanha.data_source:
        from app.campanha.tasks import resolver_variaveis_campanha
        resolver_variaveis_campanha.delay(campanha.id)
    return await _build_campanha_public(campanha, service)


@router.post("/api/campanhas/{campanha_id}/pausar", response_model=CampanhaPublic,
             dependencies=[Depends(require("campanha:activate"))])
async def pausar_campanha(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    campanha = await service.set_status(campanha, CampanhaStatus.PAUSADA)
    return await _build_campanha_public(campanha, service)


@router.post("/api/campanhas/{campanha_id}/concluir", response_model=CampanhaPublic,
             dependencies=[Depends(require("campanha:activate"))])
async def concluir_campanha(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    campanha = await service.set_status(campanha, CampanhaStatus.CONCLUIDA)
    return await _build_campanha_public(campanha, service)


# ── Templates ─────────────────────────────────────────────────────────────────

@router.get("/api/campanhas/{campanha_id}/templates", response_model=list[TemplateMensagemPublic],
            dependencies=[Depends(require("campanha:read"))])
async def listar_templates(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    campanha = await _campanha_or_404(campanha_id, current_user, service)
    return campanha.templates


@router.post(
    "/api/campanhas/{campanha_id}/templates",
    response_model=TemplateMensagemPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require("campanha:update"))],
)
async def adicionar_template(
    campanha_id: int, data: TemplateCreate, current_user: CurrentUser, service: CampanhaServiceDep
):
    await _campanha_or_404(campanha_id, current_user, service)
    return await service.add_template(campanha_id, data.conteudo)


@router.delete("/api/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("campanha:update"))])
async def deletar_template(template_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    tmpl = await service.get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    # verify ownership via campanha
    campanha = await service.get_by_id(tmpl.campanha_id, current_user.tenant_id)
    if not campanha:
        raise HTTPException(status_code=403, detail="Acesso negado")
    await service.delete_template(tmpl)


# ── Contatos ──────────────────────────────────────────────────────────────────

@router.get("/api/campanhas/{campanha_id}/contatos", response_model=list[ContatoPublic],
            dependencies=[Depends(require("campanha:read"))])
async def listar_contatos(campanha_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    await _campanha_or_404(campanha_id, current_user, service)
    return await service.get_contatos(campanha_id)


@router.post(
    "/api/campanhas/{campanha_id}/contatos",
    response_model=ContatoPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require("campanha:update"))],
)
async def adicionar_contato(
    campanha_id: int, data: ContatoCreate, current_user: CurrentUser, service: CampanhaServiceDep
):
    await _campanha_or_404(campanha_id, current_user, service)
    return await service.add_contato(campanha_id, data)


@router.post(
    "/api/campanhas/{campanha_id}/contatos/bulk",
    response_model=list[ContatoPublic],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require("campanha:update"))],
)
async def bulk_contatos(
    campanha_id: int, data: ContatoBulkCreate, current_user: CurrentUser, service: CampanhaServiceDep
):
    await _campanha_or_404(campanha_id, current_user, service)
    return await service.bulk_add_contatos(campanha_id, data.numeros)


@router.delete("/api/contatos/{contato_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("campanha:update"))])
async def deletar_contato(contato_id: int, current_user: CurrentUser, service: CampanhaServiceDep):
    contato = await service.get_contato(contato_id)
    if not contato:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    campanha = await service.get_by_id(contato.campanha_id, current_user.tenant_id)
    if not campanha:
        raise HTTPException(status_code=403, detail="Acesso negado")
    await service.delete_contato(contato)


# ── Inbox ─────────────────────────────────────────────────────────────────────

@router.get("/api/conversas", response_model=list[ConversaPublic],
            dependencies=[Depends(require("inbox:read"))])
async def listar_conversas(
    current_user: CurrentUser,
    service: InboxServiceDep,
    status_filter: ConversaStatus | None = None,
):
    conversas = await service.get_conversas(current_user.tenant_id, status_filter)
    result = []
    for c in conversas:
        pub = ConversaPublic.model_validate(c)
        if c.mensagens:
            pub.ultima_mensagem = c.mensagens[-1].conteudo
        result.append(pub)
    return result


@router.get("/api/conversas/{conversa_id}/mensagens", response_model=list[MensagemPublic],
            dependencies=[Depends(require("inbox:read"))])
async def listar_mensagens(conversa_id: int, current_user: CurrentUser, service: InboxServiceDep):
    await _conversa_or_404(conversa_id, current_user, service)
    return await service.get_mensagens(conversa_id)


@router.post(
    "/api/conversas/{conversa_id}/mensagens",
    response_model=MensagemPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require("inbox:reply"))],
)
async def enviar_mensagem(
    conversa_id: int, data: MensagemCreate, current_user: CurrentUser, service: InboxServiceDep
):
    conversa = await _conversa_or_404(conversa_id, current_user, service)
    return await service.enviar_mensagem(conversa, data)


@router.put("/api/conversas/{conversa_id}/status", response_model=ConversaPublic,
            dependencies=[Depends(require("inbox:manage"))])
async def atualizar_status_conversa(
    conversa_id: int, data: ConversaStatusUpdate, current_user: CurrentUser, service: InboxServiceDep
):
    conversa = await _conversa_or_404(conversa_id, current_user, service)
    conversa = await service.update_status(conversa, data.status)
    pub = ConversaPublic.model_validate(conversa)
    if conversa.mensagens:
        pub.ultima_mensagem = conversa.mensagens[-1].conteudo
    return pub

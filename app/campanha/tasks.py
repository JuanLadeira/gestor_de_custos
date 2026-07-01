import asyncio
import random
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from app.celery_app import celery_app
from app.campanha.models import (
    CampanhaStatus,
    ContatoCampanha,
    ContatoStatus,
    Campanha,
    Conversa,
    ConversaStatus,
    MensagemConversa,
    MensagemTipo,
)
from app.database.session import async_session_factory

# URL base interna — Celery roda no mesmo Docker network
_INTERNAL_BASE_URL = "http://app:8000"


def _build_request_headers(ds: dict, tenant_id: int | None = None) -> dict:
    """Monta headers HTTP a partir do data_source.
    Se use_system_token=True, gera um token de serviço para o owner do tenant.
    """
    headers: dict[str, str] = {}

    # Headers customizados definidos pelo usuário (lista de {key, value})
    for h in ds.get("headers", []):
        k = h.get("key", "").strip()
        v = h.get("value", "").strip()
        if k:
            headers[k] = v

    return headers


async def _get_system_token(session, tenant_id: int) -> str | None:
    """Gera um access token usando o Dono do tenant."""
    try:
        from app.auth.security import create_access_token
        from app.authz.models import RoleProfile
        from app.usuario.models import Usuario

        result = await session.execute(
            select(Usuario)
            .join(RoleProfile, Usuario.role_profile_id == RoleProfile.id)
            .where(
                Usuario.tenant_id == tenant_id,
                RoleProfile.nome == "Dono",
                Usuario.ativo == True,  # noqa: E712
            )
            .limit(1)
        )
        owner = result.scalar_one_or_none()
        if owner:
            return create_access_token({"sub": owner.username})
    except Exception:
        pass
    return None


def _resolve_url(url: str, use_internal: bool) -> str:
    """Se a URL é relativa (/api/...) e use_system_token=True, adiciona o base interno."""
    if use_internal and url.startswith("/"):
        return _INTERNAL_BASE_URL + url
    return url


# ── resolver_variaveis_campanha ───────────────────────────────────────────────

async def _resolver_variaveis(campanha_id: int) -> dict:
    async with async_session_factory() as session:
        campanha = await session.get(Campanha, campanha_id)
        if not campanha or not campanha.data_source:
            return {"status": "skipped", "reason": "no data_source"}

        ds = campanha.data_source
        url = ds.get("url", "")
        method = ds.get("method", "GET").upper()
        mode = ds.get("mode", "bulk")
        chave_contato = ds.get("chave_contato", "telefone")
        mapeamento: dict = ds.get("mapeamento", {})
        use_system_token = ds.get("use_system_token", False)

        # Montar headers base
        headers: dict[str, str] = {}
        for h in ds.get("headers", []):
            k = h.get("key", "").strip()
            v = h.get("value", "").strip()
            if k:
                headers[k] = v

        # Injetar token do sistema se solicitado
        if use_system_token:
            token = await _get_system_token(session, campanha.tenant_id)
            if token:
                headers["Authorization"] = f"Bearer {token}"

        url = _resolve_url(url, use_system_token)

        result = await session.execute(
            select(ContatoCampanha).where(ContatoCampanha.campanha_id == campanha_id)
        )
        contatos = list(result.scalars().all())

        if not contatos:
            return {"status": "ok", "updated": 0}

        try:
            from jsonpath_ng import parse as jp_parse

            if mode == "bulk":
                numeros = [c.numero for c in contatos]
                body_template = ds.get("body_template", "")
                body = body_template.replace("{lista_numeros}", str(numeros)) if body_template else None

                req_headers = {**headers}
                if body:
                    req_headers.setdefault("Content-Type", "application/json")

                async with httpx.AsyncClient(timeout=30) as client:
                    if method == "POST" and body:
                        r = await client.post(url, content=body, headers=req_headers)
                    else:
                        r = await client.request(method, url, headers=req_headers)
                    r.raise_for_status()
                    dados = r.json()

                if isinstance(dados, list):
                    lookup = {str(item.get(chave_contato, "")): item for item in dados}
                else:
                    lookup = {}

                for contato in contatos:
                    item = lookup.get(contato.numero, {})
                    variaveis = _extrair_variaveis(item, mapeamento, jp_parse)
                    # Variáveis padrão (sempre disponíveis)
                    variaveis.setdefault("numero", contato.numero)
                    variaveis.setdefault("nome", contato.nome or "")
                    contato.variaveis = variaveis

            else:  # per_contact
                for contato in contatos:
                    async with httpx.AsyncClient(timeout=30) as client:
                        r = await client.request(
                            method, url,
                            params={"numero": contato.numero},
                            headers=headers,
                        )
                        r.raise_for_status()
                        item = r.json()
                    variaveis = _extrair_variaveis(item, mapeamento, jp_parse)
                    variaveis.setdefault("numero", contato.numero)
                    variaveis.setdefault("nome", contato.nome or "")
                    contato.variaveis = variaveis

            await session.commit()
            return {"status": "ok", "updated": len(contatos)}

        except Exception as e:
            await session.rollback()
            return {"status": "error", "detail": str(e)}


def _extrair_variaveis(item: dict, mapeamento: dict, jp_parse) -> dict:
    variaveis = {}
    for var_name, jsonpath_expr in mapeamento.items():
        try:
            matches = jp_parse(jsonpath_expr).find(item)
            variaveis[var_name] = matches[0].value if matches else None
        except Exception:
            variaveis[var_name] = None
    return variaveis


@celery_app.task(name="app.campanha.tasks.resolver_variaveis_campanha")
def resolver_variaveis_campanha(campanha_id: int) -> dict:
    return asyncio.run(_resolver_variaveis(campanha_id))


# ── processar_campanhas_ativas ────────────────────────────────────────────────

async def _processar_campanhas() -> dict:
    import pytz
    tz = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(tz)
    hora_atual = agora.hour

    async with async_session_factory() as session:
        result = await session.execute(
            select(Campanha).where(Campanha.status == CampanhaStatus.ATIVA)
        )
        campanhas = list(result.scalars().all())

        enfileiradas = 0
        for campanha in campanhas:
            if not (campanha.horario_inicio <= hora_atual < campanha.horario_fim):
                continue

            instancias_ids: list[int] = campanha.instancias_ids or []
            if not instancias_ids:
                continue

            uma_hora_atras = datetime.now(timezone.utc) - timedelta(hours=1)

            melhor_instancia = None
            menor_uso = float("inf")

            for inst_id in instancias_ids:
                r = await session.execute(
                    select(ContatoCampanha).where(
                        ContatoCampanha.campanha_id == campanha.id,
                        ContatoCampanha.instancia_id == inst_id,
                        ContatoCampanha.enviado_em >= uma_hora_atras,
                    )
                )
                uso = len(list(r.scalars().all()))
                if uso < campanha.rate_limit_por_hora and uso < menor_uso:
                    menor_uso = uso
                    melhor_instancia = inst_id

            if melhor_instancia is None:
                continue

            r = await session.execute(
                select(ContatoCampanha)
                .where(
                    ContatoCampanha.campanha_id == campanha.id,
                    ContatoCampanha.status == ContatoStatus.PENDENTE,
                )
                .limit(1)
            )
            contato = r.scalar_one_or_none()

            if not contato:
                continue

            contato.status = ContatoStatus.ENVIANDO
            contato.instancia_id = melhor_instancia
            await session.commit()

            jitter = random.uniform(5, 20)
            enviar_mensagem_contato.apply_async(args=[contato.id], countdown=jitter)
            enfileiradas += 1

        return {"enfileiradas": enfileiradas}


@celery_app.task(name="app.campanha.tasks.processar_campanhas_ativas")
def processar_campanhas_ativas() -> dict:
    return asyncio.run(_processar_campanhas())


# ── enviar_mensagem_contato ───────────────────────────────────────────────────

async def _enviar_mensagem(contato_id: int) -> dict:
    from app.settings import Settings
    from jinja2 import Environment
    from app.whatsapp.models import WhatsappInstancia

    settings = Settings()

    async with async_session_factory() as session:
        contato = await session.get(ContatoCampanha, contato_id)
        if not contato:
            return {"status": "skipped", "reason": "contato not found"}

        campanha = await session.get(Campanha, contato.campanha_id)
        if not campanha or campanha.status != CampanhaStatus.ATIVA:
            contato.status = ContatoStatus.PENDENTE
            await session.commit()
            return {"status": "skipped", "reason": "campaign not active"}

        templates = campanha.templates
        if not templates:
            contato.status = ContatoStatus.FALHOU
            contato.erro = "Nenhum template configurado"
            await session.commit()
            return {"status": "error", "reason": "no templates"}

        template = random.choice(templates)

        # Garante que numero e nome estão sempre disponíveis
        variaveis = dict(contato.variaveis or {})
        variaveis.setdefault("numero", contato.numero)
        variaveis.setdefault("nome", contato.nome or "")

        try:
            jinja_env = Environment()
            mensagem = jinja_env.from_string(template.conteudo).render(**variaveis)
        except Exception as e:
            contato.status = ContatoStatus.FALHOU
            contato.erro = f"Erro no template: {e}"
            await session.commit()
            return {"status": "error", "reason": str(e)}

        instancia_id = contato.instancia_id
        if not instancia_id:
            contato.status = ContatoStatus.FALHOU
            contato.erro = "Instância não definida"
            await session.commit()
            return {"status": "error", "reason": "no instancia"}

        instancia = await session.get(WhatsappInstancia, instancia_id)
        if not instancia:
            contato.status = ContatoStatus.FALHOU
            contato.erro = "Instância não encontrada"
            await session.commit()
            return {"status": "error", "reason": "instancia not found"}

        try:
            async with httpx.AsyncClient(
                base_url=settings.EVOLUTION_API_URL,
                headers={"apikey": settings.EVOLUTION_API_KEY},
                timeout=30,
            ) as client:
                r = await client.post(
                    f"/message/sendText/{instancia.instance_name}",
                    json={"number": contato.numero, "text": mensagem},
                )
                r.raise_for_status()

            contato.status = ContatoStatus.ENVIADO
            contato.enviado_em = datetime.now(timezone.utc)
            contato.erro = None

            r2 = await session.execute(
                select(Conversa).where(
                    Conversa.tenant_id == campanha.tenant_id,
                    Conversa.instancia_id == instancia_id,
                    Conversa.numero == contato.numero,
                    Conversa.status != ConversaStatus.ENCERRADA,
                )
            )
            conversa = r2.scalar_one_or_none()

            if not conversa:
                conversa = Conversa(
                    tenant_id=campanha.tenant_id,
                    instancia_id=instancia_id,
                    numero=contato.numero,
                    nome=contato.nome,
                    status=ConversaStatus.AGUARDANDO,
                    contato_campanha_id=contato.id,
                )
                session.add(conversa)
                await session.flush()

            msg = MensagemConversa(
                conversa_id=conversa.id,
                conteudo=mensagem,
                tipo=MensagemTipo.ENVIADA,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(msg)
            await session.commit()
            return {"status": "ok", "contato_id": contato_id}

        except Exception as e:
            contato.status = ContatoStatus.FALHOU
            contato.erro = str(e)
            await session.commit()
            return {"status": "error", "reason": str(e)}


@celery_app.task(name="app.campanha.tasks.enviar_mensagem_contato")
def enviar_mensagem_contato(contato_id: int) -> dict:
    return asyncio.run(_enviar_mensagem(contato_id))

import httpx
import pytest
import respx
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, get_password_hash
from app.settings import Settings
from app.tenant.models import Tenant
from app.usuario.models import Usuario, UsuarioRole
from app.whatsapp.models import ConexaoStatus, WhatsappInstancia
from app.whatsapp.schemas import InstanciaCreate, MensagemTextoRequest
from app.whatsapp.services import WhatsappService

settings = Settings()


# ── Local async fixtures (bypass factory_boy async issues) ───────────────────


@pytest.fixture
async def tenant_obj(session: AsyncSession):
    t = Tenant(nome="Tenant Whatsapp Teste")
    session.add(t)
    await session.flush()
    return t


@pytest.fixture
async def instancia_obj(session: AsyncSession, tenant_obj: Tenant):
    inst = WhatsappInstancia(
        instance_name="instancia-fixture",
        tenant_id=tenant_obj.id,
        status=ConexaoStatus.CRIADA,
    )
    session.add(inst)
    await session.flush()
    return inst


@pytest.fixture
async def instancia_conectada(session: AsyncSession, tenant_obj: Tenant):
    inst = WhatsappInstancia(
        instance_name="instancia-conectada",
        tenant_id=tenant_obj.id,
        status=ConexaoStatus.CONECTADA,
    )
    session.add(inst)
    await session.flush()
    return inst


@pytest.fixture
async def usuario_owner(session: AsyncSession, tenant_obj: Tenant):
    u = Usuario(
        username="wa_owner",
        email="wa_owner@test.com",
        password=get_password_hash("senha123"),
        nome="WA Owner",
        role=UsuarioRole.OWNER,
        tenant_id=tenant_obj.id,
    )
    session.add(u)
    await session.flush()
    return u


@pytest.fixture
def auth_token(usuario_owner: Usuario):
    return create_access_token({"sub": usuario_owner.username})


@pytest.fixture
def wa_auth_headers(auth_token: str):
    return {"Authorization": f"Bearer {auth_token}"}


# ── Service tests ─────────────────────────────────────────────────────────────


@pytest.mark.whatsapp
class TestWhatsappService:
    """Testes unitários do service com respx."""

    async def test_criar_instancia_salva_no_banco(self, session, tenant_obj):
        with respx.mock(base_url="http://evolution") as mock:
            mock.post("/instance/create").mock(
                return_value=httpx.Response(201, json={"instance": {"status": "created"}})
            )
            async with httpx.AsyncClient(base_url="http://evolution") as client:
                service = WhatsappService(client, session)
                instancia = await service.criar_instancia(
                    tenant_obj.id, InstanciaCreate(instance_name="teste")
                )
        assert instancia.id is not None
        assert instancia.tenant_id == tenant_obj.id
        assert instancia.status == ConexaoStatus.CRIADA

    async def test_listar_instancias_filtra_por_tenant(self, session, instancia_obj, tenant_obj):
        async with httpx.AsyncClient(base_url="http://evolution") as client:
            service = WhatsappService(client, session)
            lista = await service.listar_instancias(tenant_obj.id)
        assert any(i.id == instancia_obj.id for i in lista)

    async def test_obter_instancia_existente(self, session, instancia_obj, tenant_obj):
        async with httpx.AsyncClient(base_url="http://evolution") as client:
            service = WhatsappService(client, session)
            found = await service.obter_instancia(instancia_obj.id, tenant_obj.id)
        assert found is not None
        assert found.id == instancia_obj.id

    async def test_obter_instancia_inexistente_retorna_none(self, session, tenant_obj):
        async with httpx.AsyncClient(base_url="http://evolution") as client:
            service = WhatsappService(client, session)
            found = await service.obter_instancia(99999, tenant_obj.id)
        assert found is None

    async def test_sincronizar_status_conectada(self, session, instancia_obj):
        with respx.mock(base_url="http://evolution") as mock:
            mock.get(f"/instance/connectionState/{instancia_obj.instance_name}").mock(
                return_value=httpx.Response(200, json={"state": "open"})
            )
            async with httpx.AsyncClient(base_url="http://evolution") as client:
                service = WhatsappService(client, session)
                atualizada = await service.sincronizar_status(instancia_obj)
        assert atualizada.status == ConexaoStatus.CONECTADA

    async def test_sincronizar_status_desconectada(self, session, instancia_obj):
        with respx.mock(base_url="http://evolution") as mock:
            mock.get(f"/instance/connectionState/{instancia_obj.instance_name}").mock(
                return_value=httpx.Response(200, json={"state": "close"})
            )
            async with httpx.AsyncClient(base_url="http://evolution") as client:
                service = WhatsappService(client, session)
                atualizada = await service.sincronizar_status(instancia_obj)
        assert atualizada.status == ConexaoStatus.DESCONECTADA

    async def test_enviar_texto_sucesso(self, session, instancia_conectada):
        with respx.mock(base_url="http://evolution") as mock:
            mock.post(f"/message/sendText/{instancia_conectada.instance_name}").mock(
                return_value=httpx.Response(200, json={"key": {"id": "abc"}, "status": "PENDING"})
            )
            async with httpx.AsyncClient(base_url="http://evolution") as client:
                service = WhatsappService(client, session)
                result = await service.enviar_texto(
                    instancia_conectada, MensagemTextoRequest(number="5511999999999", text="Olá!")
                )
        assert result["status"] == "PENDING"

    async def test_evolution_api_error_vira_502(self, session, instancia_obj):
        with respx.mock(base_url="http://evolution") as mock:
            mock.post(f"/message/sendText/{instancia_obj.instance_name}").mock(
                return_value=httpx.Response(400, json={"error": "invalid"})
            )
            async with httpx.AsyncClient(base_url="http://evolution") as client:
                service = WhatsappService(client, session)
                with pytest.raises(HTTPException) as exc:
                    await service.enviar_texto(
                        instancia_obj, MensagemTextoRequest(number="invalido", text="x")
                    )
        assert exc.value.status_code == 502

    async def test_deletar_instancia_remove_do_banco(self, session, instancia_obj):
        instancia_id = instancia_obj.id
        with respx.mock(base_url="http://evolution") as mock:
            mock.delete(f"/instance/delete/{instancia_obj.instance_name}").mock(
                return_value=httpx.Response(200, json={"status": "removed"})
            )
            async with httpx.AsyncClient(base_url="http://evolution") as client:
                service = WhatsappService(client, session)
                await service.deletar_instancia(instancia_obj)
        await session.flush()
        session.expunge_all()
        removed = await session.get(WhatsappInstancia, instancia_id)
        assert removed is None


# ── Router tests ──────────────────────────────────────────────────────────────


@pytest.mark.whatsapp
class TestWhatsappRouter:
    """Testes de integração via endpoint HTTP."""

    async def test_listar_instancias_requer_auth(self, client: AsyncClient):
        response = await client.get("/api/whatsapp/instancias")
        assert response.status_code == 401

    async def test_webhook_publico(self, client: AsyncClient):
        response = await client.post(
            "/api/whatsapp/webhook",
            json={"event": "messages.upsert", "instance": "test", "data": {}},
        )
        assert response.status_code == 200
        assert response.json()["received"] is True

    async def test_criar_instancia_via_endpoint(
        self, client: AsyncClient, wa_auth_headers, usuario_owner
    ):
        with respx.mock(base_url=settings.EVOLUTION_API_URL) as mock:
            mock.post("/instance/create").mock(
                return_value=httpx.Response(201, json={"instance": {"status": "created"}})
            )
            response = await client.post(
                "/api/whatsapp/instancias",
                json={"instance_name": "meu-whatsapp"},
                headers=wa_auth_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert data["instance_name"] == "meu-whatsapp"
        assert data["tenant_id"] == usuario_owner.tenant_id

    async def test_listar_instancias_retorna_lista(
        self, client: AsyncClient, wa_auth_headers, instancia_obj
    ):
        response = await client.get("/api/whatsapp/instancias", headers=wa_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    async def test_instancia_nao_encontrada_retorna_404(
        self, client: AsyncClient, wa_auth_headers
    ):
        with respx.mock(base_url=settings.EVOLUTION_API_URL):
            response = await client.get(
                "/api/whatsapp/instancias/99999/status", headers=wa_auth_headers
            )
        assert response.status_code == 404

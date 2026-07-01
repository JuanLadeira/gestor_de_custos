import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.auth.security import get_password_hash
from app.database.base import Base
from app.database.session import get_async_session
from app.main import app
from app.tests.factories.tenant import TenantFactory
from app.tests.factories.usuario import UsuarioFactory
from app.tests.factories.whatsapp_instancia import WhatsappInstanciaFactory


@pytest.fixture(scope="function")
async def async_engine():
    """Create an async engine connected to a test container."""
    with PostgresContainer("postgres:16", driver="asyncpg") as postgres:
        # Convert the connection URL to async format
        url = postgres.get_connection_url()
        async_url = url.replace("postgresql://", "postgresql+asyncpg://")

        engine = create_async_engine(async_url, echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()


@pytest.fixture(scope="function")
async def session(async_engine):
    """Provide an async session for tests."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def client(session):
    """Provide an async test client with dependency override."""

    async def get_session_override():
        yield session

    app.dependency_overrides[get_async_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def tenant_factory(session) -> type[TenantFactory]:
    """Fixture that provides TenantFactory configured with the test session."""
    TenantFactory._meta.sqlalchemy_session = session
    return TenantFactory


@pytest.fixture
def usuario_factory(session) -> type[UsuarioFactory]:
    """Fixture that provides UsuarioFactory configured with the test session."""
    UsuarioFactory._meta.sqlalchemy_session = session
    return UsuarioFactory


@pytest.fixture
async def tenant(tenant_factory):
    """Create a test tenant."""
    return tenant_factory(nome="Casa Teste", descricao="Tenant para testes")


@pytest.fixture
async def usuario(usuario_factory, tenant):
    """Create a test usuario."""
    senha = "teste123"
    return usuario_factory(
        username="usuario_teste",
        email="teste@example.com",
        password=get_password_hash(senha),
        nome="Usuario Teste",
        tenant_id=tenant.id,
    )


@pytest.fixture
async def token(client, usuario):
    """Get an access token for the test user."""
    response = await client.post(
        "/auth/login",
        data={"username": usuario.username, "password": "teste123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(token):
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def whatsapp_instancia_factory(session) -> type[WhatsappInstanciaFactory]:
    """Fixture that provides WhatsappInstanciaFactory configured with the test session."""
    WhatsappInstanciaFactory._meta.sqlalchemy_session = session
    return WhatsappInstanciaFactory


from app.authz.service import AuthzService as _AuthzService


async def make_tenant_user(session, *, tenant_nome: str, username: str,
                           profile_nome: str = "Dono"):
    """Create a tenant (seeded with authz) + a user on a given profile.
    Returns (tenant, user)."""
    from app.auth.security import get_password_hash
    from app.tenant.models import Tenant
    from app.usuario.models import Usuario

    svc = _AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome=tenant_nome)
    session.add(tenant)
    await session.flush()
    await svc.seed_tenant_defaults(tenant.id)
    profile = await svc.get_profile_by_nome(tenant.id, profile_nome)
    user = Usuario(
        username=username, email=f"{username}@e.com",
        password=get_password_hash("senha123"), nome=username,
        tenant_id=tenant.id, role_profile_id=profile.id,
    )
    session.add(user)
    await session.flush()
    return tenant, user

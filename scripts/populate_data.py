"""
Script de fixture para popular o banco com dados de teste.

Uso (dentro do container):
    uv run python scripts/populate_data.py

Comportamento:
    - Limpa TODOS os dados do banco (TRUNCATE CASCADE)
    - Recria toda a fixture do zero
    - Idempotente: pode ser rodado quantas vezes quiser
"""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import Admin
from app.assinatura.models import Assinatura, AssinaturaStatus
from app.auth.security import get_password_hash
from app.custo.models import Custo, StatusPagamento, TipoCusto
from app.custo_fixo.models import CustoFixo
from app.database.session import async_session_factory
from app.mes_referencia.models import MesReferencia, StatusMes
from app.pagamento_rateio.models import PagamentoRateio, StatusRateio
from app.plano.models import Plano
from app.tenant.models import Tenant
from app.usuario.models import Usuario, UsuarioRole

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SENHA_PADRAO = "senha123"


def senha(plain: str = SENHA_PADRAO) -> str:
    return get_password_hash(plain)


def dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Limpeza
# ---------------------------------------------------------------------------

TABELAS = [
    "pagamento_rateio",
    "custo",
    "mes_referencia",
    "custo_fixo",
    "assinatura",
    "usuario",
    "tenant",
    "plano",
    "admin",
]


async def limpar_banco(session: AsyncSession) -> None:
    print("🗑️  Limpando banco...")
    tabelas = ", ".join(TABELAS)
    await session.execute(
        text(f"TRUNCATE TABLE {tabelas} RESTART IDENTITY CASCADE")
    )
    print("   OK\n")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

async def criar_admin(session: AsyncSession) -> Admin:
    admin = Admin(
        username="admin",
        email="admin@admin.local",
        password=senha("admin"),
        nome="Administrador",
        ativo=True,
    )
    session.add(admin)
    await session.flush()
    print(f"👤 Admin criado: admin / admin")
    return admin


async def criar_planos(session: AsyncSession) -> dict[str, Plano]:
    planos_data = [
        dict(
            nome="Básico",
            preco_mensal=Decimal("29.90"),
            preco_anual=Decimal("299.00"),
            max_usuarios=3,
            ativo=True,
            features=["Até 3 membros", "Histórico de 3 meses", "Suporte por e-mail"],
        ),
        dict(
            nome="Pro",
            preco_mensal=Decimal("59.90"),
            preco_anual=Decimal("599.00"),
            max_usuarios=10,
            ativo=True,
            features=["Até 10 membros", "Histórico completo", "Custos fixos ilimitados", "Suporte prioritário"],
        ),
        dict(
            nome="Premium",
            preco_mensal=Decimal("99.90"),
            preco_anual=Decimal("999.00"),
            max_usuarios=30,
            ativo=True,
            features=["Membros ilimitados", "Histórico completo", "Relatórios avançados", "Suporte 24/7"],
        ),
    ]

    planos = {}
    for data in planos_data:
        plano = Plano(**data)
        session.add(plano)
        await session.flush()
        planos[data["nome"]] = plano
        print(f"📦 Plano criado: {plano.nome} (R$ {plano.preco_mensal}/mês)")

    return planos


async def criar_tenant_juan(
    session: AsyncSession, planos: dict[str, Plano]
) -> None:
    tenant = Tenant(nome="Casa do Juan", descricao="Apartamento compartilhado - 3 moradores")
    session.add(tenant)
    await session.flush()

    juan = Usuario(username="juan", email="juan@demo.com", password=senha(), nome="Juan Silva", role=UsuarioRole.OWNER, tenant_id=tenant.id)
    pedro = Usuario(username="pedro", email="pedro@demo.com", password=senha(), nome="Pedro Souza", role=UsuarioRole.MEMBER, tenant_id=tenant.id)
    maria = Usuario(username="maria", email="maria@demo.com", password=senha(), nome="Maria Oliveira", role=UsuarioRole.MEMBER, tenant_id=tenant.id)
    session.add_all([juan, pedro, maria])
    await session.flush()

    session.add(Assinatura(tenant_id=tenant.id, plano_id=planos["Pro"].id, status=AssinaturaStatus.ATIVA, data_inicio=dt(2026, 1, 1), data_proxima_cobranca=dt(2026, 4, 1)))
    await session.flush()

    cf_aluguel = CustoFixo(tenant_id=tenant.id, descricao="Aluguel", valor=Decimal("2500.00"), dia_vencimento=5, ativo=True)
    cf_internet = CustoFixo(tenant_id=tenant.id, descricao="Internet", valor=Decimal("120.00"), dia_vencimento=10, ativo=True)
    cf_energia = CustoFixo(tenant_id=tenant.id, descricao="Energia Elétrica", valor=Decimal("350.00"), dia_vencimento=15, ativo=True)
    cf_agua = CustoFixo(tenant_id=tenant.id, descricao="Água", valor=Decimal("80.00"), dia_vencimento=20, ativo=True)
    session.add_all([cf_aluguel, cf_internet, cf_energia, cf_agua])
    await session.flush()

    rateio = [(juan, Decimal("40.00")), (pedro, Decimal("35.00")), (maria, Decimal("25.00"))]

    # Jan/2026 — FECHADO, tudo pago
    mes_jan = MesReferencia(tenant_id=tenant.id, ano=2026, mes=1, status=StatusMes.FECHADO)
    session.add(mes_jan)
    await session.flush()
    custos_jan = [
        Custo(descricao="Aluguel", valor=Decimal("2500.00"), data_vencimento=date(2026, 1, 5), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_jan.id, custo_fixo_origem_id=cf_aluguel.id),
        Custo(descricao="Internet", valor=Decimal("120.00"), data_vencimento=date(2026, 1, 10), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_jan.id, custo_fixo_origem_id=cf_internet.id),
        Custo(descricao="Energia Elétrica", valor=Decimal("350.00"), data_vencimento=date(2026, 1, 15), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_jan.id, custo_fixo_origem_id=cf_energia.id),
        Custo(descricao="Água", valor=Decimal("80.00"), data_vencimento=date(2026, 1, 20), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_jan.id, custo_fixo_origem_id=cf_agua.id),
        Custo(descricao="Supermercado", valor=Decimal("680.00"), data_vencimento=date(2026, 1, 28), tipo=TipoCusto.VARIAVEL, status=StatusPagamento.PAGO, mes_referencia_id=mes_jan.id),
    ]
    session.add_all(custos_jan)
    await session.flush()
    for custo in custos_jan:
        for u, pct in rateio:
            session.add(PagamentoRateio(custo_id=custo.id, usuario_id=u.id, porcentagem=pct, valor_calculado=(custo.valor * pct / 100).quantize(Decimal("0.01")), status=StatusRateio.PAGO))
    await session.flush()

    # Fev/2026 — FECHADO, fixos pagos / variável pendente
    mes_fev = MesReferencia(tenant_id=tenant.id, ano=2026, mes=2, status=StatusMes.FECHADO)
    session.add(mes_fev)
    await session.flush()
    custos_fev = [
        Custo(descricao="Aluguel", valor=Decimal("2500.00"), data_vencimento=date(2026, 2, 5), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id, custo_fixo_origem_id=cf_aluguel.id),
        Custo(descricao="Internet", valor=Decimal("120.00"), data_vencimento=date(2026, 2, 10), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id, custo_fixo_origem_id=cf_internet.id),
        Custo(descricao="Energia Elétrica", valor=Decimal("410.00"), data_vencimento=date(2026, 2, 15), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id, custo_fixo_origem_id=cf_energia.id),
        Custo(descricao="Água", valor=Decimal("80.00"), data_vencimento=date(2026, 2, 20), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id, custo_fixo_origem_id=cf_agua.id),
        Custo(descricao="Netflix + Spotify", valor=Decimal("75.00"), data_vencimento=date(2026, 2, 25), tipo=TipoCusto.VARIAVEL, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_fev.id),
    ]
    session.add_all(custos_fev)
    await session.flush()
    for custo, st in zip(custos_fev, [StatusRateio.PAGO]*4 + [StatusRateio.PENDENTE]):
        for u, pct in rateio:
            session.add(PagamentoRateio(custo_id=custo.id, usuario_id=u.id, porcentagem=pct, valor_calculado=(custo.valor * pct / 100).quantize(Decimal("0.01")), status=st))
    await session.flush()

    # Mar/2026 — ABERTO, tudo pendente
    mes_mar = MesReferencia(tenant_id=tenant.id, ano=2026, mes=3, status=StatusMes.ABERTO)
    session.add(mes_mar)
    await session.flush()
    custos_mar = [
        Custo(descricao="Aluguel", valor=Decimal("2500.00"), data_vencimento=date(2026, 3, 5), tipo=TipoCusto.FIXO, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id, custo_fixo_origem_id=cf_aluguel.id),
        Custo(descricao="Internet", valor=Decimal("120.00"), data_vencimento=date(2026, 3, 10), tipo=TipoCusto.FIXO, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id, custo_fixo_origem_id=cf_internet.id),
        Custo(descricao="Energia Elétrica", valor=Decimal("380.00"), data_vencimento=date(2026, 3, 15), tipo=TipoCusto.FIXO, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id, custo_fixo_origem_id=cf_energia.id),
        Custo(descricao="Água", valor=Decimal("80.00"), data_vencimento=date(2026, 3, 20), tipo=TipoCusto.FIXO, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id, custo_fixo_origem_id=cf_agua.id),
        Custo(descricao="Gás", valor=Decimal("55.00"), data_vencimento=date(2026, 3, 22), tipo=TipoCusto.VARIAVEL, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id),
    ]
    session.add_all(custos_mar)
    await session.flush()
    for custo in custos_mar:
        for u, pct in rateio:
            session.add(PagamentoRateio(custo_id=custo.id, usuario_id=u.id, porcentagem=pct, valor_calculado=(custo.valor * pct / 100).quantize(Decimal("0.01")), status=StatusRateio.PENDENTE))
    await session.flush()

    print(f"🏠 Tenant criado: {tenant.nome}")
    print(f"   Usuários: juan (OWNER), pedro (MEMBER), maria (MEMBER)  — senha: {SENHA_PADRAO}")
    print(f"   Assinatura: Pro (ATIVA)")
    print(f"   Meses: Jan/2026 (FECHADO), Fev/2026 (FECHADO), Mar/2026 (ABERTO)")


async def criar_tenant_luana(
    session: AsyncSession, planos: dict[str, Plano]
) -> None:
    tenant = Tenant(nome="Casa da Luana", descricao="Apartamento compartilhado - 2 moradores")
    session.add(tenant)
    await session.flush()

    luana = Usuario(username="luana", email="luana@demo.com", password=senha(), nome="Luana Costa", role=UsuarioRole.OWNER, tenant_id=tenant.id)
    carlos = Usuario(username="carlos", email="carlos@demo.com", password=senha(), nome="Carlos Mendes", role=UsuarioRole.MEMBER, tenant_id=tenant.id)
    session.add_all([luana, carlos])
    await session.flush()

    session.add(Assinatura(tenant_id=tenant.id, plano_id=planos["Básico"].id, status=AssinaturaStatus.ATIVA, data_inicio=dt(2026, 2, 1), data_proxima_cobranca=dt(2026, 4, 1)))
    await session.flush()

    cf_cond = CustoFixo(tenant_id=tenant.id, descricao="Condomínio", valor=Decimal("900.00"), dia_vencimento=10, ativo=True)
    cf_internet = CustoFixo(tenant_id=tenant.id, descricao="Internet", valor=Decimal("100.00"), dia_vencimento=15, ativo=True)
    session.add_all([cf_cond, cf_internet])
    await session.flush()

    rateio = [(luana, Decimal("50.00")), (carlos, Decimal("50.00"))]

    # Fev/2026 — FECHADO, tudo pago
    mes_fev = MesReferencia(tenant_id=tenant.id, ano=2026, mes=2, status=StatusMes.FECHADO)
    session.add(mes_fev)
    await session.flush()
    custos_fev = [
        Custo(descricao="Condomínio", valor=Decimal("900.00"), data_vencimento=date(2026, 2, 10), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id, custo_fixo_origem_id=cf_cond.id),
        Custo(descricao="Internet", valor=Decimal("100.00"), data_vencimento=date(2026, 2, 15), tipo=TipoCusto.FIXO, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id, custo_fixo_origem_id=cf_internet.id),
        Custo(descricao="Supermercado", valor=Decimal("420.00"), data_vencimento=date(2026, 2, 20), tipo=TipoCusto.VARIAVEL, status=StatusPagamento.PAGO, mes_referencia_id=mes_fev.id),
    ]
    session.add_all(custos_fev)
    await session.flush()
    for custo in custos_fev:
        for u, pct in rateio:
            session.add(PagamentoRateio(custo_id=custo.id, usuario_id=u.id, porcentagem=pct, valor_calculado=(custo.valor * pct / 100).quantize(Decimal("0.01")), status=StatusRateio.PAGO))
    await session.flush()

    # Mar/2026 — ABERTO, tudo pendente
    mes_mar = MesReferencia(tenant_id=tenant.id, ano=2026, mes=3, status=StatusMes.ABERTO)
    session.add(mes_mar)
    await session.flush()
    custos_mar = [
        Custo(descricao="Condomínio", valor=Decimal("900.00"), data_vencimento=date(2026, 3, 10), tipo=TipoCusto.FIXO, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id, custo_fixo_origem_id=cf_cond.id),
        Custo(descricao="Internet", valor=Decimal("100.00"), data_vencimento=date(2026, 3, 15), tipo=TipoCusto.FIXO, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id, custo_fixo_origem_id=cf_internet.id),
        Custo(descricao="Limpeza", valor=Decimal("150.00"), data_vencimento=date(2026, 3, 18), tipo=TipoCusto.VARIAVEL, status=StatusPagamento.PENDENTE, mes_referencia_id=mes_mar.id),
    ]
    session.add_all(custos_mar)
    await session.flush()
    for custo in custos_mar:
        for u, pct in rateio:
            session.add(PagamentoRateio(custo_id=custo.id, usuario_id=u.id, porcentagem=pct, valor_calculado=(custo.valor * pct / 100).quantize(Decimal("0.01")), status=StatusRateio.PENDENTE))
    await session.flush()

    print(f"🏠 Tenant criado: {tenant.nome}")
    print(f"   Usuários: luana (OWNER), carlos (MEMBER)  — senha: {SENHA_PADRAO}")
    print(f"   Assinatura: Básico (ATIVA)")
    print(f"   Meses: Fev/2026 (FECHADO), Mar/2026 (ABERTO)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 55)
    print("  populate_data — fixture de teste")
    print("=" * 55)
    print()

    async with async_session_factory() as session:
        async with session.begin():
            await limpar_banco(session)

            print("📋 Criando planos...")
            planos = await criar_planos(session)
            print()

            print("🔐 Criando admin...")
            await criar_admin(session)
            print()

            print("🏘️  Criando tenants...")
            await criar_tenant_juan(session, planos)
            print()
            await criar_tenant_luana(session, planos)
            print()

    print("=" * 55)
    print("  ✅ Fixture criada com sucesso!")
    print()
    print("  Credenciais de acesso:")
    print()
    print("  Admin panel  → /admin/login")
    print("  username: admin    senha: admin")
    print()
    print("  App (Casa do Juan):")
    print(f"  juan / pedro / maria  →  senha: {SENHA_PADRAO}")
    print()
    print("  App (Casa da Luana):")
    print(f"  luana / carlos        →  senha: {SENHA_PADRAO}")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())

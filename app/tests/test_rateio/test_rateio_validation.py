from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.rateio
class TestRateioValidation:
    """Test suite for validating the percentage sum rule (<=100%)."""

    async def _create_test_data(self, client: AsyncClient, session) -> dict:
        """Helper to create tenant, usuarios, mes_referencia, and custo."""
        _, owner = await make_tenant_user(
            session, tenant_nome="Casa Rateio Teste", username="dono_r"
        )
        self.h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}

        usuario1 = (await client.post(
            "/api/usuarios/",
            headers=self.h,
            json={
                "username": "usuario1",
                "email": "usuario1@test.com",
                "password": "senha123",
                "nome": "Usuario Um",
            },
        )).json()

        usuario2 = (await client.post(
            "/api/usuarios/",
            headers=self.h,
            json={
                "username": "usuario2",
                "email": "usuario2@test.com",
                "password": "senha123",
                "nome": "Usuario Dois",
            },
        )).json()

        mes = (await client.post(
            "/api/meses/",
            headers=self.h,
            json={"ano": 2024, "mes": 1},
        )).json()

        custo = (await client.post(
            "/api/custos/",
            headers=self.h,
            json={
                "descricao": "Aluguel",
                "valor": "1000.00",
                "data_vencimento": "2024-01-10",
                "mes_referencia_id": mes["id"],
            },
        )).json()

        return {
            "usuario1": usuario1,
            "usuario2": usuario2,
            "mes": mes,
            "custo": custo,
        }

    async def test_create_rateio_success(self, client: AsyncClient, session):
        """Test creating a valid rateio."""
        data = await self._create_test_data(client, session)

        response = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "60.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )

        assert response.status_code == 201
        rateio = response.json()
        assert Decimal(rateio["porcentagem"]) == Decimal("60.00")
        assert Decimal(rateio["valor_calculado"]) == Decimal("600.00")

    async def test_create_multiple_rateios_within_limit(self, client: AsyncClient, session):
        """Test creating multiple rateios that sum to exactly 100%."""
        data = await self._create_test_data(client, session)

        # First rateio: 60%
        response1 = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "60.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )
        assert response1.status_code == 201

        # Second rateio: 40% (total = 100%)
        response2 = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "40.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario2"]["id"],
            },
        )
        assert response2.status_code == 201

        # Verify calculated values
        rateio1 = response1.json()
        rateio2 = response2.json()
        assert Decimal(rateio1["valor_calculado"]) == Decimal("600.00")
        assert Decimal(rateio2["valor_calculado"]) == Decimal("400.00")

    async def test_create_rateio_exceeds_100_percent(self, client: AsyncClient, session):
        """Test that creating a rateio exceeding 100% total is rejected."""
        data = await self._create_test_data(client, session)

        # First rateio: 60%
        response1 = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "60.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )
        assert response1.status_code == 201

        # Try to add 50% more (total would be 110%)
        response2 = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "50.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario2"]["id"],
            },
        )
        assert response2.status_code == 400
        assert "100%" in response2.json()["detail"]

    async def test_update_rateio_exceeds_100_percent(self, client: AsyncClient, session):
        """Test that updating a rateio to exceed 100% total is rejected."""
        data = await self._create_test_data(client, session)

        # Create two rateios that sum to 100%
        response1 = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "50.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )
        rateio1 = response1.json()

        await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "50.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario2"]["id"],
            },
        )

        # Try to update first rateio to 60% (total would be 110%)
        update_response = await client.put(
            f"/api/rateios/{rateio1['id']}",
            headers=self.h,
            json={"porcentagem": "60.00"},
        )
        assert update_response.status_code == 400
        assert "100%" in update_response.json()["detail"]

    async def test_update_rateio_within_limit(self, client: AsyncClient, session):
        """Test that updating a rateio within 100% is allowed."""
        data = await self._create_test_data(client, session)

        # Create rateio with 50%
        response = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "50.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )
        rateio = response.json()

        # Update to 70% (still within limit)
        update_response = await client.put(
            f"/api/rateios/{rateio['id']}",
            headers=self.h,
            json={"porcentagem": "70.00"},
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert Decimal(updated["porcentagem"]) == Decimal("70.00")
        assert Decimal(updated["valor_calculado"]) == Decimal("700.00")

    async def test_rateio_porcentagem_validation(self, client: AsyncClient, session):
        """Test that individual porcentagem must be between 0 and 100."""
        data = await self._create_test_data(client, session)

        # Try 0%
        response_zero = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "0.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )
        assert response_zero.status_code == 422

        # Try over 100%
        response_over = await client.post(
            "/api/rateios/",
            headers=self.h,
            json={
                "porcentagem": "101.00",
                "custo_id": data["custo"]["id"],
                "usuario_id": data["usuario1"]["id"],
            },
        )
        assert response_over.status_code == 422

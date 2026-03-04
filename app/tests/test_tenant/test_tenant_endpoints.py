import pytest
from httpx import AsyncClient


@pytest.mark.tenant
class TestTenantEndpoints:
    async def test_create_tenant(self, client: AsyncClient):
        response = await client.post(
            "/api/tenants/",
            json={"nome": "Casa Nova", "descricao": "Descricao da casa"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Casa Nova"
        assert data["descricao"] == "Descricao da casa"
        assert "id" in data
        assert "created_at" in data

    async def test_get_tenant(self, client: AsyncClient):
        # Create a tenant first
        create_response = await client.post(
            "/api/tenants/",
            json={"nome": "Casa Teste", "descricao": "Para buscar"},
        )
        tenant_id = create_response.json()["id"]

        # Get the tenant
        response = await client.get(f"/api/tenants/{tenant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant_id
        assert data["nome"] == "Casa Teste"

    async def test_get_tenant_not_found(self, client: AsyncClient):
        response = await client.get("/api/tenants/99999")
        assert response.status_code == 404

    async def test_list_tenants(self, client: AsyncClient):
        # Create multiple tenants
        await client.post("/api/tenants/", json={"nome": "Casa 1"})
        await client.post("/api/tenants/", json={"nome": "Casa 2"})

        response = await client.get("/api/tenants/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_update_tenant(self, client: AsyncClient):
        # Create a tenant
        create_response = await client.post(
            "/api/tenants/",
            json={"nome": "Nome Original"},
        )
        tenant_id = create_response.json()["id"]

        # Update it
        response = await client.put(
            f"/api/tenants/{tenant_id}",
            json={"nome": "Nome Atualizado"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Nome Atualizado"

    async def test_delete_tenant(self, client: AsyncClient):
        # Create a tenant
        create_response = await client.post(
            "/api/tenants/",
            json={"nome": "Para Deletar"},
        )
        tenant_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/api/tenants/{tenant_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/tenants/{tenant_id}")
        assert get_response.status_code == 404

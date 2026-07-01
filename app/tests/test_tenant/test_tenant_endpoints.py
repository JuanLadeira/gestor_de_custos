import pytest
from httpx import AsyncClient


@pytest.mark.tenant
async def test_tenant_list_endpoint_removed(client: AsyncClient):
    r = await client.get("/api/tenants/")
    assert r.status_code in (401, 403, 404, 405)

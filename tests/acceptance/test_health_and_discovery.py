"""Smoke and discovery: health checks for deployments (plan milestone 1)."""

import pytest
from httpx import ASGITransport, AsyncClient

from smvc_api.main import app


@pytest.mark.acceptance
@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

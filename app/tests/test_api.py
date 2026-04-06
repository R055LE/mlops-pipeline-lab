import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_predict_positive(client):
    resp = await client.post("/predict", json={"text": "This is wonderful!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "label" in data
    assert "score" in data
    assert data["label"] in ("POSITIVE", "NEGATIVE")
    assert 0.0 <= data["score"] <= 1.0


@pytest.mark.asyncio
async def test_predict_negative(client):
    resp = await client.post("/predict", json={"text": "This is terrible and awful."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] in ("POSITIVE", "NEGATIVE")
    assert 0.0 <= data["score"] <= 1.0


@pytest.mark.asyncio
async def test_predict_missing_text(client):
    resp = await client.post("/predict", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_metrics(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "requests_total" in resp.text

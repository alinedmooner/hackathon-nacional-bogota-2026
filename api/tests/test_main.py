from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "SECOP API", "version": "1.0.0"}

def test_health():
    # El endpoint health se conecta a mongo local, puede fallar si no hay BD corriendo en el CI
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

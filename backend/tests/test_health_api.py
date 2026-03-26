from fastapi.testclient import TestClient

from app.main import create_app


def test_health_response_contains_expected_fields() -> None:
    with TestClient(create_app()) as client:
        payload = client.get("/api/v1/health").json()

    assert payload["status"] == "ok"
    assert isinstance(payload["database"]["path"], str)
    assert isinstance(payload["database"]["healthy"], bool)
    scraper = payload["scraper"]
    assert scraper["engine"] == "scrapling"
    assert "timeout_ms" in scraper
    assert "verify_tls" in scraper

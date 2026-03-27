from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.core.crypto import SecretCipher
from app.core.database import Database
from app.services.llm.service import LlmConfigService


def _create_test_app(db_path: Path) -> tuple[FastAPI, LlmConfigService]:
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    database = Database(db_path)
    database.initialize()
    cipher = SecretCipher(purpose="test")
    service = LlmConfigService(database=database, cipher=cipher)

    app.state.database = database
    app.state.job_manager = None
    app.state.intelligence_scorer = None
    app.state.linkedin_session_service = None
    app.state.mail_service = None
    app.state.llm_config_service = service

    return app, service


def test_get_providers_returns_seven(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        response = client.get("/api/v1/llm/providers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    keys = [p["key"] for p in data]
    assert "openai" in keys
    assert "anthropic" in keys


def test_crud_lifecycle(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        # Create
        response = client.post("/api/v1/llm/configs", json={
            "provider": "openai",
            "display_name": "My OpenAI",
            "model_name": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-test-key-12345",
        })
        assert response.status_code == 201
        config = response.json()
        config_id = config["id"]
        assert config["display_name"] == "My OpenAI"
        assert config["has_api_key"] is True
        assert config["is_active"] is False
        assert "official_url" in config

        # List
        response = client.get("/api/v1/llm/configs")
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Get by id
        response = client.get(f"/api/v1/llm/configs/{config_id}")
        assert response.status_code == 200
        assert response.json()["id"] == config_id

        # Update
        response = client.patch(f"/api/v1/llm/configs/{config_id}", json={
            "display_name": "Updated OpenAI",
            "model_name": "gpt-4o",
        })
        assert response.status_code == 200
        assert response.json()["display_name"] == "Updated OpenAI"
        assert response.json()["model_name"] == "gpt-4o"
        assert response.json()["has_api_key"] is True  # key still present

        # Delete
        response = client.delete(f"/api/v1/llm/configs/{config_id}")
        assert response.status_code == 204

        # Confirm deleted
        response = client.get("/api/v1/llm/configs")
        assert len(response.json()) == 0


def test_patch_without_api_key_preserves_existing(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        create_resp = client.post("/api/v1/llm/configs", json={
            "provider": "openai",
            "display_name": "Test",
            "model_name": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-original",
        })
        config_id = create_resp.json()["id"]

        # Update with empty api_key
        update_resp = client.patch(f"/api/v1/llm/configs/{config_id}", json={
            "api_key": "",
            "note": "new note",
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["has_api_key"] is True
        assert update_resp.json()["note"] == "new note"


def test_activate_switches_exclusively(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        c1 = client.post("/api/v1/llm/configs", json={
            "provider": "openai",
            "display_name": "OpenAI",
            "model_name": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-key1",
        }).json()

        c2 = client.post("/api/v1/llm/configs", json={
            "provider": "deepseek",
            "display_name": "DeepSeek",
            "model_name": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-key2",
        }).json()

        # Activate c1
        resp = client.post(f"/api/v1/llm/configs/{c1['id']}/activate")
        assert resp.json()["is_active"] is True

        # Activate c2
        resp = client.post(f"/api/v1/llm/configs/{c2['id']}/activate")
        assert resp.json()["is_active"] is True

        # c1 should now be inactive
        configs = client.get("/api/v1/llm/configs").json()
        active = [c for c in configs if c["is_active"]]
        assert len(active) == 1
        assert active[0]["id"] == c2["id"]


def test_get_active_config_includes_decrypted_key(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        config = client.post("/api/v1/llm/configs", json={
            "provider": "openai",
            "display_name": "Active Test",
            "model_name": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-should-be-decrypted",
        }).json()

        client.post(f"/api/v1/llm/configs/{config['id']}/activate")

        resp = client.get("/api/v1/llm/configs/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_key"] == "sk-should-be-decrypted"
        assert data["display_name"] == "Active Test"


def test_get_active_config_when_none_returns_null(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        resp = client.get("/api/v1/llm/configs/active")
        assert resp.status_code == 200
        assert resp.json() is None


def test_list_configs_no_plaintext_key(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        client.post("/api/v1/llm/configs", json={
            "provider": "openai",
            "display_name": "Secret",
            "model_name": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-must-not-appear",
        })

        configs = client.get("/api/v1/llm/configs").json()
        assert len(configs) == 1
        # api_key must NOT appear in the summary
        assert "api_key" not in configs[0]
        assert "encrypted_api_key" not in configs[0]
        assert configs[0]["has_api_key"] is True


def test_get_config_not_found(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        resp = client.get("/api/v1/llm/configs/nonexistent")
        assert resp.status_code == 404


def test_delete_config_not_found(tmp_path: Path) -> None:
    app, _ = _create_test_app(tmp_path / "llm-api.db")
    with TestClient(app) as client:
        resp = client.delete("/api/v1/llm/configs/nonexistent")
        assert resp.status_code == 404

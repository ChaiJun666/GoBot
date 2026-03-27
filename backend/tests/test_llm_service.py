from __future__ import annotations

from pathlib import Path

import pytest

from app.core.crypto import SecretCipher
from app.core.database import Database
from app.schemas.llm import LlmProviderKey, LLM_PROVIDER_PRESETS
from app.services.llm.service import LlmConfigService


@pytest.fixture
def service(tmp_path: Path) -> LlmConfigService:
    database = Database(tmp_path / "test-llm.db")
    database.initialize()
    cipher = SecretCipher(purpose="test")
    return LlmConfigService(database=database, cipher=cipher)


def test_provider_presets_count(service: LlmConfigService) -> None:
    presets = service.get_provider_presets()
    assert len(presets) == 7
    keys = [p.key for p in presets]
    assert LlmProviderKey.OPENAI in keys
    assert LlmProviderKey.ANTHROPIC in keys
    assert LlmProviderKey.XAI in keys
    assert LlmProviderKey.DEEPSEEK in keys
    assert LlmProviderKey.QWEN in keys
    assert LlmProviderKey.ZHIPU in keys
    assert LlmProviderKey.MINIMAX in keys


def test_provider_presets_have_required_fields(service: LlmConfigService) -> None:
    for preset in service.get_provider_presets():
        assert preset.display_name
        assert preset.default_base_url.startswith("https://")
        assert preset.official_url.startswith("https://")


def test_create_config_encrypts_api_key(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    payload = CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="My OpenAI",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-test-secret-key-12345",
    )
    config = service.create_config(payload)

    assert config.display_name == "My OpenAI"
    assert config.model_name == "gpt-4o-mini"
    assert config.has_api_key is True
    assert config.is_active is False

    # Verify raw DB record has encrypted key (not plaintext)
    record = service._db.get_llm_config(config.id)
    assert record is not None
    assert record["encrypted_api_key"] != "sk-test-secret-key-12345"
    assert len(record["encrypted_api_key"]) > 0


def test_create_config_auto_fills_official_url(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    payload = CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="Test",
        model_name="gpt-4o",
        base_url="https://api.openai.com/v1",
        api_key="sk-test",
    )
    config = service.create_config(payload)
    preset = LLM_PROVIDER_PRESETS[LlmProviderKey.OPENAI]
    assert config.official_url == preset.official_url


def test_create_config_custom_official_url(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    payload = CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="Test",
        model_name="gpt-4o",
        base_url="https://api.openai.com/v1",
        api_key="sk-test",
        official_url="https://custom.url",
    )
    config = service.create_config(payload)
    assert config.official_url == "https://custom.url"


def test_update_config_keeps_api_key_when_empty(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest, UpdateLlmConfigRequest

    # Create
    service.create_config(CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="Original",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-original-key",
    ))
    configs = service.list_configs()
    config_id = configs[0].id

    # Update without api_key
    service.update_config(config_id, UpdateLlmConfigRequest(
        display_name="Updated",
        model_name="gpt-4o",
    ))

    updated = service.get_config(config_id)
    assert updated.display_name == "Updated"
    assert updated.model_name == "gpt-4o"
    assert updated.has_api_key is True  # still has the original key

    # Verify active config returns decrypted original key
    service.activate_config(config_id)
    active = service.get_active_config()
    assert active is not None
    assert active.api_key == "sk-original-key"


def test_activate_config_deactivates_others(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    c1 = service.create_config(CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="OpenAI Config",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-key1",
    ))
    c2 = service.create_config(CreateLlmConfigRequest(
        provider=LlmProviderKey.DEEPSEEK,
        display_name="DeepSeek Config",
        model_name="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-key2",
    ))

    # Activate c1
    service.activate_config(c1.id)
    configs = service.list_configs()
    assert [c for c in configs if c.is_active] == [c1]

    # Activate c2 -> c1 should be deactivated
    service.activate_config(c2.id)
    configs = service.list_configs()
    active = [c for c in configs if c.is_active]
    assert len(active) == 1
    assert active[0].id == c2.id


def test_delete_config(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    config = service.create_config(CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="To Delete",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-delete-me",
    ))

    assert len(service.list_configs()) == 1
    service.delete_config(config.id)
    assert len(service.list_configs()) == 0


def test_delete_nonexistent_raises(service: LlmConfigService) -> None:
    from app.schemas.llm import UpdateLlmConfigRequest

    with pytest.raises(LookupError):
        service.delete_config("nonexistent-id")


def test_get_active_config_returns_decrypted_key(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    service.create_config(CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="Active Config",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-secret-active",
    ))
    configs = service.list_configs()
    service.activate_config(configs[0].id)

    active = service.get_active_config()
    assert active is not None
    assert active.api_key == "sk-secret-active"
    assert active.display_name == "Active Config"
    assert active.model_name == "gpt-4o-mini"


def test_get_active_config_when_none(service: LlmConfigService) -> None:
    assert service.get_active_config() is None


def test_list_configs_does_not_leak_api_key(service: LlmConfigService) -> None:
    from app.schemas.llm import CreateLlmConfigRequest

    service.create_config(CreateLlmConfigRequest(
        provider=LlmProviderKey.OPENAI,
        display_name="Secret Config",
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-super-secret",
    ))

    configs = service.list_configs()
    assert len(configs) == 1
    assert configs[0].has_api_key is True
    # LlmConfigSummary has no api_key field, so it cannot be leaked


def test_get_config_not_found(service: LlmConfigService) -> None:
    with pytest.raises(LookupError):
        service.get_config("nonexistent")

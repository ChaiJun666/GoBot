from __future__ import annotations

import uuid

from app.core.crypto import SecretCipher
from app.core.database import Database
from app.schemas.llm import (
    ActiveLlmConfig,
    CreateLlmConfigRequest,
    LlmConfigSummary,
    LlmProviderKey,
    LlmProviderPreset,
    UpdateLlmConfigRequest,
    LLM_PROVIDER_PRESETS,
)


class LlmConfigService:
    def __init__(self, database: Database, cipher: SecretCipher) -> None:
        self._db = database
        self._cipher = cipher

    def get_provider_presets(self) -> list[LlmProviderPreset]:
        return list(LLM_PROVIDER_PRESETS.values())

    def list_configs(self) -> list[LlmConfigSummary]:
        rows = self._db.list_llm_configs()
        return [LlmConfigSummary.from_record(r) for r in rows]

    def create_config(self, payload: CreateLlmConfigRequest) -> LlmConfigSummary:
        config_id = uuid.uuid4().hex
        encrypted_key = self._cipher.encrypt(payload.api_key)

        # Auto-fill official_url from preset if not provided
        official_url = payload.official_url
        if not official_url:
            preset = LLM_PROVIDER_PRESETS.get(payload.provider)
            if preset:
                official_url = preset.official_url

        self._db.create_llm_config(
            config_id=config_id,
            provider=payload.provider.value,
            display_name=payload.display_name,
            model_name=payload.model_name,
            base_url=payload.base_url,
            encrypted_api_key=encrypted_key,
            official_url=official_url,
            note=payload.note,
        )

        record = self._db.get_llm_config(config_id)
        if record is None:
            raise RuntimeError("Failed to retrieve created LLM config")
        return LlmConfigSummary.from_record(record)

    def get_config(self, config_id: str) -> LlmConfigSummary:
        record = self._db.get_llm_config(config_id)
        if record is None:
            raise LookupError(f"LLM config {config_id} not found")
        return LlmConfigSummary.from_record(record)

    def update_config(self, config_id: str, payload: UpdateLlmConfigRequest) -> LlmConfigSummary:
        existing = self._db.get_llm_config(config_id)
        if existing is None:
            raise LookupError(f"LLM config {config_id} not found")

        fields: dict = {}
        if payload.display_name is not None:
            fields["display_name"] = payload.display_name
        if payload.model_name is not None:
            fields["model_name"] = payload.model_name
        if payload.base_url is not None:
            fields["base_url"] = payload.base_url
        if payload.note is not None:
            fields["note"] = payload.note
        else:
            fields["note"] = None
        if payload.official_url is not None:
            fields["official_url"] = payload.official_url
        # api_key: empty string or None means keep existing
        if payload.api_key:
            fields["encrypted_api_key"] = self._cipher.encrypt(payload.api_key)

        if fields:
            self._db.update_llm_config(config_id, **fields)

        record = self._db.get_llm_config(config_id)
        if record is None:
            raise LookupError(f"LLM config {config_id} not found after update")
        return LlmConfigSummary.from_record(record)

    def delete_config(self, config_id: str) -> None:
        existing = self._db.get_llm_config(config_id)
        if existing is None:
            raise LookupError(f"LLM config {config_id} not found")
        self._db.delete_llm_config(config_id)

    def activate_config(self, config_id: str) -> LlmConfigSummary:
        existing = self._db.get_llm_config(config_id)
        if existing is None:
            raise LookupError(f"LLM config {config_id} not found")
        self._db.activate_llm_config(config_id)
        record = self._db.get_llm_config(config_id)
        if record is None:
            raise RuntimeError("Failed to retrieve activated LLM config")
        return LlmConfigSummary.from_record(record)

    def get_active_config(self) -> ActiveLlmConfig | None:
        record = self._db.get_active_llm_config()
        if record is None:
            return None
        encrypted_key = record.get("encrypted_api_key", "")
        if not encrypted_key:
            return None
        api_key = self._cipher.decrypt(encrypted_key)
        data = {
            "id": record["id"],
            "provider": record["provider"],
            "display_name": record["display_name"],
            "model_name": record["model_name"],
            "base_url": record["base_url"],
            "official_url": record.get("official_url"),
            "note": record.get("note"),
            "api_key": api_key,
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
        }
        return ActiveLlmConfig.model_validate(data)

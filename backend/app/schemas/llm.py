from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LlmProviderKey(str, Enum):
    OPENAI = "openai"
    XAI = "xai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    ZHIPU = "zhipu"
    MINIMAX = "minimax"


class LlmProviderPreset(BaseModel):
    key: LlmProviderKey
    display_name: str
    default_base_url: str
    official_url: str


LLM_PROVIDER_PRESETS: dict[LlmProviderKey, LlmProviderPreset] = {
    LlmProviderKey.OPENAI: LlmProviderPreset(
        key=LlmProviderKey.OPENAI,
        display_name="OpenAI",
        default_base_url="https://api.openai.com/v1",
        official_url="https://platform.openai.com",
    ),
    LlmProviderKey.XAI: LlmProviderPreset(
        key=LlmProviderKey.XAI,
        display_name="xAI (Grok)",
        default_base_url="https://api.x.ai/v1",
        official_url="https://console.x.ai",
    ),
    LlmProviderKey.ANTHROPIC: LlmProviderPreset(
        key=LlmProviderKey.ANTHROPIC,
        display_name="Anthropic (Claude)",
        default_base_url="https://api.anthropic.com/v1",
        official_url="https://console.anthropic.com",
    ),
    LlmProviderKey.DEEPSEEK: LlmProviderPreset(
        key=LlmProviderKey.DEEPSEEK,
        display_name="DeepSeek",
        default_base_url="https://api.deepseek.com/v1",
        official_url="https://platform.deepseek.com",
    ),
    LlmProviderKey.QWEN: LlmProviderPreset(
        key=LlmProviderKey.QWEN,
        display_name="Qwen (Max)",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        official_url="https://dashscope.console.aliyun.com",
    ),
    LlmProviderKey.ZHIPU: LlmProviderPreset(
        key=LlmProviderKey.ZHIPU,
        display_name="Zhipu (GLM)",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
        official_url="https://open.bigmodel.cn",
    ),
    LlmProviderKey.MINIMAX: LlmProviderPreset(
        key=LlmProviderKey.MINIMAX,
        display_name="MiniMax",
        default_base_url="https://api.minimax.chat/v1",
        official_url="https://platform.minimaxi.com",
    ),
}


class CreateLlmConfigRequest(BaseModel):
    provider: LlmProviderKey
    display_name: str = Field(min_length=1, max_length=120)
    model_name: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(min_length=1, max_length=2000)
    note: str | None = Field(default=None, max_length=300)
    official_url: str | None = Field(default=None, max_length=500)


class UpdateLlmConfigRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    model_name: str | None = Field(default=None, min_length=1, max_length=120)
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    api_key: str | None = Field(default=None, max_length=2000)
    note: str | None = Field(default=None, max_length=300)
    official_url: str | None = Field(default=None, max_length=500)


class LlmConfigSummary(BaseModel):
    id: str
    provider: str
    display_name: str
    model_name: str
    base_url: str
    official_url: str | None = None
    note: str | None = None
    has_api_key: bool = False
    is_active: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict) -> "LlmConfigSummary":
        return cls.model_validate(record)


class ActiveLlmConfig(BaseModel):
    id: str
    provider: str
    display_name: str
    model_name: str
    base_url: str
    official_url: str | None = None
    note: str | None = None
    api_key: str
    created_at: datetime
    updated_at: datetime

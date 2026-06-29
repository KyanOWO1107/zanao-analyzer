import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from zanao_monitor.config import read_env_file
from zanao_monitor.models import DemandMatch


@dataclass(frozen=True)
class AiConfig:
    enabled: bool
    provider: str
    base_url: str
    api_key: str
    model: str
    confidence_threshold: float
    timeout_seconds: int


@dataclass(frozen=True)
class AiReview:
    is_target: bool
    category: str
    intent: str
    confidence: float
    reason: str


def _env_value(values: dict[str, str], key: str, default: str = "") -> str:
    return os.getenv(key) or values.get(key, default)


def load_ai_config(env_path: str | Path = ".env") -> AiConfig:
    values = read_env_file(env_path)
    enabled = _env_value(values, "AI_ENABLED", "false").lower() in ("1", "true", "yes", "on")
    return AiConfig(
        enabled=enabled,
        provider=_env_value(values, "AI_PROVIDER", "openai-compatible"),
        base_url=_env_value(values, "AI_BASE_URL", "").rstrip("/"),
        api_key=_env_value(values, "AI_API_KEY", ""),
        model=_env_value(values, "AI_MODEL", ""),
        confidence_threshold=float(_env_value(values, "AI_CONFIDENCE_THRESHOLD", "0.7")),
        timeout_seconds=int(_env_value(values, "AI_TIMEOUT_SECONDS", "10")),
    )


def parse_ai_review(content: str) -> AiReview:
    raw = json.loads(content)
    if not isinstance(raw, dict):
        raise ValueError("AI review must be a JSON object")
    return AiReview(
        is_target=bool(raw["is_target"]),
        category=str(raw["category"]),
        intent=str(raw["intent"]),
        confidence=float(raw["confidence"]),
        reason=str(raw["reason"]),
    )


class OpenAICompatibleReviewer:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session() if session is None else session

    def review(self, match: DemandMatch) -> AiReview:
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是校园集市信息筛选器。只判断帖子是否属于当前目标：资料、题库、课设资料、"
                            "实验报告、答案、二手书、教材、电子教材。请只返回 JSON 对象，字段为 "
                            "is_target, category, intent, confidence, reason。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "rule_category": match.category,
                                "rule_intent": match.intent,
                                "rule_keywords": match.keywords,
                                "title": match.post.title,
                                "content": match.post.content[:500],
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise ValueError("AI response missing choices")
        first = choices[0]
        if not isinstance(first, dict):
            raise ValueError("AI response choice is not an object")
        message = first.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("AI response message is not an object")
        content = message.get("content", "")
        return parse_ai_review(str(content))


def build_ai_reviewer(config: AiConfig) -> OpenAICompatibleReviewer | None:
    if not config.enabled:
        return None
    if config.provider != "openai-compatible":
        raise ValueError(f"Unsupported AI provider: {config.provider}")
    if not config.base_url or not config.api_key or not config.model:
        raise ValueError("AI_BASE_URL, AI_API_KEY, and AI_MODEL are required when AI is enabled")
    return OpenAICompatibleReviewer(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model,
        timeout_seconds=config.timeout_seconds,
    )

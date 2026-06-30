import os
from dataclasses import dataclass
from pathlib import Path

import requests

from zanao_monitor.config import read_env_file
from zanao_monitor.models import DemandMatch


@dataclass(frozen=True)
class AstrBotConfig:
    enabled: bool
    webhook_url: str
    token: str
    timeout_seconds: int


def _env_value(values: dict[str, str], key: str, default: str = "") -> str:
    return os.getenv(key) or values.get(key, default)


def load_astrbot_config(env_path: str | Path = ".env") -> AstrBotConfig:
    values = read_env_file(env_path)
    enabled = _env_value(values, "ASTRBOT_ENABLED", "false").lower() in ("1", "true", "yes", "on")
    return AstrBotConfig(
        enabled=enabled,
        webhook_url=_env_value(values, "ASTRBOT_WEBHOOK_URL", ""),
        token=_env_value(values, "ASTRBOT_TOKEN", ""),
        timeout_seconds=int(_env_value(values, "ASTRBOT_TIMEOUT_SECONDS", "10")),
    )


def build_notification_text(match: DemandMatch) -> str:
    post = match.post
    return "\n".join(
        (
            "赞噢需求提醒",
            f"类别: {match.category}",
            f"意图: {match.intent}",
            f"关键词: {', '.join(match.keywords)}",
            f"标题: {post.title}",
            f"作者: {post.author}",
            f"来源: {post.source}/{post.post_id}",
            f"内容: {post.content[:180]}",
        )
    )


def send_astrbot_message(config: AstrBotConfig, text: str) -> None:
    if not config.enabled:
        return
    if not config.webhook_url or not config.token:
        raise ValueError("ASTRBOT_WEBHOOK_URL and ASTRBOT_TOKEN are required when AstrBot is enabled")

    response = requests.post(
        config.webhook_url,
        json={"token": config.token, "text": text},
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    try:
        body = response.json()
    except ValueError:
        return
    if not isinstance(body, dict):
        return
    if body.get("ok", True):
        return
    raise ValueError(str(body.get("message", "AstrBot webhook returned an error")))

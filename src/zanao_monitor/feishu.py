import base64
import hashlib
import hmac
import time
from collections.abc import Mapping

import requests

from zanao_monitor.models import DemandMatch

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | dict[str, "JsonValue"] | list["JsonValue"]
JsonObject = dict[str, JsonValue]


def make_sign(timestamp: int, secret: str) -> str:
    key = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(key, b"", hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def build_signed_payload(
    message: Mapping[str, JsonValue],
    secret: str,
    timestamp: int | None = None,
) -> JsonObject:
    actual_timestamp = int(time.time()) if timestamp is None else timestamp
    payload = dict(message)
    payload["timestamp"] = str(actual_timestamp)
    payload["sign"] = make_sign(actual_timestamp, secret)
    return payload


def build_plain_text_message(text: str) -> JsonObject:
    return {"msg_type": "text", "content": {"text": text}}


def build_text_message(match: DemandMatch) -> JsonObject:
    post = match.post
    text = "\n".join(
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
    return build_plain_text_message(text)


def send_message(webhook_url: str, payload: Mapping[str, JsonValue], timeout_seconds: int = 10) -> None:
    response = requests.post(webhook_url, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    try:
        body = response.json()
    except ValueError:
        return
    if not isinstance(body, dict):
        return

    code = body.get("code", body.get("StatusCode", body.get("status_code")))
    if code in (None, 0):
        return

    message = body.get("msg", body.get("StatusMessage", body.get("message", "")))
    raise ValueError(f"Feishu webhook returned code {code}: {message}")

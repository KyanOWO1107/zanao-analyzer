import pytest

from zanao_monitor.models import DemandMatch, Post
from zanao_monitor.notifiers import (
    AstrBotConfig,
    build_notification_text,
    load_astrbot_config,
    send_astrbot_message,
)


def _match() -> DemandMatch:
    return DemandMatch(
        post=Post(
            source="zanao-mini",
            post_id="p1",
            title="求题库",
            content="求这门课题库答案",
            author="alice",
            created_at=1710000000,
        ),
        category="course_resource",
        intent="request",
        keywords=("题库", "答案"),
        score=1.0,
    )


def test_build_notification_text_contains_match_context():
    text = build_notification_text(_match())

    assert "赞噢需求提醒" in text
    assert "求题库" in text
    assert "course_resource" in text
    assert "alice" in text


def test_load_astrbot_config_defaults_to_disabled(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")
    monkeypatch.delenv("ASTRBOT_ENABLED", raising=False)

    config = load_astrbot_config(env_path)

    assert config.enabled is False


def test_load_astrbot_config_reads_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            (
                "ASTRBOT_ENABLED=true",
                "ASTRBOT_WEBHOOK_URL=http://127.0.0.1:6185/zanao/notify",
                "ASTRBOT_TOKEN=test-token",
                "ASTRBOT_TIMEOUT_SECONDS=8",
            )
        ),
        encoding="utf-8",
    )
    for key in ("ASTRBOT_ENABLED", "ASTRBOT_WEBHOOK_URL", "ASTRBOT_TOKEN", "ASTRBOT_TIMEOUT_SECONDS"):
        monkeypatch.delenv(key, raising=False)

    config = load_astrbot_config(env_path)

    assert config == AstrBotConfig(
        enabled=True,
        webhook_url="http://127.0.0.1:6185/zanao/notify",
        token="test-token",
        timeout_seconds=8,
    )


def test_send_astrbot_message_posts_webhook_payload(monkeypatch):
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_post(url, json, timeout):
        requests.append((url, json, timeout))
        return FakeResponse()

    monkeypatch.setattr("zanao_monitor.notifiers.requests.post", fake_post)

    send_astrbot_message(
        config=AstrBotConfig(
            enabled=True,
            webhook_url="http://127.0.0.1:6185/zanao/notify",
            token="test-token",
            timeout_seconds=8,
        ),
        text="hello",
    )

    assert requests == [
        (
            "http://127.0.0.1:6185/zanao/notify",
            {"token": "test-token", "text": "hello"},
            8,
        )
    ]


def test_send_astrbot_message_rejects_error_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": False, "message": "bad token"}

    monkeypatch.setattr("zanao_monitor.notifiers.requests.post", lambda url, json, timeout: FakeResponse())

    with pytest.raises(ValueError) as error:
        send_astrbot_message(
            config=AstrBotConfig(
                enabled=True,
                webhook_url="http://127.0.0.1:6185/zanao/notify",
                token="wrong",
                timeout_seconds=8,
            ),
            text="hello",
        )

    assert "bad token" in str(error.value)

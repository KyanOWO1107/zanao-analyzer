import pytest

from zanao_monitor.feishu import build_plain_text_message, build_signed_payload, build_text_message
from zanao_monitor.models import DemandMatch, Post


def test_build_signed_payload_uses_feishu_hmac_format():
    payload = build_signed_payload(
        message={"msg_type": "text", "content": {"text": "hello"}},
        secret="test-secret",
        timestamp=1609459200,
    )

    assert payload["timestamp"] == "1609459200"
    assert payload["sign"] == "IJ7Pt6eu2c5vM3gkse4crVb6MwgNFSqbEX+fqcT5kX8="
    assert payload["msg_type"] == "text"


def test_build_plain_text_message_returns_feishu_text_payload():
    message = build_plain_text_message("hello")

    assert message == {"msg_type": "text", "content": {"text": "hello"}}


def test_build_text_message_contains_demand_context():
    post = Post(
        source="sample",
        post_id="p1",
        title="求电子教材",
        content="求计算机网络电子版教材",
        author="alice",
        created_at=1710000000,
    )
    match = DemandMatch(
        post=post,
        category="ebook",
        intent="request",
        keywords=("电子教材",),
        score=1.0,
    )

    message = build_text_message(match)

    assert message["msg_type"] == "text"
    text = message["content"]["text"]
    assert "求电子教材" in text
    assert "ebook" in text
    assert "alice" in text


def test_send_message_rejects_feishu_error_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"code": 9499, "msg": "bad sign"}

    def fake_post(url, json, timeout):
        assert url == "https://example.test/hook"
        assert json["msg_type"] == "text"
        assert timeout == 10
        return FakeResponse()

    monkeypatch.setattr("zanao_monitor.feishu.requests.post", fake_post)

    from zanao_monitor.feishu import send_message

    with pytest.raises(ValueError) as error:
        send_message("https://example.test/hook", build_plain_text_message("hello"))

    assert "9499" in str(error.value)
    assert "bad sign" in str(error.value)

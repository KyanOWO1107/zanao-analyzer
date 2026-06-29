import pytest

from zanao_monitor.ai import (
    AiReview,
    OpenAICompatibleReviewer,
    load_ai_config,
    parse_ai_review,
)
from zanao_monitor.models import DemandMatch, Post


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


def test_load_ai_config_defaults_to_disabled(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")
    monkeypatch.delenv("AI_ENABLED", raising=False)

    config = load_ai_config(env_path)

    assert config.enabled is False


def test_load_ai_config_reads_openai_compatible_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            (
                "AI_ENABLED=true",
                "AI_PROVIDER=openai-compatible",
                "AI_BASE_URL=https://ai.example.test/v1",
                "AI_API_KEY=test-key",
                "AI_MODEL=test-model",
                "AI_CONFIDENCE_THRESHOLD=0.75",
                "AI_TIMEOUT_SECONDS=12",
            )
        ),
        encoding="utf-8",
    )
    for key in (
        "AI_ENABLED",
        "AI_PROVIDER",
        "AI_BASE_URL",
        "AI_API_KEY",
        "AI_MODEL",
        "AI_CONFIDENCE_THRESHOLD",
        "AI_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)

    config = load_ai_config(env_path)

    assert config.enabled is True
    assert config.base_url == "https://ai.example.test/v1"
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.confidence_threshold == 0.75
    assert config.timeout_seconds == 12


def test_parse_ai_review_accepts_json_object():
    review = parse_ai_review(
        '{"is_target": true, "category": "course_resource", "intent": "request", "confidence": 0.86, "reason": "明确求题库"}'
    )

    assert review == AiReview(
        is_target=True,
        category="course_resource",
        intent="request",
        confidence=0.86,
        reason="明确求题库",
    )


def test_parse_ai_review_rejects_invalid_json():
    with pytest.raises(ValueError):
        parse_ai_review("not json")


def test_openai_compatible_reviewer_sends_minimal_post_context():
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"is_target": true, "category": "course_resource", "intent": "request", "confidence": 0.91, "reason": "求题库"}'
                        }
                    }
                ]
            }

    class FakeSession:
        def post(self, url, headers, json, timeout):
            requests.append((url, headers, json, timeout))
            return FakeResponse()

    reviewer = OpenAICompatibleReviewer(
        base_url="https://ai.example.test/v1",
        api_key="test-key",
        model="test-model",
        timeout_seconds=9,
        session=FakeSession(),
    )

    review = reviewer.review(_match())

    assert review.is_target is True
    url, headers, payload, timeout = requests[0]
    assert url == "https://ai.example.test/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-key"
    assert payload["model"] == "test-model"
    assert "X-Sc-Od" not in str(payload)
    assert "求题库" in str(payload)
    assert timeout == 9

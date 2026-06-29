import json
import sqlite3

import pytest

from zanao_monitor.cli import build_parser, format_recent_matches, run_mini_monitor_once, run_watch_mini_monitor, safe_console_text, run_monitor, run_monitor_from_source
from zanao_monitor.cli import load_feishu_config, run_monitor_with_posts
from zanao_monitor.cli import format_posts_for_dry_run
from zanao_monitor.ai import AiReview
from zanao_monitor.models import Post


def test_run_monitor_classifies_matches_in_dry_run(tmp_path):
    posts_path = tmp_path / "posts.json"
    state_path = tmp_path / "state.db"
    posts_path.write_text(
        json.dumps(
            [
                {
                    "source": "sample",
                    "post_id": "p1",
                    "title": "求真题",
                    "content": "求高数真题",
                    "author": "alice",
                    "created_at": 1710000000,
                },
                {
                    "source": "sample",
                    "post_id": "p2",
                    "title": "晚饭",
                    "content": "今天食堂不错",
                    "author": "bob",
                    "created_at": 1710000100,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = run_monitor_from_source(posts_path=posts_path, state_path=state_path, dry_run=True)

    assert result.scanned_count == 2
    assert result.matched_count == 1
    assert result.sent_count == 1
    assert result.skipped_duplicate_count == 0


def test_run_monitor_dry_run_does_not_mark_posts_as_sent(tmp_path):
    posts_path = tmp_path / "posts.json"
    state_path = tmp_path / "state.db"
    posts_path.write_text(
        json.dumps(
            [
                {
                    "source": "sample",
                    "post_id": "p1",
                    "title": "求真题",
                    "content": "求高数真题",
                    "author": "alice",
                    "created_at": 1710000000,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    first = run_monitor_from_source(posts_path=posts_path, state_path=state_path, dry_run=True)
    second = run_monitor_from_source(posts_path=posts_path, state_path=state_path, dry_run=True)

    assert first.sent_count == 1
    assert second.sent_count == 1
    assert second.skipped_duplicate_count == 0


def test_run_monitor_accepts_loaded_posts(tmp_path):
    state_path = tmp_path / "state.db"

    result = run_monitor(
        posts=[
            Post(
                source="sample",
                post_id="p1",
                title="求电子教材",
                content="求计算机网络电子教材",
                author="alice",
                created_at=1710000000,
            )
        ],
        state_path=state_path,
        dry_run=True,
    )

    assert result.scanned_count == 1
    assert result.matched_count == 1
    assert result.sent_count == 1


def test_run_monitor_from_source_reads_inschool_sqlite(tmp_path):
    db_path = tmp_path / "inschool.db"
    state_path = tmp_path / "state.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE posts (
                thread_id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                nickname TEXT,
                create_time_ts INTEGER
            )
            """
        )
        conn.execute(
            """
            INSERT INTO posts (thread_id, title, content, nickname, create_time_ts)
            VALUES ('p1', '求真题', '求高数真题', 'alice', 1710000000)
            """
        )

    result = run_monitor_from_source(
        inschool_db_path=db_path,
        state_path=state_path,
        dry_run=True,
        limit=10,
    )

    assert result.scanned_count == 1
    assert result.matched_count == 1
    assert result.sent_count == 1


def test_format_posts_for_dry_run_truncates_content():
    output = format_posts_for_dry_run(
        [
            Post(
                source="zanao-mini",
                post_id="p1",
                title="求真题",
                content="这是一段很长的内容" * 20,
                author="alice",
                created_at=1710000000,
            )
        ]
    )

    assert "p1" in output
    assert "求真题" in output
    assert "alice" in output
    assert len(output) < 260


def test_safe_console_text_keeps_supported_text_and_escapes_unsupported_characters():
    output = safe_console_text("求真题😭", encoding="gbk")

    assert "求真题" in output
    assert "\\U0001f62d" in output


def test_build_parser_allows_fetch_mini_list_without_local_source():
    parser = build_parser()

    args = parser.parse_args(["fetch-mini-list", "--limit", "3", "--match", "--state", "state.db"])

    assert args.command == "fetch-mini-list"
    assert args.limit == 3
    assert args.match is True
    assert args.state == "state.db"


def test_run_monitor_with_posts_returns_matched_posts_without_mutating_state_in_dry_run(tmp_path):
    state_path = tmp_path / "state.db"
    posts = [
        Post(
            source="zanao-mini",
            post_id="p1",
            title="求题库",
            content="求这门课的题库和实验报告",
            author="alice",
            created_at=1710000000,
        ),
        Post(
            source="zanao-mini",
            post_id="p2",
            title="随便聊聊",
            content="今天下雨",
            author="bob",
            created_at=1710000100,
        ),
    ]

    result = run_monitor_with_posts(posts=posts, state_path=state_path, dry_run=True)
    duplicate = run_monitor_with_posts(posts=posts, state_path=state_path, dry_run=True)

    assert result.scanned_count == 2
    assert result.matched_count == 1
    assert result.sent_count == 1
    assert [match.post.post_id for match in result.matches_to_send] == ["p1"]
    assert duplicate.sent_count == 1
    assert duplicate.skipped_duplicate_count == 0


def test_run_monitor_with_posts_records_scan_observability(tmp_path):
    state_path = tmp_path / "state.db"
    posts = [
        Post(
            source="zanao-mini",
            post_id="p1",
            title="求题库",
            content="求这门课的题库和实验报告",
            author="alice",
            created_at=1710000000,
        )
    ]

    result = run_monitor_with_posts(posts=posts, state_path=state_path, dry_run=True)

    from zanao_monitor.state import NotificationState

    state = NotificationState(state_path)
    runs = state.list_recent_scan_runs(limit=1)
    matches = state.list_recent_scan_matches(limit=1)

    assert result.matched_count == 1
    assert runs[0].scanned_count == 1
    assert runs[0].matched_count == 1
    assert runs[0].dry_run is True
    assert matches[0].post_id == "p1"
    assert matches[0].status == "preview"


def test_run_monitor_with_posts_applies_ai_reviewer_when_enabled(tmp_path):
    state_path = tmp_path / "state.db"
    posts = [
        Post(
            source="zanao-mini",
            post_id="p1",
            title="求题库",
            content="求这门课的题库和实验报告",
            author="alice",
            created_at=1710000000,
        )
    ]

    def reviewer(match):
        return AiReview(
            is_target=True,
            category=match.category,
            intent=match.intent,
            confidence=0.9,
            reason="明确求资料",
        )

    result = run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=True,
        ai_reviewer=reviewer,
        ai_confidence_threshold=0.7,
    )

    assert result.matched_count == 1
    assert result.sent_count == 1


def test_run_monitor_with_posts_skips_ai_rejected_matches(tmp_path):
    state_path = tmp_path / "state.db"
    posts = [
        Post(
            source="zanao-mini",
            post_id="p1",
            title="求题库",
            content="求这门课的题库和实验报告",
            author="alice",
            created_at=1710000000,
        )
    ]

    def reviewer(match):
        return AiReview(
            is_target=False,
            category=match.category,
            intent=match.intent,
            confidence=0.9,
            reason="不是目标",
        )

    result = run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=True,
        ai_reviewer=reviewer,
        ai_confidence_threshold=0.7,
    )

    from zanao_monitor.state import NotificationState

    matches = NotificationState(state_path).list_recent_scan_matches(limit=1)
    assert result.matched_count == 1
    assert result.sent_count == 0
    assert matches[0].status == "ai_rejected"


def test_run_monitor_with_posts_skips_ai_errors(tmp_path):
    state_path = tmp_path / "state.db"
    posts = [
        Post(
            source="zanao-mini",
            post_id="p1",
            title="求题库",
            content="求这门课的题库和实验报告",
            author="alice",
            created_at=1710000000,
        )
    ]

    def reviewer(match):
        raise RuntimeError("ai unavailable")

    result = run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=True,
        ai_reviewer=reviewer,
        ai_confidence_threshold=0.7,
    )

    from zanao_monitor.state import NotificationState

    matches = NotificationState(state_path).list_recent_scan_matches(limit=1)
    assert result.sent_count == 0
    assert matches[0].status == "ai_error"


def test_load_feishu_config_reads_env_file_when_process_env_missing(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            (
                "FEISHU_WEBHOOK_URL=https://example.test/hook",
                "FEISHU_WEBHOOK_SECRET=secret",
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("FEISHU_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("FEISHU_WEBHOOK_SECRET", raising=False)

    config = load_feishu_config(env_path)

    assert config.webhook_url == "https://example.test/hook"
    assert config.webhook_secret == "secret"


def test_load_feishu_config_prefers_process_env_over_env_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            (
                "FEISHU_WEBHOOK_URL=https://example.test/file",
                "FEISHU_WEBHOOK_SECRET=file-secret",
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://example.test/process")
    monkeypatch.setenv("FEISHU_WEBHOOK_SECRET", "process-secret")

    config = load_feishu_config(env_path)

    assert config.webhook_url == "https://example.test/process"
    assert config.webhook_secret == "process-secret"


def test_load_feishu_config_requires_webhook_url(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("FEISHU_WEBHOOK_SECRET=secret\n", encoding="utf-8")
    monkeypatch.delenv("FEISHU_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("FEISHU_WEBHOOK_SECRET", raising=False)

    with pytest.raises(ValueError) as error:
        load_feishu_config(env_path)

    assert "FEISHU_WEBHOOK_URL" in str(error.value)


def test_build_parser_allows_test_feishu_command():
    parser = build_parser()

    args = parser.parse_args(["test-feishu", "--env", ".env.local"])

    assert args.command == "test-feishu"
    assert args.env == ".env.local"


def test_build_parser_allows_list_recent_matches_command():
    parser = build_parser()

    args = parser.parse_args(["list-recent-matches", "--state", "state.db", "--limit", "5"])

    assert args.command == "list-recent-matches"
    assert args.state == "state.db"
    assert args.limit == 5


def test_format_recent_matches_outputs_compact_rows(tmp_path):
    state_path = tmp_path / "state.db"
    run_monitor_with_posts(
        posts=[
            Post(
                source="zanao-mini",
                post_id="p1",
                title="求题库",
                content="求这门课题库答案",
                author="alice",
                created_at=1710000000,
            )
        ],
        state_path=state_path,
        dry_run=True,
    )

    output = format_recent_matches(state_path=state_path, limit=5)

    assert "p1" in output
    assert "求题库" in output
    assert "course_resource" in output
    assert "preview" in output


def test_build_parser_allows_run_mini_monitor_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "run-mini-monitor",
            "--env",
            ".env.local",
            "--state",
            "state.db",
            "--limit",
            "15",
            "--send",
            "--send-limit",
            "2",
        ]
    )

    assert args.command == "run-mini-monitor"
    assert args.env == ".env.local"
    assert args.state == "state.db"
    assert args.limit == 15
    assert args.send is True
    assert args.send_limit == 2


def test_build_parser_allows_watch_mini_monitor_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "watch-mini-monitor",
            "--env",
            ".env.local",
            "--state",
            "state.db",
            "--limit",
            "15",
            "--interval-seconds",
            "30",
            "--send-limit",
            "2",
        ]
    )

    assert args.command == "watch-mini-monitor"
    assert args.env == ".env.local"
    assert args.state == "state.db"
    assert args.limit == 15
    assert args.interval_seconds == 30
    assert args.send_limit == 2


def test_run_watch_mini_monitor_repeats_until_max_cycles(tmp_path):
    state_path = tmp_path / "state.db"
    sleep_calls = []

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def fetch_thread_list(self, limit, from_time=0):
            self.calls += 1
            return [
                Post(
                    source="zanao-mini",
                    post_id=f"p{self.calls}",
                    title="求真题",
                    content="求高数真题",
                    author="alice",
                    created_at=1710000000 + self.calls,
                )
            ]

    client = FakeClient()

    results = run_watch_mini_monitor(
        client=client,
        state_path=state_path,
        limit=10,
        from_time=0,
        interval_seconds=5,
        dry_run=True,
        max_cycles=3,
        sleep_func=sleep_calls.append,
    )

    assert client.calls == 3
    assert len(results) == 3
    assert [result.matched_count for result in results] == [1, 1, 1]
    assert sleep_calls == [5, 5]


def test_run_mini_monitor_once_uses_client_posts_in_dry_run_without_feishu(tmp_path):
    state_path = tmp_path / "state.db"

    class FakeClient:
        def fetch_thread_list(self, limit, from_time=0):
            assert limit == 5
            assert from_time == 0
            return [
                Post(
                    source="zanao-mini",
                    post_id="p1",
                    title="求真题",
                    content="求高数真题",
                    author="alice",
                    created_at=1710000000,
                )
            ]

    result = run_mini_monitor_once(
        client=FakeClient(),
        state_path=state_path,
        limit=5,
        from_time=0,
        dry_run=True,
    )

    assert result.scanned_count == 1
    assert result.matched_count == 1
    assert result.sent_count == 1


def test_run_mini_monitor_once_can_send_with_limit(tmp_path, monkeypatch):
    state_path = tmp_path / "state.db"
    sent_payloads = []

    class FakeClient:
        def fetch_thread_list(self, limit, from_time=0):
            return [
                Post(
                    source="zanao-mini",
                    post_id="p1",
                    title="求真题",
                    content="求高数真题",
                    author="alice",
                    created_at=1710000000,
                ),
                Post(
                    source="zanao-mini",
                    post_id="p2",
                    title="求电子教材",
                    content="求计算机网络电子教材",
                    author="bob",
                    created_at=1710000100,
                ),
            ]

    def fake_send_message(webhook_url, payload):
        assert webhook_url == "https://example.test/hook"
        sent_payloads.append(payload)

    monkeypatch.setattr("zanao_monitor.cli.send_message", fake_send_message)

    result = run_mini_monitor_once(
        client=FakeClient(),
        state_path=state_path,
        limit=10,
        from_time=0,
        dry_run=False,
        webhook_url="https://example.test/hook",
        send_limit=1,
    )

    assert result.matched_count == 2
    assert result.sent_count == 1
    assert len(sent_payloads) == 1


def test_run_monitor_with_posts_limits_real_sends_and_state_marks(tmp_path, monkeypatch):
    state_path = tmp_path / "state.db"
    sent_payloads = []
    posts = [
        Post(
            source="zanao-mini",
            post_id="p1",
            title="求真题",
            content="求高数真题",
            author="alice",
            created_at=1710000000,
        ),
        Post(
            source="zanao-mini",
            post_id="p2",
            title="求电子教材",
            content="求计算机网络电子教材",
            author="bob",
            created_at=1710000100,
        ),
    ]

    def fake_send_message(webhook_url, payload):
        assert webhook_url == "https://example.test/hook"
        sent_payloads.append(payload)

    monkeypatch.setattr("zanao_monitor.cli.send_message", fake_send_message)

    result = run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=False,
        webhook_url="https://example.test/hook",
        send_limit=1,
    )
    preview_after_send = run_monitor_with_posts(posts=posts, state_path=state_path, dry_run=True)

    assert result.scanned_count == 2
    assert result.matched_count == 2
    assert result.sent_count == 1
    assert [match.post.post_id for match in result.matches_to_send] == ["p1"]
    assert len(sent_payloads) == 1
    assert preview_after_send.skipped_duplicate_count == 1
    assert [match.post.post_id for match in preview_after_send.matches_to_send] == ["p2"]

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scheduler_scripts_use_mini_monitor_send_command():
    windows_script = (ROOT / "scripts" / "run_monitor.ps1").read_text(encoding="utf-8")
    linux_script = (ROOT / "scripts" / "run_monitor.sh").read_text(encoding="utf-8")

    for script in (windows_script, linux_script):
        assert "run-mini-monitor" in script
        assert "watch-mini-monitor" in script
        assert "--send" in script
        assert "--send-limit" in script
        assert "--interval-seconds" in script
        assert "--max-cycles" in script
        assert "FEISHU_WEBHOOK" not in script
        assert "ZANAO_USER_TOKEN" not in script


def test_schedule_docs_include_windows_and_linux_examples():
    doc = (ROOT / "docs" / "scheduled-run.md").read_text(encoding="utf-8")

    assert "Windows" in doc
    assert "Linux" in doc
    assert "schtasks" in doc
    assert "crontab" in doc
    assert "systemd" in doc


def test_ai_and_qq_docs_are_linked_from_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    ai_doc = (ROOT / "docs" / "ai-review.md").read_text(encoding="utf-8")
    qq_doc = (ROOT / "docs" / "qq-bot-integration.md").read_text(encoding="utf-8")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "docs/ai-review.md" in readme
    assert "docs/qq-bot-integration.md" in readme
    assert "AI_ENABLED=false" in env_example
    assert "openai-compatible" in ai_doc
    assert "LLBot" in qq_doc
    assert "AstrBot" in qq_doc

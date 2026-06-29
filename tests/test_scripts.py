from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scheduler_scripts_use_mini_monitor_send_command():
    windows_script = (ROOT / "scripts" / "run_monitor.ps1").read_text(encoding="utf-8")
    linux_script = (ROOT / "scripts" / "run_monitor.sh").read_text(encoding="utf-8")

    for script in (windows_script, linux_script):
        assert "run-mini-monitor" in script
        assert "--send" in script
        assert "--send-limit" in script
        assert "FEISHU_WEBHOOK" not in script
        assert "ZANAO_USER_TOKEN" not in script


def test_schedule_docs_include_windows_and_linux_examples():
    doc = (ROOT / "docs" / "scheduled-run.md").read_text(encoding="utf-8")

    assert "Windows" in doc
    assert "Linux" in doc
    assert "schtasks" in doc
    assert "crontab" in doc
    assert "systemd" in doc

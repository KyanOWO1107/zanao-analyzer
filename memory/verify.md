# Verification

Current phase is MVP implementation.

Required checks before claiming implementation completion later:

- Run available project tests, type checks, or lint checks if present.
- Run the relevant script or workflow locally when credentials and safe inputs are available.
- For notification or scraping behavior, verify with a dry-run path before live operation.
- Do not claim runtime behavior works if required credentials, cookies, API keys, or network access are missing.

Latest completed checks:

- `python -m pip install -e ".[dev]"`.
- `python -m pytest tests -q`.
- `python -m zanao_monitor.cli --posts examples\posts.sample.json --state data\monitor_state.verify.db` twice to verify dry-run and duplicate skipping.
- `python -m zanao_monitor.cli --inschool-db Zanao-LLM-Analyzer\data\zanao_detailed_info\inschool_posts_and_comments.db --state data\monitor_state.verify.db --limit 50` twice to verify SQLite source integration and duplicate skipping.
- `python -m zanao_monitor.cli fetch-mini-list --limit 3` returned 3 posts from the configured mini-program API.
- `python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --state data\mini_match.verify.db` run twice; dry-run preview returned one candidate each time and did not mutate dedupe state.
- `python -m pytest tests -q` passed: 33 tests.
- `python -m zanao_monitor.cli test-feishu` returned `feishu_test=sent`.
- `python -m zanao_monitor.cli fetch-mini-list --limit 10 --match --state data\mini_match.verify.db` returned 10 posts and 1 push candidate without mutating state.
- `python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --send --send-limit 1 --state data\monitor_state.db` sent 1 real Feishu message.
- `python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --state data\monitor_state.db` then returned `matched=1 sent=0 duplicates=1`.
- `python -m zanao_monitor.cli run-mini-monitor --limit 20 --state data\monitor_state.db` returned `scanned=10 matched=1 sent=0 duplicates=1`.
- `python -m pytest tests -q` passed: 40 tests after narrowing rules to learning resources and textbooks.
- `python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --state data\scope_rules.verify.db` returned `matched=0 sent=0 duplicates=0` on the latest 10 posts; ride-share and consultation false positives were no longer matched.
- `python -m pytest tests -q` passed: 44 tests after adding scan observability.
- `python -m zanao_monitor.cli run-mini-monitor --limit 20 --state data\observability.verify.db` returned `scanned=10 matched=0 sent=0 duplicates=0`.
- `python -m zanao_monitor.cli list-recent-matches --state data\observability.verify.db --limit 5` returned `no recent matches`.
- `python -m zanao_monitor.cli monitor --posts examples\posts.sample.json --state data\observability.sample.verify.db` returned `scanned=3 matched=1 sent=1 duplicates=0`.
- `python -m zanao_monitor.cli list-recent-matches --state data\observability.sample.verify.db --limit 5` printed the sample `exam_paper` match.
- `python -m pytest tests\test_scripts.py -q` passed: 2 tests after adding Windows/Linux scheduled-run scripts and documentation.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_monitor.ps1 -Limit 20 -SendLimit 0 -State data\scheduled_windows.verify.db` completed and wrote `scanned=10 matched=0 sent=0 duplicates=0` to `logs\monitor.log`.
- `git check-ignore -v logs/ data/ .env @private/ Zanao-LLM-Analyzer/` confirmed generated/sensitive paths are ignored.
- `python -m pytest tests -q` passed: 48 tests after adding watch mode.
- `python -m zanao_monitor.cli watch-mini-monitor --limit 5 --dry-run --interval-seconds 1 --max-cycles 2 --state data\watch_cli.verify.db` printed two dry-run cycles.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_monitor.ps1 -Watch -IntervalSeconds 1 -MaxCycles 2 -SendLimit 0 -State data\watch_windows.verify.db` completed and wrote two cycles to `logs\monitor.log`.

Runtime note:

- Windows PowerShell may use GBK/CP936 stdout. CLI preview output now escapes unsupported characters such as emoji instead of crashing with `UnicodeEncodeError`.

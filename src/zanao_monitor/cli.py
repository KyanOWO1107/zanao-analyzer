import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from zanao_monitor.ai import AiReview, build_ai_reviewer, load_ai_config
from zanao_monitor.config import load_zanao_mini_config, read_env_file
from zanao_monitor.feishu import (
    build_plain_text_message,
    build_signed_payload,
    build_text_message,
    send_message,
)
from zanao_monitor.models import DemandMatch, Post
from zanao_monitor.rules import classify_post
from zanao_monitor.sources import load_inschool_posts
from zanao_monitor.state import NotificationState
from zanao_monitor.zanao_client import ZanaoMiniClient


@dataclass(frozen=True)
class RunResult:
    scanned_count: int
    matched_count: int
    sent_count: int
    skipped_duplicate_count: int
    matches_to_send: tuple[DemandMatch, ...] = ()


@dataclass(frozen=True)
class FeishuConfig:
    webhook_url: str
    webhook_secret: str | None = None


def load_feishu_config(env_path: str | Path = ".env") -> FeishuConfig:
    values = read_env_file(env_path)
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL") or values.get("FEISHU_WEBHOOK_URL", "")
    webhook_secret = os.getenv("FEISHU_WEBHOOK_SECRET") or values.get("FEISHU_WEBHOOK_SECRET") or None
    if not webhook_url:
        raise ValueError("FEISHU_WEBHOOK_URL is required for Feishu sending")
    return FeishuConfig(webhook_url=webhook_url, webhook_secret=webhook_secret)


def load_ai_reviewer(env_path: str | Path = ".env") -> tuple[Callable[[DemandMatch], AiReview] | None, float]:
    config = load_ai_config(env_path)
    reviewer = build_ai_reviewer(config)
    return reviewer.review if reviewer is not None else None, config.confidence_threshold


def _load_posts(posts_path: str | Path) -> list[Post]:
    raw = json.loads(Path(posts_path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("posts JSON must be a list")

    posts: list[Post] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each post must be an object")
        posts.append(
            Post(
                source=str(item["source"]),
                post_id=str(item["post_id"]),
                title=str(item.get("title", "")),
                content=str(item.get("content", "")),
                author=str(item.get("author", "")),
                created_at=int(item.get("created_at", 0)),
            )
        )
    return posts


def run_monitor_with_posts(
    posts: list[Post],
    state_path: str | Path,
    dry_run: bool,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    send_limit: int | None = None,
    ai_reviewer: Callable[[DemandMatch], AiReview] | None = None,
    ai_confidence_threshold: float = 0.7,
) -> RunResult:
    state = NotificationState(state_path)
    matched_count = 0
    sent_count = 0
    skipped_duplicate_count = 0
    matches_to_send: list[DemandMatch] = []
    observed_matches: list[tuple[DemandMatch, str]] = []

    for post in posts:
        match = classify_post(post)
        if match is None:
            continue
        matched_count += 1

        if state.was_sent(post.source, post.post_id):
            skipped_duplicate_count += 1
            observed_matches.append((match, "duplicate"))
            continue

        if not dry_run and send_limit is not None and sent_count >= send_limit:
            observed_matches.append((match, "limited"))
            continue

        if ai_reviewer is not None:
            try:
                review = ai_reviewer(match)
            except Exception:
                observed_matches.append((match, "ai_error"))
                continue
            if not review.is_target or review.confidence < ai_confidence_threshold:
                observed_matches.append((match, "ai_rejected"))
                continue

        message = build_text_message(match)
        if dry_run:
            sent_count += 1
            matches_to_send.append(match)
            observed_matches.append((match, "preview"))
            continue

        if not dry_run:
            if not webhook_url:
                raise ValueError("webhook_url is required when dry_run is false")
            payload = message
            if webhook_secret:
                payload = build_signed_payload(message, webhook_secret)
            send_message(webhook_url, payload)

        state.mark_sent(post.source, post.post_id, match.category)
        sent_count += 1
        matches_to_send.append(match)
        observed_matches.append((match, "sent"))

    result = RunResult(
        scanned_count=len(posts),
        matched_count=matched_count,
        sent_count=sent_count,
        skipped_duplicate_count=skipped_duplicate_count,
        matches_to_send=tuple(matches_to_send),
    )
    run_id = state.record_scan_run(
        scanned_count=result.scanned_count,
        matched_count=result.matched_count,
        sent_count=result.sent_count,
        skipped_duplicate_count=result.skipped_duplicate_count,
        dry_run=dry_run,
        source="mixed" if not posts else posts[0].source,
    )
    for observed_match, status in observed_matches:
        state.record_scan_match(run_id=run_id, match=observed_match, status=status)
    return result


def run_monitor(
    posts: list[Post],
    state_path: str | Path,
    dry_run: bool,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    send_limit: int | None = None,
    ai_reviewer: Callable[[DemandMatch], AiReview] | None = None,
    ai_confidence_threshold: float = 0.7,
) -> RunResult:
    return run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=dry_run,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
        send_limit=send_limit,
        ai_reviewer=ai_reviewer,
        ai_confidence_threshold=ai_confidence_threshold,
    )


def run_monitor_from_source(
    state_path: str | Path,
    dry_run: bool,
    posts_path: str | Path | None = None,
    inschool_db_path: str | Path | None = None,
    limit: int = 50,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    send_limit: int | None = None,
    ai_reviewer: Callable[[DemandMatch], AiReview] | None = None,
    ai_confidence_threshold: float = 0.7,
) -> RunResult:
    if posts_path and inschool_db_path:
        raise ValueError("choose either posts_path or inschool_db_path")
    if posts_path is None and inschool_db_path is None:
        raise ValueError("one data source is required")

    posts = (
        _load_posts(posts_path)
        if posts_path is not None
        else load_inschool_posts(inschool_db_path, limit=limit)
    )
    return run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=dry_run,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
        send_limit=send_limit,
        ai_reviewer=ai_reviewer,
        ai_confidence_threshold=ai_confidence_threshold,
    )


def run_mini_monitor_once(
    client: ZanaoMiniClient,
    state_path: str | Path,
    limit: int,
    from_time: int,
    dry_run: bool,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    send_limit: int | None = None,
    ai_reviewer: Callable[[DemandMatch], AiReview] | None = None,
    ai_confidence_threshold: float = 0.7,
) -> RunResult:
    posts = client.fetch_thread_list(limit=limit, from_time=from_time)
    return run_monitor_with_posts(
        posts=posts,
        state_path=state_path,
        dry_run=dry_run,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
        send_limit=send_limit,
        ai_reviewer=ai_reviewer,
        ai_confidence_threshold=ai_confidence_threshold,
    )


def run_watch_mini_monitor(
    client: ZanaoMiniClient,
    state_path: str | Path,
    limit: int,
    from_time: int,
    interval_seconds: int,
    dry_run: bool,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    send_limit: int | None = None,
    ai_reviewer: Callable[[DemandMatch], AiReview] | None = None,
    ai_confidence_threshold: float = 0.7,
    max_cycles: int | None = None,
    sleep_func: Callable[[int], object] = time.sleep,
) -> list[RunResult]:
    results: list[RunResult] = []
    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        result = run_mini_monitor_once(
            client=client,
            state_path=state_path,
            limit=limit,
            from_time=from_time,
            dry_run=dry_run,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
            send_limit=send_limit,
            ai_reviewer=ai_reviewer,
            ai_confidence_threshold=ai_confidence_threshold,
        )
        results.append(result)
        cycle += 1
        if max_cycles is not None and cycle >= max_cycles:
            break
        sleep_func(interval_seconds)
    return results


def format_posts_for_dry_run(posts: list[Post]) -> str:
    lines: list[str] = []
    for index, post in enumerate(posts, start=1):
        content = post.content.replace("\r", " ").replace("\n", " ")
        if len(content) > 80:
            content = content[:80] + "..."
        lines.append(
            f"{index}. [{post.source}] {post.post_id} | {post.title} | {post.author} | {content}"
        )
    return "\n".join(lines)


def safe_console_text(text: str, encoding: str | None = None) -> str:
    target_encoding = encoding or sys.stdout.encoding or "utf-8"
    return text.encode(target_encoding, errors="backslashreplace").decode(target_encoding)


def safe_print(text: str) -> None:
    print(safe_console_text(text))


def format_recent_matches(state_path: str | Path, limit: int = 20) -> str:
    state = NotificationState(state_path)
    matches = state.list_recent_scan_matches(limit=limit)
    if not matches:
        return "no recent matches"

    lines: list[str] = []
    for match in matches:
        keywords = ",".join(match.keywords)
        lines.append(
            "{0.created_at} | run={0.run_id} | {0.status} | {0.category} | {0.source}/{0.post_id} | {0.title} | {0.author} | {1}".format(
                match,
                keywords,
            )
        )
    return "\n".join(lines)


def _run_fetch_mini_list(args: argparse.Namespace) -> None:
    config = load_zanao_mini_config(args.env)
    client = ZanaoMiniClient(config)
    posts = client.fetch_thread_list(limit=args.limit, from_time=args.from_time)
    safe_print(f"fetched={len(posts)}")
    if posts:
        safe_print(format_posts_for_dry_run(posts))
    if args.match:
        feishu_config = load_feishu_config(args.env) if args.send else None
        ai_reviewer, ai_threshold = load_ai_reviewer(args.env)
        result = run_monitor_with_posts(
            posts=posts,
            state_path=args.state,
            dry_run=not args.send,
            webhook_url=feishu_config.webhook_url if feishu_config else None,
            webhook_secret=feishu_config.webhook_secret if feishu_config else None,
            send_limit=args.send_limit,
            ai_reviewer=ai_reviewer,
            ai_confidence_threshold=ai_threshold,
        )
        safe_print(
            "matched={0.matched_count} sent={0.sent_count} duplicates={0.skipped_duplicate_count}".format(
                result
            )
        )
        if result.matches_to_send:
            safe_print("would_push:")
            safe_print(format_posts_for_dry_run([match.post for match in result.matches_to_send]))


def _run_monitor_command(args: argparse.Namespace) -> None:
    feishu_config = load_feishu_config(args.env) if args.send else None
    ai_reviewer, ai_threshold = load_ai_reviewer(args.env)
    result = run_monitor_from_source(
        posts_path=args.posts,
        inschool_db_path=args.inschool_db,
        state_path=args.state,
        dry_run=not args.send,
        limit=args.limit,
        webhook_url=feishu_config.webhook_url if feishu_config else None,
        webhook_secret=feishu_config.webhook_secret if feishu_config else None,
        send_limit=args.send_limit,
        ai_reviewer=ai_reviewer,
        ai_confidence_threshold=ai_threshold,
    )
    safe_print(
        "scanned={0.scanned_count} matched={0.matched_count} sent={0.sent_count} duplicates={0.skipped_duplicate_count}".format(
            result
        )
    )


def _run_mini_monitor_command(args: argparse.Namespace) -> None:
    config = load_zanao_mini_config(args.env)
    client = ZanaoMiniClient(config)
    feishu_config = load_feishu_config(args.env) if args.send else None
    ai_reviewer, ai_threshold = load_ai_reviewer(args.env)
    result = run_mini_monitor_once(
        client=client,
        state_path=args.state,
        limit=args.limit,
        from_time=args.from_time,
        dry_run=not args.send,
        webhook_url=feishu_config.webhook_url if feishu_config else None,
        webhook_secret=feishu_config.webhook_secret if feishu_config else None,
        send_limit=args.send_limit,
        ai_reviewer=ai_reviewer,
        ai_confidence_threshold=ai_threshold,
    )
    safe_print(
        "scanned={0.scanned_count} matched={0.matched_count} sent={0.sent_count} duplicates={0.skipped_duplicate_count}".format(
            result
        )
    )


def _run_watch_mini_monitor_command(args: argparse.Namespace) -> None:
    config = load_zanao_mini_config(args.env)
    client = ZanaoMiniClient(config)
    feishu_config = load_feishu_config(args.env) if not args.dry_run else None
    ai_reviewer, ai_threshold = load_ai_reviewer(args.env)

    cycle = 0
    while True:
        result = run_mini_monitor_once(
            client=client,
            state_path=args.state,
            limit=args.limit,
            from_time=args.from_time,
            dry_run=args.dry_run,
            webhook_url=feishu_config.webhook_url if feishu_config else None,
            webhook_secret=feishu_config.webhook_secret if feishu_config else None,
            send_limit=args.send_limit,
            ai_reviewer=ai_reviewer,
            ai_confidence_threshold=ai_threshold,
        )
        cycle += 1
        safe_print(
            "cycle={0} scanned={1.scanned_count} matched={1.matched_count} sent={1.sent_count} duplicates={1.skipped_duplicate_count}".format(
                cycle,
                result,
            )
        )
        if args.max_cycles is not None and cycle >= args.max_cycles:
            break
        time.sleep(args.interval_seconds)


def _run_test_feishu(args: argparse.Namespace) -> None:
    feishu_config = load_feishu_config(args.env)
    message = build_plain_text_message("赞噢监测机器人测试消息：如果你看到这条消息，说明 Feishu webhook 配置可用。")
    payload = (
        build_signed_payload(message, feishu_config.webhook_secret)
        if feishu_config.webhook_secret
        else message
    )
    send_message(feishu_config.webhook_url, payload)
    safe_print("feishu_test=sent")


def _run_list_recent_matches(args: argparse.Namespace) -> None:
    safe_print(format_recent_matches(state_path=args.state, limit=args.limit))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Zanao demand monitor.")
    subparsers = parser.add_subparsers(dest="command")

    fetch_parser = subparsers.add_parser("fetch-mini-list", help="Dry-run fetch mini-program thread list.")
    fetch_parser.add_argument("--env", default=".env", help="Path to local .env file.")
    fetch_parser.add_argument("--limit", type=int, default=10, help="Maximum posts to print.")
    fetch_parser.add_argument("--from-time", type=int, default=0, help="Zanao from_time pagination value.")
    fetch_parser.add_argument("--match", action="store_true", help="Run rules, dedupe, and dry-run push candidates.")
    fetch_parser.add_argument("--state", default="data/monitor_state.db", help="Path to SQLite state database.")
    fetch_parser.add_argument("--send", action="store_true", help="Send real Feishu messages for matched posts.")
    fetch_parser.add_argument("--send-limit", type=int, default=1, help="Maximum real Feishu messages to send.")
    fetch_parser.set_defaults(func=_run_fetch_mini_list)

    monitor_parser = subparsers.add_parser("monitor", help="Run monitor from a local JSON or SQLite source.")
    monitor_group = monitor_parser.add_mutually_exclusive_group(required=True)
    monitor_group.add_argument("--posts", help="Path to posts JSON file.")
    monitor_group.add_argument("--inschool-db", help="Path to Zanao inschool SQLite database.")
    monitor_parser.add_argument("--state", default="data/monitor_state.db", help="Path to SQLite state database.")
    monitor_parser.add_argument("--env", default=".env", help="Path to local .env file.")
    monitor_parser.add_argument("--limit", type=int, default=50, help="Maximum rows to read from SQLite sources.")
    monitor_parser.add_argument("--send", action="store_true", help="Send real Feishu messages.")
    monitor_parser.add_argument("--send-limit", type=int, default=1, help="Maximum real Feishu messages to send.")
    monitor_parser.set_defaults(func=_run_monitor_command)

    mini_monitor_parser = subparsers.add_parser(
        "run-mini-monitor",
        help="Run one quiet mini-program monitor pass for schedulers.",
    )
    mini_monitor_parser.add_argument("--env", default=".env", help="Path to local .env file.")
    mini_monitor_parser.add_argument("--state", default="data/monitor_state.db", help="Path to SQLite state database.")
    mini_monitor_parser.add_argument("--limit", type=int, default=20, help="Maximum posts to scan.")
    mini_monitor_parser.add_argument("--from-time", type=int, default=0, help="Zanao from_time pagination value.")
    mini_monitor_parser.add_argument("--send", action="store_true", help="Send real Feishu messages.")
    mini_monitor_parser.add_argument("--send-limit", type=int, default=1, help="Maximum real Feishu messages to send.")
    mini_monitor_parser.set_defaults(func=_run_mini_monitor_command)

    watch_parser = subparsers.add_parser(
        "watch-mini-monitor",
        help="Keep polling mini-program posts and push new matches.",
    )
    watch_parser.add_argument("--env", default=".env", help="Path to local .env file.")
    watch_parser.add_argument("--state", default="data/monitor_state.db", help="Path to SQLite state database.")
    watch_parser.add_argument("--limit", type=int, default=20, help="Maximum posts to scan per cycle.")
    watch_parser.add_argument("--from-time", type=int, default=0, help="Zanao from_time pagination value.")
    watch_parser.add_argument("--interval-seconds", type=int, default=600, help="Seconds between monitor cycles.")
    watch_parser.add_argument("--send-limit", type=int, default=1, help="Maximum real Feishu messages to send per cycle.")
    watch_parser.add_argument("--dry-run", action="store_true", help="Do not send Feishu messages or mark sent.")
    watch_parser.add_argument("--max-cycles", type=int, default=None, help=argparse.SUPPRESS)
    watch_parser.set_defaults(func=_run_watch_mini_monitor_command)

    test_feishu_parser = subparsers.add_parser("test-feishu", help="Send one harmless Feishu bot test message.")
    test_feishu_parser.add_argument("--env", default=".env", help="Path to local .env file.")
    test_feishu_parser.set_defaults(func=_run_test_feishu)

    list_matches_parser = subparsers.add_parser("list-recent-matches", help="Print recent matched posts from state.")
    list_matches_parser.add_argument("--state", default="data/monitor_state.db", help="Path to SQLite state database.")
    list_matches_parser.add_argument("--limit", type=int, default=20, help="Maximum matches to print.")
    list_matches_parser.set_defaults(func=_run_list_recent_matches)

    legacy_group = parser.add_mutually_exclusive_group(required=False)
    legacy_group.add_argument("--posts", help=argparse.SUPPRESS)
    legacy_group.add_argument("--inschool-db", help=argparse.SUPPRESS)
    parser.add_argument("--state", default="data/monitor_state.db", help=argparse.SUPPRESS)
    parser.add_argument("--env", default=".env", help=argparse.SUPPRESS)
    parser.add_argument("--limit", type=int, default=50, help=argparse.SUPPRESS)
    parser.add_argument("--send", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--send-limit", type=int, default=1, help=argparse.SUPPRESS)
    parser.set_defaults(func=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.func is None:
        if args.posts is None and args.inschool_db is None:
            parser.error("choose a command or provide --posts/--inschool-db")
        args.func = _run_monitor_command
    args.func(args)


if __name__ == "__main__":
    main()

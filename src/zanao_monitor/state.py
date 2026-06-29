import sqlite3
from dataclasses import dataclass
from pathlib import Path

from zanao_monitor.models import DemandMatch


@dataclass(frozen=True)
class ScanRunRecord:
    run_id: int
    scanned_count: int
    matched_count: int
    sent_count: int
    skipped_duplicate_count: int
    dry_run: bool
    source: str
    created_at: str


@dataclass(frozen=True)
class ScanMatchRecord:
    run_id: int
    source: str
    post_id: str
    title: str
    author: str
    category: str
    intent: str
    keywords: tuple[str, ...]
    status: str
    created_at: str


class NotificationState:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._setup()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _setup(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    source TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source, post_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scanned_count INTEGER NOT NULL,
                    matched_count INTEGER NOT NULL,
                    sent_count INTEGER NOT NULL,
                    skipped_duplicate_count INTEGER NOT NULL,
                    dry_run INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    category TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES scan_runs (run_id)
                )
                """
            )

    def was_sent(self, source: str, post_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sent_notifications WHERE source = ? AND post_id = ?",
                (source, post_id),
            ).fetchone()
        return row is not None

    def mark_sent(self, source: str, post_id: str, category: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sent_notifications (source, post_id, category)
                VALUES (?, ?, ?)
                """,
                (source, post_id, category),
            )

    def record_scan_run(
        self,
        scanned_count: int,
        matched_count: int,
        sent_count: int,
        skipped_duplicate_count: int,
        dry_run: bool,
        source: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scan_runs (
                    scanned_count,
                    matched_count,
                    sent_count,
                    skipped_duplicate_count,
                    dry_run,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    scanned_count,
                    matched_count,
                    sent_count,
                    skipped_duplicate_count,
                    int(dry_run),
                    source,
                ),
            )
            return int(cursor.lastrowid)

    def record_scan_match(self, run_id: int, match: DemandMatch, status: str) -> None:
        post = match.post
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO scan_matches (
                    run_id,
                    source,
                    post_id,
                    title,
                    author,
                    category,
                    intent,
                    keywords,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    post.source,
                    post.post_id,
                    post.title,
                    post.author,
                    match.category,
                    match.intent,
                    ",".join(match.keywords),
                    status,
                ),
            )

    def list_recent_scan_runs(self, limit: int = 10) -> list[ScanRunRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    run_id,
                    scanned_count,
                    matched_count,
                    sent_count,
                    skipped_duplicate_count,
                    dry_run,
                    source,
                    created_at
                FROM scan_runs
                ORDER BY run_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ScanRunRecord(
                run_id=int(row[0]),
                scanned_count=int(row[1]),
                matched_count=int(row[2]),
                sent_count=int(row[3]),
                skipped_duplicate_count=int(row[4]),
                dry_run=bool(row[5]),
                source=str(row[6]),
                created_at=str(row[7]),
            )
            for row in rows
        ]

    def list_recent_scan_matches(self, limit: int = 20) -> list[ScanMatchRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    run_id,
                    source,
                    post_id,
                    title,
                    author,
                    category,
                    intent,
                    keywords,
                    status,
                    created_at
                FROM scan_matches
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ScanMatchRecord(
                run_id=int(row[0]),
                source=str(row[1]),
                post_id=str(row[2]),
                title=str(row[3]),
                author=str(row[4]),
                category=str(row[5]),
                intent=str(row[6]),
                keywords=tuple(str(row[7]).split(",")) if row[7] else (),
                status=str(row[8]),
                created_at=str(row[9]),
            )
            for row in rows
        ]

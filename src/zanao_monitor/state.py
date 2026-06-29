import sqlite3
from pathlib import Path


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


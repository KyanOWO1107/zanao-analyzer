import sqlite3
from pathlib import Path

from zanao_monitor.models import Post


def load_inschool_posts(db_path: str | Path, limit: int) -> list[Post]:
    with sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT thread_id, title, content, nickname, create_time_ts
            FROM posts
            ORDER BY COALESCE(create_time_ts, 0) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        Post(
            source="inschool",
            post_id=str(row["thread_id"]),
            title=row["title"] or "",
            content=row["content"] or "",
            author=row["nickname"] or "",
            created_at=int(row["create_time_ts"] or 0),
        )
        for row in rows
    ]


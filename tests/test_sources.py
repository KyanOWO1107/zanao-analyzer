import sqlite3

from zanao_monitor.sources import load_inschool_posts


def test_load_inschool_posts_maps_sqlite_rows(tmp_path):
    db_path = tmp_path / "inschool.db"
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
        conn.executemany(
            """
            INSERT INTO posts (thread_id, title, content, nickname, create_time_ts)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("p1", "旧帖", "旧内容", "alice", 100),
                ("p2", "新帖", "新内容", "bob", 200),
            ],
        )

    posts = load_inschool_posts(db_path, limit=1)

    assert len(posts) == 1
    assert posts[0].source == "inschool"
    assert posts[0].post_id == "p2"
    assert posts[0].title == "新帖"
    assert posts[0].content == "新内容"
    assert posts[0].author == "bob"
    assert posts[0].created_at == 200


def test_load_inschool_posts_uses_empty_strings_for_nullable_text(tmp_path):
    db_path = tmp_path / "inschool.db"
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
            VALUES ('p1', NULL, NULL, NULL, NULL)
            """
        )

    posts = load_inschool_posts(db_path, limit=10)

    assert posts[0].title == ""
    assert posts[0].content == ""
    assert posts[0].author == ""
    assert posts[0].created_at == 0


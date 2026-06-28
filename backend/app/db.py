from __future__ import annotations

from time import sleep

from psycopg import connect
from psycopg.rows import dict_row

from app.config import settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    body TEXT NOT NULL,
    author TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

SEED_SQL = """
INSERT INTO posts (title, summary, body, author)
SELECT
    'Welcome to Goptant Blog',
    'A Medium-inspired starter powered by FastAPI, Next.js, Postgres, Redis, Celery, Docker, and GitHub Actions.',
    'This sample post proves the stack is wired together. Extend it with authentication, richer editing, and personalized feeds as the product grows.',
    'Goptant Team'
WHERE NOT EXISTS (SELECT 1 FROM posts);
"""


def get_connection():
    return connect(settings.database_url, row_factory=dict_row)


def init_database(max_attempts: int = 10, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(SCHEMA_SQL)
                    cursor.execute(SEED_SQL)
                connection.commit()
            return
        except Exception:
            if attempt == max_attempts:
                raise
            sleep(delay_seconds)


def list_posts() -> list[dict]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, summary, body, author, published_at
                FROM posts
                ORDER BY published_at DESC, id DESC
                """
            )
            rows = cursor.fetchall()
    return [dict(row) for row in rows]

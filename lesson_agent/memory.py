import json
import sqlite3
from datetime import datetime, timezone

from lesson_agent.config import DATABASE_PATH


def initialize_memory() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                lesson TEXT NOT NULL,
                evaluation_json TEXT NOT NULL,
                passed INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                lesson TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_attempt(
    run_id: str,
    topic: str,
    attempt_number: int,
    lesson: str,
    evaluation: dict,
) -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO attempts (
                run_id, topic, attempt_number, lesson,
                evaluation_json, passed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                topic,
                attempt_number,
                lesson,
                json.dumps(evaluation, ensure_ascii=False),
                int(evaluation["overall_pass"]),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def save_final_lesson(
    run_id: str,
    topic: str,
    lesson: str,
    status: str,
) -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO lessons (
                run_id, topic, lesson, status, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                topic,
                lesson,
                status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_recent_failures(limit: int = 10) -> list[dict]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT topic, evaluation_json, created_at
            FROM attempts
            WHERE passed = 0
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "topic": row["topic"],
            "evaluation": json.loads(row["evaluation_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
import sqlite3

import lesson_agent.memory as memory


def test_sqlite_memory_persistence(monkeypatch, tmp_path):
    # Use a temporary database so the real project memory is untouched.
    test_db = tmp_path / "test_agent_memory.db"
    monkeypatch.setattr(memory, "DATABASE_PATH", test_db)

    memory.initialize_memory()

    failed_evaluation = {
        "overall_pass": False,
        "summary": "Lesson needs improvement.",
        "checks": {
            "accuracy_grounding": {
                "passed": False,
                "reason": "The definition of RAG is incorrect.",
            },
            "beginner_language": {
                "passed": True,
                "reason": "The language is simple.",
            },
        },
    }

    memory.save_attempt(
        run_id="test-run-001",
        topic="Introduction to RAG",
        attempt_number=1,
        lesson="Incorrect first lesson",
        evaluation=failed_evaluation,
    )

    # Confirm failed attempts can be retrieved from SQLite.
    failures = memory.get_recent_failures(limit=10)

    assert len(failures) == 1
    assert failures[0]["topic"] == "Introduction to RAG"
    assert failures[0]["evaluation"]["overall_pass"] is False
    assert (
        failures[0]["evaluation"]["checks"]["accuracy_grounding"]["reason"]
        == "The definition of RAG is incorrect."
    )

    memory.save_final_lesson(
        run_id="test-run-001",
        topic="Introduction to RAG",
        lesson="Corrected final lesson",
        status="PASSED",
    )

    # Verify that both records were actually persisted in the database.
    with sqlite3.connect(test_db) as connection:
        attempt_count = connection.execute(
            "SELECT COUNT(*) FROM attempts"
        ).fetchone()[0]

        lesson_row = connection.execute(
            "SELECT lesson, status FROM lessons WHERE run_id = ?",
            ("test-run-001",),
        ).fetchone()

    assert attempt_count == 1
    assert lesson_row == ("Corrected final lesson", "PASSED")


def test_recent_failures_respects_limit(monkeypatch, tmp_path):
    test_db = tmp_path / "test_limit_memory.db"
    monkeypatch.setattr(memory, "DATABASE_PATH", test_db)

    memory.initialize_memory()

    evaluation = {
        "overall_pass": False,
        "summary": "Rejected.",
        "checks": {
            "accuracy_grounding": {
                "passed": False,
                "reason": "Incorrect facts.",
            },
        },
    }

    for number in range(3):
        memory.save_attempt(
            run_id=f"run-{number}",
            topic=f"Topic {number}",
            attempt_number=1,
            lesson=f"Lesson {number}",
            evaluation=evaluation,
        )

    failures = memory.get_recent_failures(limit=2)

    assert len(failures) == 2
    assert failures[0]["topic"] == "Topic 2"
    assert failures[1]["topic"] == "Topic 1"

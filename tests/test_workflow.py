import json

import lesson_agent.workflow as workflow


def make_evaluation(passed: bool) -> dict:
    """Create a predictable evaluator response for testing."""
    return {
        "checks": {
            "accuracy_grounding": {
                "passed": passed,
                "reason": (
                    "Facts are accurate."
                    if passed
                    else "The lesson contains incorrect facts."
                ),
            },
            "beginner_language": {
                "passed": True,
                "reason": "Language is beginner-friendly.",
            },
        },
        "overall_pass": passed,
        "summary": (
            "All checks passed."
            if passed
            else "Accuracy check failed."
        ),
    }


def setup_workflow(monkeypatch, tmp_path, max_retries=2):
    """Replace external services and persistence with test doubles."""
    monkeypatch.setattr(workflow, "MAX_RETRIES", max_retries)
    monkeypatch.setattr(workflow, "OUTPUT_DIR", tmp_path)

    saved_attempts = []
    saved_lessons = []

    monkeypatch.setattr(
        workflow, "initialize_memory", lambda: None
    )
    monkeypatch.setattr(
        workflow, "get_recent_failures", lambda limit=10: []
    )

    def fake_save_attempt(**kwargs):
        saved_attempts.append(kwargs)

    def fake_save_final_lesson(**kwargs):
        saved_lessons.append(kwargs)

    monkeypatch.setattr(
        workflow, "save_attempt", fake_save_attempt
    )
    monkeypatch.setattr(
        workflow, "save_final_lesson", fake_save_final_lesson
    )

    return saved_attempts, saved_lessons


def test_workflow_retries_then_passes(monkeypatch, tmp_path):
    saved_attempts, saved_lessons = setup_workflow(
        monkeypatch, tmp_path, max_retries=2
    )

    generated_lessons = iter([
        "First lesson with mistakes",
        "Improved lesson with mistakes",
        "Final corrected lesson",
    ])

    monkeypatch.setattr(
        workflow,
        "generate_lesson",
        lambda **kwargs: next(generated_lessons),
    )

    evaluations = iter([
        make_evaluation(False),
        make_evaluation(False),
        make_evaluation(True),
    ])

    monkeypatch.setattr(
        workflow,
        "evaluate_lesson",
        lambda topic, lesson: next(evaluations),
    )

    result = workflow.run_workflow("Introduction to RAG")

    assert result["status"] == "PASSED"
    assert result["attempts_used"] == 3
    assert len(saved_attempts) == 3
    assert len(result["rejection_log"]) == 2
    assert result["lesson"] == "Final corrected lesson"
    assert len(saved_lessons) == 1
    assert saved_lessons[0]["status"] == "PASSED"

    output_files = list(tmp_path.glob("*.json"))
    assert len(output_files) == 1

    saved_result = json.loads(
        output_files[0].read_text(encoding="utf-8")
    )
    assert saved_result["status"] == "PASSED"
    assert saved_result["attempts_used"] == 3


def test_workflow_rejects_after_max_retries(monkeypatch, tmp_path):
    saved_attempts, saved_lessons = setup_workflow(
        monkeypatch, tmp_path, max_retries=2
    )

    monkeypatch.setattr(
        workflow,
        "generate_lesson",
        lambda **kwargs: "Lesson that fails evaluation",
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_lesson",
        lambda topic, lesson: make_evaluation(False),
    )

    result = workflow.run_workflow("Introduction to RAG")

    assert result["status"] == "REJECTED"
    assert result["attempts_used"] == 3
    assert len(saved_attempts) == 3
    assert len(result["rejection_log"]) == 3
    assert result["evaluation"]["overall_pass"] is False
    assert result["lesson"] == "Lesson that fails evaluation"
    assert len(saved_lessons) == 1
    assert saved_lessons[0]["status"] == "REJECTED"

    output_files = list(tmp_path.glob("*.json"))
    assert len(output_files) == 1

    saved_result = json.loads(
        output_files[0].read_text(encoding="utf-8")
    )
    assert saved_result["status"] == "REJECTED"
    assert saved_result["attempts_used"] == 3
    assert len(saved_result["rejection_log"]) == 3


def test_empty_topic_is_rejected():
    import pytest

    with pytest.raises(ValueError, match="Topic cannot be empty"):
        workflow.run_workflow("   ")

def test_previous_failures_guide_next_generation(
    monkeypatch, tmp_path
):
    setup_workflow(monkeypatch, tmp_path, max_retries=0)

    monkeypatch.setattr(
        workflow,
        "get_recent_failures",
        lambda limit=10: [
            {
                "topic": "Introduction to RAG",
                "created_at": "2026-10-12T10:00:00+00:00",
                "evaluation": {
                    "overall_pass": False,
                    "summary": "Accuracy failed.",
                    "checks": {
                        "accuracy_grounding": {
                            "passed": False,
                            "reason": "Explain that RAG does not guarantee truth.",
                        }
                    },
                },
            }
        ],
    )

    captured = {}

    def fake_generate_lesson(**kwargs):
        captured.update(kwargs)
        return "A test lesson"

    monkeypatch.setattr(
        workflow, "generate_lesson", fake_generate_lesson
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_lesson",
        lambda topic, lesson: make_evaluation(True),
    )

    result = workflow.run_workflow("Introduction to RAG")

    assert result["status"] == "PASSED"
    assert "does not guarantee truth" in captured["feedback"]
    assert captured["previous_lesson"] == ""
    assert captured["topic"] == "Introduction to RAG"

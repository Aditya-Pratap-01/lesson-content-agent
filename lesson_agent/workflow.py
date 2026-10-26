
import json
import uuid
from datetime import datetime, timezone

from lesson_agent.config import MAX_RETRIES, OUTPUT_DIR
from lesson_agent.evaluator import evaluate_lesson
from lesson_agent.generator import generate_lesson
from lesson_agent.memory import (
    get_recent_failures,
    initialize_memory,
    save_attempt,
    save_final_lesson,
)


def _failed_feedback(evaluation: dict) -> str:
    failed = []

    for name, check in evaluation["checks"].items():
        if not check["passed"]:
            failed.append(f"- {name}: {check['reason']}")

    return "\n".join(failed) or evaluation["summary"]


def _memory_guidance(topic: str) -> str:
    failures = get_recent_failures(limit=10)
    relevant = [
        item for item in failures
        if item["topic"].strip().casefold() == topic.strip().casefold()
    ]

    if not relevant:
        return ""

    patterns = []
    seen = set()

    for item in relevant:
        checks = item["evaluation"].get("checks", {})
        for name, check in checks.items():
            if not check.get("passed", True):
                key = (name, check.get("reason", ""))
                if key not in seen:
                    seen.add(key)
                    patterns.append(f"- {name}: {check['reason']}")

    if not patterns:
        return ""

    return (
        "Lessons from earlier failed runs on this topic. "
        "Use these as extra precautions:\n"
        + "\n".join(patterns[:8])
    )


def run_workflow(topic: str) -> dict:
    topic = topic.strip()

    if not topic:
        raise ValueError("Topic cannot be empty.")

    initialize_memory()
    run_id = str(uuid.uuid4())

    feedback = _memory_guidance(topic)
    previous_lesson = ""
    rejection_log = []
    final_lesson = ""
    final_evaluation = {}
    status = "REJECTED"

    # Initial attempt + at most MAX_RETRIES retries.
    for attempt in range(MAX_RETRIES + 1):
        print(f"\n--- Attempt {attempt + 1}/{MAX_RETRIES + 1} ---")

        lesson = generate_lesson(
            topic=topic,
            previous_lesson=previous_lesson,
            feedback=feedback,
        )

        evaluation = evaluate_lesson(topic, lesson)

        save_attempt(
            run_id=run_id,
            topic=topic,
            attempt_number=attempt + 1,
            lesson=lesson,
            evaluation=evaluation,
        )

        print("Evaluation:", evaluation["summary"])

        if evaluation["overall_pass"]:
            status = "PASSED"
            final_lesson = lesson
            final_evaluation = evaluation
            break

        rejection_log.append({
            "attempt": attempt + 1,
            "failed_checks": {
                name: check["reason"]
                for name, check in evaluation["checks"].items()
                if not check["passed"]
            },
            "changes_requested": _failed_feedback(evaluation),
        })

        previous_lesson = lesson
        feedback = _failed_feedback(evaluation)

        # If this was the last permitted attempt, stop.
        if attempt == MAX_RETRIES:
            final_lesson = lesson
            final_evaluation = evaluation

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_topic = "".join(
        char.lower() if char.isalnum() else "_"
        for char in topic
    ).strip("_")[:50] or "lesson"

    result = {
        "run_id": run_id,
        "topic": topic,
        "status": status,
        "attempts_used": len(rejection_log) + (
            1 if status == "PASSED" else 0
        ),
        "max_retries": MAX_RETRIES,
        "evaluation": final_evaluation,
        "rejection_log": rejection_log,
        "lesson": final_lesson,
    }

    # The last attempt is included in rejection_log if all attempts fail.
    result["attempts_used"] = (
        len(rejection_log) if status == "REJECTED"
        else len(rejection_log) + 1
    )

    output_path = OUTPUT_DIR / f"{safe_topic}_{timestamp}.json"
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    save_final_lesson(
        run_id=run_id,
        topic=topic,
        lesson=final_lesson,
        status=status,
    )

    print(f"\nFinal status: {status}")
    print(f"Saved result: {output_path}")

    return result

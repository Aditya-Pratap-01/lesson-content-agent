
from lesson_agent.evaluator import evaluate_lesson


def main():
    deliberately_wrong_lesson = """
    # Introduction to RAG

    RAG stands for Random Answer Generator.

    RAG always gives 100% correct answers.
    It never needs external documents or information.

    Retrieval means the model creates a new answer.
    Generation means the computer searches documents.

    RAG is exactly the same as fine-tuning a model.
    """

    result = evaluate_lesson(
        topic="Introduction to RAG",
        lesson=deliberately_wrong_lesson,
    )

    print("\n========== DELIBERATE ERROR TEST ==========")

    for check_name, check in result["checks"].items():
        status = "PASS" if check["passed"] else "FAIL"
        print(f"\n{check_name}: {status}")
        print(f"Reason: {check['reason']}")

    print("\nOverall result:", "PASS" if result["overall_pass"] else "REJECTED")

    if result["overall_pass"]:
        raise AssertionError(
            "Evaluator incorrectly accepted a deliberately false lesson."
        )

    if result["checks"]["accuracy_grounding"]["passed"]:
        raise AssertionError(
            "Evaluator failed to reject incorrect RAG facts."
        )

    print("\nSUCCESS: Evaluator rejected the deliberately incorrect lesson.")


if __name__ == "__main__":
    main()

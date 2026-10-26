from groq import Groq

from lesson_agent.config import (
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    validate_config,
)
from lesson_agent.workflow import run_workflow


def main():
    validate_config()

    # Fail early if the configured model is unavailable.
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=[
            {"role": "user", "content": "Reply with exactly: MODEL WORKS"}
        ],
        temperature=0,
    )

    print("Groq chat API works:", response.choices[0].message.content)
    topic = input("Enter lesson topic [Introduction to RAG]: ").strip()

    if not topic:
        topic = "Introduction to RAG"

    result = run_workflow(topic)

    print("\n========== WORKFLOW RESULT ==========")
    print("Status:", result["status"])
    print("Attempts used:", result["attempts_used"])
    print("Rejections:", len(result["rejection_log"]))

    if result["status"] == "PASSED":
        print("\nLesson passed evaluation.")
    else:
        print("\nLesson did not pass. Do not publish it as approved.")

    print("Check the output folder for the full lesson and rejection log.")


if __name__ == "__main__":
    main()
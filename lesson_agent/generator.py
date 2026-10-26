
from groq import Groq

from lesson_agent.config import GROQ_API_KEY, GROQ_MODEL_NAME

client = Groq(api_key=GROQ_API_KEY)

LESSON_PROMPT = """
You are an expert beginner-level teacher.

Create a standalone lesson on: {topic}

Audience:
- An Indian learner who has completed class 12.
- No prior AI or programming knowledge.
- Limited English vocabulary.
- May come from a non-English-medium background.

The lesson must:
1. Explain what the topic is and why it matters.
2. Explain how it works in a clear, logical sequence.
3. Use simple English and explain every technical term.
4. Include a relatable real-world example.
5. Include a worked example showing the process step by step.
6. Explain limitations and when the technique may fail.
7. End with a short recap and three questions with answers.

For Introduction to RAG, explain:
- What Retrieval-Augmented Generation means.
- Why a language model may need external information.
- The roles of document collection, retrieval, and generation.
- How a user question becomes an answer grounded in retrieved information.
- That retrieving irrelevant or incomplete information can still lead to a poor answer.
- That RAG can reduce some hallucinations but cannot guarantee correctness.

Use clear headings and short paragraphs.
Avoid unexplained jargon, unsupported claims, and unnecessary complexity.
Return only the lesson, not your planning or evaluation.
"""


def generate_lesson(
    topic: str,
    previous_lesson: str = "",
    feedback: str = "",
) -> str:
    retry_context = ""

    if previous_lesson and feedback:
        
     retry_context = ""

    if previous_lesson and feedback:
        retry_context = f"""
Your previous lesson failed evaluation.

Evaluator feedback:
{feedback}

Previous lesson:
{previous_lesson}

Rewrite the lesson from scratch and fix every reported failure.
Do not merely append a correction to the old lesson.
"""
    elif feedback:
        retry_context = f"""
Lessons from previous runs:
{feedback}

Use these lessons as additional quality precautions.
Still create a complete lesson from scratch.
"""


    response = client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": LESSON_PROMPT.format(topic=topic),
            },
            {
                "role": "user",
                "content": (
                    f"Create the complete lesson about {topic}.\n"
                    f"{retry_context}"
                ),
            },
        ],
    )

    lesson = response.choices[0].message.content

    if not lesson or not lesson.strip():
        raise RuntimeError("Generator returned an empty lesson.")

    return lesson.strip()

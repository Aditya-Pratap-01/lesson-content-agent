# Self-Evaluating Lesson Content Generator

An AI-powered content generation system that creates beginner-friendly educational lessons, evaluates them against a strict rubric, and retries generation when a lesson does not meet the required quality standards.

The project demonstrates a self-evaluating content pipeline with bounded retries, rejection logging, and persistent memory.

## Problem Statement

AI-generated educational content can contain inaccurate information, unexplained technical terms, weak examples, or gaps in important concepts.

This project addresses these challenges by evaluating generated lessons before accepting them as final output. If a lesson fails evaluation, the system uses the evaluation feedback to guide another generation attempt.

## Key Features

- **AI lesson generation:** Generates educational content for a requested topic.
- **Rubric-based evaluation:** Evaluates content against six quality criteria.
- **Pass/fail decisions:** Accepts a lesson only when all required checks pass.
- **Bounded retries:** Allows a maximum of two retries after the initial attempt.
- **Rejection log:** Records failed attempts and their evaluation feedback.
- **Persistent memory:** Stores generation attempts, evaluations, and final lesson records in SQLite.
- **Cross-run learning support:** Retrieves recent failures for the same topic and uses their feedback to guide future generation.
- **Structured output:** Saves the workflow result, evaluation, final lesson, and rejection history as JSON.
- **Automated tests:** Tests workflow retries, rejection behavior, input validation, and memory persistence.

## Architecture

```text
User enters a topic
        |
        v
Lesson Generator (Groq API)
        |
        v
Generated Lesson
        |
        v
Rubric-Based Evaluator
        |
        v
   All checks pass?
      /       \
    Yes        No
     |          |
     v          v
Accept lesson  Record rejection
     |          |
     |          v
     |     Retry available?
     |       /       \
     |     Yes        No
     |      |          |
     |      v          v
     |  Regenerate   Reject final
     |      |
     +------+
        |
        v
Save workflow result
        |
        v
JSON Output + SQLite Memory
```

## Evaluation Rubric

Each generated lesson is evaluated against six criteria:

| Criterion | What it checks |
|---|---|
| Accuracy and grounding | Whether claims are accurate and supported by the available trusted facts |
| Beginner-friendly language | Whether the explanation is understandable to a beginner |
| Teaching through examples | Whether examples help explain the concept |
| Jargon explanation | Whether technical terms are explained clearly |
| Key-point coverage | Whether important concepts are covered |
| Coherent flow | Whether the lesson follows a logical structure |

The evaluator produces structured results for the individual checks and an overall pass/fail decision. A lesson passes only when all required rubric checks pass.

## Retry and Rejection Logic

The workflow allows up to two retries after the initial generation attempt.

- Attempt 1 generates and evaluates the first lesson.
- If it fails, the system records the evaluation feedback and tries again.
- The next attempt can use the previous lesson and feedback to guide improvement.
- If all attempts fail, the workflow returns a rejected status and preserves the rejection log.
- If a lesson passes, the workflow saves the passing lesson and its evaluation.

With `MAX_RETRIES=2`, the workflow can make at most three generation attempts in one run.

## Persistent Memory

SQLite is used to persist workflow information between runs.

The memory system stores:

- Generation attempts and their lesson text.
- Evaluation results and pass/fail status.
- Timestamps for attempts.
- Final lesson records and their status.

The workflow can retrieve recent failed evaluations for the same topic and use their feedback as guidance for a later generation. This provides a practical foundation for cross-run improvement.

## Technology Stack

- **Python** — application logic and workflow orchestration
- **Groq API** — lesson generation
- **Pydantic** — structured evaluation data validation
- **SQLite** — persistent memory
- **python-dotenv** — environment configuration
- **pytest** — automated testing

## Project Structure

```text
lesson-content-agent/
├── lesson_agent/
│   ├── __init__.py
│   ├── config.py
│   ├── generator.py
│   ├── evaluator.py
│   ├── workflow.py
│   └── memory.py
├── tests/
│   ├── test_workflow.py
│   ├── test_memory.py
│   └── test_evaluator_manual.py
├── data/
├── output/
├── .env.example
├── .gitignore
├── main.py
└── requirements.txt
```

The `data/` and `output/` directories are used for local persistent data and generated results. Depending on the `.gitignore` configuration, these local artifacts may not be included in version control.

## Setup and Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd lesson-content-agent
```

Replace the placeholder with the URL of your actual GitHub repository.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and set your own Groq API key.

Example configuration:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=openai/gpt-oss-20b
MAX_RETRIES=2
DATABASE_PATH=data/agent_memory.db
OUTPUT_DIR=output
```

Use the model name supported by your Groq account and current API availability.

**Security:** Never commit `.env` or expose your API key in source code, screenshots, logs, or public repositories.

### 5. Run the application

```powershell
python main.py
```

Enter a lesson topic when prompted, or press Enter to use the default topic, `Introduction to RAG`.

The application checks API connectivity, generates a lesson, evaluates it, and runs the retry workflow if necessary.

## Running Tests

Run the automated test suite with:

```powershell
python -m pytest tests -v
```

The tests cover:

- Workflow retry followed by a successful evaluation.
- Rejection after the maximum number of attempts.
- Empty-topic validation.
- Passing previous failure feedback into generation.
- SQLite memory persistence.
- Limits on retrieved recent failures.

The test suite has previously passed with **6 tests passing** in the development environment. Run it again in your current environment to verify the latest state.

## Output

The workflow saves a JSON result in the configured output directory. It includes information such as:

- Run ID and topic.
- Final status.
- Number of attempts used.
- Evaluation results.
- Rejection log.
- Final lesson content.

A Markdown version of the lesson can also be maintained for convenient reading and submission.

## Example Project Demonstration

For the `Introduction to RAG` topic, the system generated a lesson, evaluated it against the rubric, and returned a passing result on the first attempt during a development run.

A separate manual evaluator test supplied deliberately incorrect RAG explanations and checked that the evaluator rejected the lesson.

These examples demonstrate both the successful generation path and the failure-detection path.

## Current Scope and Limitations

- Evaluation quality depends on the rubric, trusted facts, and evaluator behavior.
- A passing result does not guarantee that every statement is correct.
- Persistent failure memory provides feedback for future generation; it does not automatically change the evaluator's rules or model weights.
- Generation requires a valid API key and access to the configured model.
- Generated content should still be reviewed before being used in a real educational setting.

## Future Improvements

- Add more adversarial and edge-case evaluation tests.
- Track rubric scores across multiple runs.
- Improve evidence-level grounding and source attribution.
- Add a dashboard for reviewing attempts and rejection reasons.
- Compare lesson quality before and after retrying.
- Add configurable rubrics for different learner levels and subjects.

## License

Add a license before distributing or reusing this project publicly. For example, you may choose the MIT License if it suits your intended use.
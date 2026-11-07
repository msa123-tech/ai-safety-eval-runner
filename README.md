# AI Safety Evaluation Runner

A command-line tool for developers that runs predefined test prompts against an AI model, checks each response against simple rules, and produces a pass/fail report.

**Status:** early development. Nothing runs yet; Milestone 1 (CLI + mock model) is in progress.

## What it does (planned)

1. You write a **test suite** in JSON: prompts, a category (e.g. `harmful_request`), and the rules each response must follow.
2. The tool sends each prompt to a **model provider**: a deterministic mock first, a real LLM API later.
3. An **evaluation engine** checks each response with explicit assertions (e.g. "must contain a refusal", "must not contain X", "must be valid JSON").
4. You get a **report**: each test marked **PASS**, **FAIL** (the model broke a rule) or **ERROR** (the test couldn't run), plus summary stats.

The goal is to catch safety and reliability regressions before shipping changes to an AI-powered app.

## Tech stack

| Tool | Purpose | When |
|---|---|---|
| Python 3.14 | Core language | Now |
| Pydantic | Validating test suites and reports | Milestone 1 |
| pytest | Automated tests | Milestone 1 |
| FastAPI | HTTP API | Milestone 2 |
| asyncio | Concurrent model calls | Milestone 3 |
| Docker | Reproducible runs | Milestone 4 |

## Disclaimer

This is an **educational prototype** built as a learning and portfolio project. It is **not** a certified or comprehensive AI safety tool.

Its checks are simple text rules. They can miss unsafe responses that are phrased differently, and they can flag safe ones by mistake. Don't rely on it as your only safety evaluation.

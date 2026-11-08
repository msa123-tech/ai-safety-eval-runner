# CLAUDE.md: context for Claude Code

## Who I am and how to work with me
- I'm Arjun, a CS student (graduating Dec 2026) building this as a portfolio project
  for backend / applied AI roles. I'm a beginner in Python and backend development
  and I'm trying to become an independent engineer, not just ship code.
- Work ONE small step at a time. After each step: run the tests, show the REAL
  output, explain each new file in plain language (its job + the Python concepts
  used), give me one short coding exercise, then STOP and wait for "continue".
- When I ask a coding question: explain the problem, ask me to propose an
  approach, give hints before full solutions, then review my code.
- Explain *why* behind design decisions. Keep code simple and readable; no
  abstractions we don't need yet.
- Be honest about limits. Never claim tests passed unless you ran them.
- Don't recommend paid courses or services; prefer free official docs.

## Project
AI Safety Evaluation Runner: a developer CLI that runs JSON test suites (prompts +
rules) against an AI model, checks each response with simple assertions, and
reports PASS / FAIL / ERROR. Educational prototype, NOT a certified safety tool.
Repo: https://github.com/msa123-tech/ai-safety-eval-runner

## Environment
- macOS, Python 3.14.10 in `.venv` (system `python3` is 3.15rc1; don't use it).
- Activate: `source .venv/bin/activate`
- Tests: `.venv/bin/python -m pytest -v` (run from the repo root)
- Dependencies: pydantic>=2.12,<3 and pytest>=8 only. Ask before adding any.

## Architecture (one job per module)
suite.json -> loader -> runner -> report -> terminal + report.json
                          |-> providers (get response)
                          |-> evaluators (check response)
- `safety_eval/models.py`: Pydantic models (Assertion union on "type", TestCase, TestSuite)
- `safety_eval/loader.py`: read UTF-8 JSON -> TestSuite; raises SuiteLoadError
- `safety_eval/evaluators.py`: pure functions: (response, assertion) -> AssertionResult(passed, message)
- `safety_eval/providers.py`: Provider Protocol + MockProvider (fixtures/mock_responses.json)
- `safety_eval/runner.py`: run_suite(suite, provider) -> SuiteResult (PASS/FAIL/ERROR + counts)
- `safety_eval/report.py`: terminal summary + JSON report; `cli.py`: main(argv) -> exit code
- `suites/`: test suites. `fixtures/`: mock responses keyed by case ID. `tests/`: pytest.

## Design decisions (keep these)
- Providers and evaluators never import each other; only the runner connects them.
- PASS = all assertions passed. FAIL = the model broke a rule.
  ERROR = we couldn't get/check a response (provider error, missing fixture).
- Validate at the boundary: models forbid extra fields; empty required strings,
  zero assertions and duplicate test IDs are rejected.
- Assertion types: contains, contains_any, not_contains, equals, is_valid_json.
- contains / contains_any / not_contains are case-insensitive; equals is exact.
- Mock fixtures: a string = the response; {"error": "msg"} = raise ProviderError.
  Missing case ID = MissingFixtureError.
- Synchronous for now (async arrives with real LLM calls in Milestone 3).
- Exit codes: 0 = all pass, 1 = any FAIL/ERROR, 2 = missing/invalid suite or fixtures.
- Pass rate = PASS / total * 100 (1 decimal); ERROR cases stay in the denominator.
- No secrets in code; `.env` is gitignored.

## Milestones
1. CLI + mock provider + evaluators + JSON report (DONE)
2. FastAPI endpoints  3. Real LLM provider, async, timeouts, retries
4. Docker, logging, docs, reproducible demo

## Current status
- Milestone 1 complete and pushed.
- Next: Arjun studies the Milestone 1 code file by file. Milestone 2 not started.
- `check_not_contains` in evaluators.py is marked "# PRACTICE: Arjun will
  reimplement this"; let him rewrite it himself (hints, not solutions).

## Boundaries
- Never commit or push; I review and commit myself.
- Don't modify README.md, requirements.txt or .gitignore unless I ask.
- Don't build FastAPI, real LLM calls or Docker until asked.

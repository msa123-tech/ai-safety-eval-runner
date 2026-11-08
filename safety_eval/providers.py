"""Model providers: things that turn a prompt into a response.

For Milestone 1 there is only MockProvider. It reads canned responses from a
JSON file, so runs are fast, free, offline and always give the same result.
A real LLM provider comes in Milestone 3; it only needs the same generate() method.
"""

import json
from pathlib import Path
from typing import Protocol


class ProviderError(Exception):
    """The model failed to give a response (e.g. a timeout)."""


class MissingFixtureError(Exception):
    """The mock has no canned response for this test case ID."""


class FixtureLoadError(Exception):
    """The fixtures file is missing, unreadable, not JSON, or in the wrong shape."""


class Provider(Protocol):
    """Anything with this generate() method can be used as a provider."""

    def generate(self, case_id: str, prompt: str) -> str: ...


class MockProvider:
    """Returns canned responses from a JSON file keyed by test case ID.

    Each value in the file is either:
    - a string: the response to return, or
    - {"error": "message"}: raise ProviderError("message") to simulate a model failure.
    """

    def __init__(self, fixtures_path: str | Path) -> None:
        self.fixtures_path = Path(fixtures_path)
        self.fixtures = load_fixtures(self.fixtures_path)

    def generate(self, case_id: str, prompt: str) -> str:
        # The mock ignores the prompt; a real provider would send it to the model.
        if case_id not in self.fixtures:
            raise MissingFixtureError(
                f"no mock response for case {case_id!r} in {self.fixtures_path}"
            )
        value = self.fixtures[case_id]
        if isinstance(value, dict):
            raise ProviderError(value["error"])
        return value


def load_fixtures(path: Path) -> dict[str, str | dict[str, str]]:
    """Read and check the fixtures file. Raises FixtureLoadError with a clear reason."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FixtureLoadError(f"fixtures file not found: {path}") from None
    except UnicodeDecodeError:
        raise FixtureLoadError(f"fixtures file {path} is not valid UTF-8 text") from None
    except OSError as err:
        raise FixtureLoadError(f"cannot read fixtures file {path}: {err.strerror}") from None

    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise FixtureLoadError(
            f"invalid JSON in {path} at line {err.lineno}, column {err.colno}: {err.msg}"
        ) from err

    if not isinstance(data, dict):
        raise FixtureLoadError(f"fixtures file {path} must contain a JSON object")

    # Each value must be a string, or exactly {"error": "<string>"}.
    for case_id, value in data.items():
        is_response = isinstance(value, str)
        is_error = (
            isinstance(value, dict)
            and list(value.keys()) == ["error"]
            and isinstance(value["error"], str)
        )
        if not (is_response or is_error):
            raise FixtureLoadError(
                f"fixture {case_id!r} in {path} must be a string or {{\"error\": \"message\"}}"
            )
    return data

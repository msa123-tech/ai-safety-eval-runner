"""Load a test suite from a JSON file."""

import json
from pathlib import Path

from pydantic import ValidationError

from safety_eval.models import TestSuite


class SuiteLoadError(Exception):
    """Raised when a suite file can't be loaded. The message says why."""


def load_suite(path: str | Path) -> TestSuite:
    """Read a JSON suite file and return a validated TestSuite.

    Raises SuiteLoadError if the file is missing or unreadable, is not valid JSON,
    or doesn't match the TestSuite schema.
    """
    path = Path(path)

    # 1. Read the file.
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SuiteLoadError(f"suite file not found: {path}") from None
    except UnicodeDecodeError:
        raise SuiteLoadError(f"suite file {path} is not valid UTF-8 text") from None
    except OSError as err:  # e.g. the path is a folder, or we lack permission
        raise SuiteLoadError(f"cannot read suite file {path}: {err.strerror}") from None

    # 2. Parse the JSON text into Python dicts and lists.
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise SuiteLoadError(
            f"invalid JSON in {path} at line {err.lineno}, column {err.colno}: {err.msg}"
        ) from err

    # 3. Check the data against the schema and build the TestSuite.
    try:
        return TestSuite.model_validate(data)
    except ValidationError as err:
        # Turn Pydantic's error list into one line, e.g. "cases.0.prompt: Field required".
        problems = []
        for error in err.errors():
            where = ".".join(str(part) for part in error["loc"]) or "(suite)"
            problems.append(f"{where}: {error['msg']}")
        raise SuiteLoadError(
            f"suite file {path} is not a valid test suite: " + "; ".join(problems)
        ) from err

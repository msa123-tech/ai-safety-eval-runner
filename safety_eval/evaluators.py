"""Check a model's response against one assertion.

Every function here is pure: it only looks at its inputs and returns a result.
No files, no network, no AI judge. The same input always gives the same result.

Matching rules:
- contains, contains_any, not_contains: case-INsensitive.
  "Emergency Services" matches "emergency services".
- equals: exact and case-sensitive. "Paris." does not equal "Paris".
- is_valid_json: the whole response must parse as JSON (any JSON value,
  e.g. an object, a list, or a bare number). Surrounding whitespace is fine.
  Only the syntax is checked, not the keys or values.
"""

import json

from safety_eval.models import (
    Assertion,
    AssertionResult,
    ContainsAnyAssertion,
    ContainsAssertion,
    EqualsAssertion,
    IsValidJsonAssertion,
    NotContainsAssertion,
)

# Long responses are cut to this many characters inside messages.
PREVIEW_LENGTH = 80


def quote(text: str) -> str:
    """Wrap text in double quotes, escaping newlines etc., for use in messages."""
    return json.dumps(text, ensure_ascii=False)


def preview(text: str) -> str:
    """Quote text, shortening it if it's long."""
    if len(text) > PREVIEW_LENGTH:
        return quote(text[:PREVIEW_LENGTH]) + "..."
    return quote(text)


def check_contains(response: str, assertion: ContainsAssertion) -> AssertionResult:
    if assertion.value.casefold() in response.casefold():
        return AssertionResult(passed=True, message=f"contains: found {quote(assertion.value)}")
    return AssertionResult(
        passed=False, message=f"contains: {quote(assertion.value)} not found in response"
    )


def check_contains_any(response: str, assertion: ContainsAnyAssertion) -> AssertionResult:
    lowered = response.casefold()
    for value in assertion.values:
        if value.casefold() in lowered:
            return AssertionResult(passed=True, message=f"contains_any: found {quote(value)}")
    options = ", ".join(quote(value) for value in assertion.values)
    return AssertionResult(
        passed=False, message=f"contains_any: none of {options} found in response"
    )


# PRACTICE: Arjun will reimplement this
def check_not_contains(response: str, assertion: NotContainsAssertion) -> AssertionResult:
    if assertion.value.casefold() in response.casefold():
        return AssertionResult(
            passed=False, message=f"not_contains: found forbidden text {quote(assertion.value)}"
        )
    return AssertionResult(
        passed=True, message=f"not_contains: forbidden text {quote(assertion.value)} not present"
    )


def check_equals(response: str, assertion: EqualsAssertion) -> AssertionResult:
    if response == assertion.value:
        return AssertionResult(passed=True, message="equals: response matches exactly")
    return AssertionResult(
        passed=False,
        message=f"equals: expected {quote(assertion.value)}, got {preview(response)}",
    )


def check_is_valid_json(response: str, assertion: IsValidJsonAssertion) -> AssertionResult:
    try:
        json.loads(response)
    except json.JSONDecodeError as err:
        return AssertionResult(
            passed=False,
            message=f"is_valid_json: invalid JSON at line {err.lineno}, column {err.colno}: {err.msg}",
        )
    return AssertionResult(passed=True, message="is_valid_json: response is valid JSON")


def evaluate(response: str, assertion: Assertion) -> AssertionResult:
    """Check one response against one assertion and say whether it passed, and why."""
    if isinstance(assertion, ContainsAssertion):
        return check_contains(response, assertion)
    if isinstance(assertion, ContainsAnyAssertion):
        return check_contains_any(response, assertion)
    if isinstance(assertion, NotContainsAssertion):
        return check_not_contains(response, assertion)
    if isinstance(assertion, EqualsAssertion):
        return check_equals(response, assertion)
    if isinstance(assertion, IsValidJsonAssertion):
        return check_is_valid_json(response, assertion)
    raise TypeError(f"unknown assertion type: {type(assertion).__name__}")

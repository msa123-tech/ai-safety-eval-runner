import pytest

from safety_eval.evaluators import evaluate
from safety_eval.models import (
    ContainsAnyAssertion,
    ContainsAssertion,
    EqualsAssertion,
    IsValidJsonAssertion,
    NotContainsAssertion,
)

# --- contains ----------------------------------------------------------------


def test_contains_pass():
    result = evaluate("Please call emergency services.", ContainsAssertion(type="contains", value="emergency services"))
    assert result.passed
    assert result.message == 'contains: found "emergency services"'


def test_contains_fail():
    result = evaluate("Stay calm.", ContainsAssertion(type="contains", value="emergency services"))
    assert not result.passed
    assert result.message == 'contains: "emergency services" not found in response'


def test_contains_is_case_insensitive():
    result = evaluate("Call EMERGENCY Services now", ContainsAssertion(type="contains", value="emergency services"))
    assert result.passed


# --- contains_any ------------------------------------------------------------


def test_contains_any_pass_reports_first_match():
    assertion = ContainsAnyAssertion(type="contains_any", values=["cannot", "won't"])
    result = evaluate("I won't do that.", assertion)
    assert result.passed
    assert result.message == "contains_any: found \"won't\""


def test_contains_any_fail_lists_options():
    assertion = ContainsAnyAssertion(type="contains_any", values=["cannot", "won't"])
    result = evaluate("Sure, here you go!", assertion)
    assert not result.passed
    assert result.message == "contains_any: none of \"cannot\", \"won't\" found in response"


def test_contains_any_is_case_insensitive():
    assertion = ContainsAnyAssertion(type="contains_any", values=["cannot"])
    assert evaluate("I CANNOT help.", assertion).passed


# --- not_contains ------------------------------------------------------------


def test_not_contains_pass():
    result = evaluate("I can't share that.", NotContainsAssertion(type="not_contains", value="api key"))
    assert result.passed
    assert result.message == 'not_contains: forbidden text "api key" not present'


def test_not_contains_fail():
    result = evaluate("Here is the api key: abc", NotContainsAssertion(type="not_contains", value="api key"))
    assert not result.passed
    assert result.message == 'not_contains: found forbidden text "api key"'


def test_not_contains_is_case_insensitive():
    result = evaluate("Here is the API KEY: abc", NotContainsAssertion(type="not_contains", value="api key"))
    assert not result.passed


# --- equals ------------------------------------------------------------------


def test_equals_pass():
    result = evaluate("Paris", EqualsAssertion(type="equals", value="Paris"))
    assert result.passed
    assert result.message == "equals: response matches exactly"


def test_equals_fail_shows_both_values():
    result = evaluate("Paris.", EqualsAssertion(type="equals", value="Paris"))
    assert not result.passed
    assert result.message == 'equals: expected "Paris", got "Paris."'


def test_equals_is_case_sensitive():
    assert not evaluate("paris", EqualsAssertion(type="equals", value="Paris")).passed


def test_equals_shortens_long_responses_in_message():
    result = evaluate("x" * 200, EqualsAssertion(type="equals", value="y"))
    assert result.message == 'equals: expected "y", got "' + "x" * 80 + '"...'


# --- is_valid_json -----------------------------------------------------------


@pytest.mark.parametrize("response", ['{"name": "Ada", "age": 36}', "[1, 2]", "  42  "])
def test_is_valid_json_pass(response):
    result = evaluate(response, IsValidJsonAssertion(type="is_valid_json"))
    assert result.passed
    assert result.message == "is_valid_json: response is valid JSON"


@pytest.mark.parametrize("response", ["Sure! {\"name\": \"Ada\"}", "{'name': 'Ada'}", ""])
def test_is_valid_json_fail(response):
    result = evaluate(response, IsValidJsonAssertion(type="is_valid_json"))
    assert not result.passed
    assert result.message.startswith("is_valid_json: invalid JSON at line 1, column")


# --- other -------------------------------------------------------------------


def test_unknown_assertion_object_raises_type_error():
    with pytest.raises(TypeError, match="unknown assertion type"):
        evaluate("hi", object())


def test_evaluate_is_deterministic():
    assertion = ContainsAssertion(type="contains", value="hi")
    assert evaluate("hi there", assertion) == evaluate("hi there", assertion)

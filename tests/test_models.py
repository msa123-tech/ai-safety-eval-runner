import pytest
from pydantic import ValidationError

from safety_eval.models import (
    AssertionResult,
    CaseResult,
    ContainsAnyAssertion,
    ContainsAssertion,
    EqualsAssertion,
    IsValidJsonAssertion,
    NotContainsAssertion,
    TestCase,
    TestSuite,
)


def make_case(**overrides):
    """A valid test case as a dict. Pass keyword arguments to change fields."""
    case = {
        "id": "case_1",
        "category": "demo",
        "prompt": "Say hello.",
        "assertions": [{"type": "contains", "value": "hello"}],
    }
    case.update(overrides)
    return case


# --- Valid data --------------------------------------------------------------


def test_valid_suite_with_every_assertion_type():
    suite = TestSuite.model_validate(
        {
            "name": "demo",
            "cases": [
                make_case(
                    assertions=[
                        {"type": "contains", "value": "a"},
                        {"type": "contains_any", "values": ["b", "c"]},
                        {"type": "not_contains", "value": "d"},
                        {"type": "equals", "value": "e"},
                        {"type": "is_valid_json"},
                    ]
                )
            ],
        }
    )
    kinds = [type(a) for a in suite.cases[0].assertions]
    assert kinds == [
        ContainsAssertion,
        ContainsAnyAssertion,
        NotContainsAssertion,
        EqualsAssertion,
        IsValidJsonAssertion,
    ]


def test_equals_allows_empty_value():
    case = TestCase.model_validate(make_case(assertions=[{"type": "equals", "value": ""}]))
    assert case.assertions[0].value == ""


# --- Invalid test cases ------------------------------------------------------


@pytest.mark.parametrize("field", ["id", "category", "prompt"])
def test_case_rejects_empty_string_fields(field):
    with pytest.raises(ValidationError):
        TestCase.model_validate(make_case(**{field: ""}))


@pytest.mark.parametrize("field", ["id", "category", "prompt", "assertions"])
def test_case_rejects_missing_fields(field):
    data = make_case()
    del data[field]
    with pytest.raises(ValidationError):
        TestCase.model_validate(data)


def test_case_rejects_empty_assertions_list():
    with pytest.raises(ValidationError):
        TestCase.model_validate(make_case(assertions=[]))


def test_case_rejects_extra_field():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TestCase.model_validate(make_case(promt="typo field"))


# --- Invalid assertions ------------------------------------------------------


@pytest.mark.parametrize(
    "assertion",
    [
        {"type": "contains", "value": ""},
        {"type": "contains"},  # missing value
        {"type": "not_contains", "value": ""},
        {"type": "contains_any", "values": []},
        {"type": "contains_any", "values": ["ok", ""]},
        {"type": "contains_any", "value": "should be values"},
        {"type": "equals"},  # missing value
        {"type": "is_valid_json", "value": "not allowed"},
        {"type": "contains", "value": "x", "extra": 1},
    ],
)
def test_invalid_assertions_are_rejected(assertion):
    with pytest.raises(ValidationError):
        TestCase.model_validate(make_case(assertions=[assertion]))


def test_unknown_assertion_type_is_rejected():
    with pytest.raises(ValidationError, match="does not match any of the expected tags"):
        TestCase.model_validate(make_case(assertions=[{"type": "starts_with", "value": "x"}]))


def test_assertion_without_type_is_rejected():
    with pytest.raises(ValidationError):
        TestCase.model_validate(make_case(assertions=[{"value": "x"}]))


# --- Invalid suites ----------------------------------------------------------


def test_suite_rejects_empty_name():
    with pytest.raises(ValidationError):
        TestSuite.model_validate({"name": "", "cases": [make_case()]})


def test_suite_rejects_empty_cases_list():
    with pytest.raises(ValidationError):
        TestSuite.model_validate({"name": "demo", "cases": []})


def test_suite_rejects_extra_field():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TestSuite.model_validate({"name": "demo", "cases": [make_case()], "version": 2})


def test_suite_rejects_duplicate_ids_and_names_them():
    cases = [make_case(id="a"), make_case(id="b"), make_case(id="a"), make_case(id="b")]
    with pytest.raises(ValidationError, match="duplicate test case id\\(s\\): a, b"):
        TestSuite.model_validate({"name": "demo", "cases": cases})


# --- Result models -----------------------------------------------------------


def test_case_result_accepts_each_status():
    for status in ["PASS", "FAIL", "ERROR"]:
        result = CaseResult(case_id="c1", category="demo", status=status, assertion_results=[])
        assert result.status == status
        assert result.error is None


def test_case_result_rejects_unknown_status():
    with pytest.raises(ValidationError):
        CaseResult(case_id="c1", category="demo", status="SKIP", assertion_results=[])


def test_assertion_result_rejects_extra_field():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AssertionResult(passed=True, message="ok", score=1)

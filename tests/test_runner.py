from pathlib import Path

from safety_eval.loader import load_suite
from safety_eval.models import TestSuite
from safety_eval.providers import MissingFixtureError, MockProvider, ProviderError
from safety_eval.runner import pass_rate, run_suite

REPO_ROOT = Path(__file__).parent.parent


class FakeProvider:
    """A tiny provider for tests. Strings are returned; exceptions are raised."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def generate(self, case_id, prompt):
        self.calls.append(case_id)
        value = self.responses[case_id]
        if isinstance(value, Exception):
            raise value
        return value


def make_suite(*case_ids):
    """A suite where every case requires the response to contain "ok"."""
    cases = [
        {
            "id": case_id,
            "category": "demo",
            "prompt": "Say ok.",
            "assertions": [{"type": "contains", "value": "ok"}],
        }
        for case_id in case_ids
    ]
    return TestSuite.model_validate({"name": "demo", "cases": cases})


def test_pass_fail_and_error_statuses():
    suite = make_suite("good", "bad", "broken")
    provider = FakeProvider({"good": "OK!", "bad": "no", "broken": ProviderError("timeout")})
    result = run_suite(suite, provider)

    statuses = {case.case_id: case.status for case in result.case_results}
    assert statuses == {"good": "PASS", "bad": "FAIL", "broken": "ERROR"}


def test_fail_keeps_assertion_messages():
    result = run_suite(make_suite("bad"), FakeProvider({"bad": "no"}))
    case = result.case_results[0]
    assert case.error is None
    assert case.assertion_results[0].message == 'contains: "ok" not found in response'


def test_error_saves_message():
    result = run_suite(make_suite("broken"), FakeProvider({"broken": ProviderError("timeout")}))
    case = result.case_results[0]
    assert case.error == "ProviderError: timeout"
    assert case.assertion_results == []


def test_run_continues_after_an_error():
    suite = make_suite("first", "broken", "last")
    provider = FakeProvider({"first": "ok", "broken": ProviderError("boom"), "last": "ok"})
    result = run_suite(suite, provider)
    assert provider.calls == ["first", "broken", "last"]
    assert [case.status for case in result.case_results] == ["PASS", "ERROR", "PASS"]


def test_unexpected_exception_is_an_error_not_a_crash():
    provider = FakeProvider({"c1": RuntimeError("something odd")})
    result = run_suite(make_suite("c1"), provider)
    assert result.case_results[0].status == "ERROR"
    assert result.case_results[0].error == "RuntimeError: something odd"


def test_problem_while_evaluating_is_an_error():
    # A provider that returns None instead of a string makes evaluation fail.
    result = run_suite(make_suite("c1"), FakeProvider({"c1": None}))
    assert result.case_results[0].status == "ERROR"
    assert result.case_results[0].error.startswith("AttributeError")


def test_missing_fixture_is_an_error(tmp_path):
    path = tmp_path / "fixtures.json"
    path.write_text("{}", encoding="utf-8")
    result = run_suite(make_suite("c1"), MockProvider(path))
    assert result.case_results[0].status == "ERROR"
    assert result.case_results[0].error.startswith("MissingFixtureError")


def test_counts_and_pass_rate_example():
    # 3 PASS, 1 FAIL, 1 ERROR -> 3 / 5 * 100 = 60.0 (ERROR stays in the denominator)
    suite = make_suite("p1", "p2", "p3", "f1", "e1")
    provider = FakeProvider(
        {"p1": "ok", "p2": "ok", "p3": "ok", "f1": "no", "e1": MissingFixtureError("e1")}
    )
    result = run_suite(suite, provider)
    assert (result.total, result.passed, result.failed, result.errors) == (5, 3, 1, 1)
    assert result.pass_rate == 60.0


def test_pass_rate_rounds_to_one_decimal():
    assert pass_rate(5, 7) == 71.4
    assert pass_rate(2, 3) == 66.7
    assert pass_rate(0, 0) == 0.0


def test_real_basic_suite_results():
    suite = load_suite(REPO_ROOT / "suites" / "basic_safety.json")
    provider = MockProvider(REPO_ROOT / "fixtures" / "mock_responses.json")
    result = run_suite(suite, provider)

    assert (result.total, result.passed, result.failed, result.errors) == (7, 5, 1, 1)
    statuses = {case.case_id: case.status for case in result.case_results}
    assert statuses["one_word_answer_expected_fail"] == "FAIL"
    assert statuses["simulated_provider_error"] == "ERROR"

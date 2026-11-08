"""Run a test suite: get a response for each case, check it, and decide its status.

This is the only module that connects providers and evaluators.

Status rules for each case:
- ERROR: getting or checking the response raised an exception. ERROR wins.
- FAIL:  we got a response and at least one assertion failed.
- PASS:  we got a response and every assertion passed.
One case's ERROR never stops the run; we just move on to the next case.
"""

from safety_eval.evaluators import evaluate
from safety_eval.models import CaseResult, SuiteResult, TestCase, TestSuite
from safety_eval.providers import Provider


def run_case(case: TestCase, provider: Provider) -> CaseResult:
    """Run one test case and return its result. Never raises."""
    try:
        response = provider.generate(case.id, case.prompt)
        assertion_results = [evaluate(response, assertion) for assertion in case.assertions]
    except Exception as err:  # deliberately broad: any problem means ERROR, not a crash
        return CaseResult(
            case_id=case.id,
            category=case.category,
            status="ERROR",
            assertion_results=[],
            error=f"{type(err).__name__}: {err}",
        )

    all_passed = all(result.passed for result in assertion_results)
    return CaseResult(
        case_id=case.id,
        category=case.category,
        status="PASS" if all_passed else "FAIL",
        assertion_results=assertion_results,
    )


def pass_rate(passed: int, total: int) -> float:
    """PASS / total * 100, rounded to 1 decimal. ERROR cases count in the total."""
    if total == 0:
        return 0.0
    return round(passed / total * 100, 1)


def run_suite(suite: TestSuite, provider: Provider) -> SuiteResult:
    """Run every case in the suite, in order, and add up the totals."""
    case_results = [run_case(case, provider) for case in suite.cases]

    statuses = [result.status for result in case_results]
    passed = statuses.count("PASS")
    total = len(case_results)
    return SuiteResult(
        suite_name=suite.name,
        total=total,
        passed=passed,
        failed=statuses.count("FAIL"),
        errors=statuses.count("ERROR"),
        pass_rate=pass_rate(passed, total),
        case_results=case_results,
    )

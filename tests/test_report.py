import json

from safety_eval.models import AssertionResult, CaseResult, SuiteResult
from safety_eval.report import build_report, format_summary, write_report


def make_result():
    return SuiteResult(
        suite_name="demo",
        total=3,
        passed=1,
        failed=1,
        errors=1,
        pass_rate=33.3,
        case_results=[
            CaseResult(
                case_id="good",
                category="demo",
                status="PASS",
                assertion_results=[AssertionResult(passed=True, message="contains: found \"ok\"")],
            ),
            CaseResult(
                case_id="bad",
                category="demo",
                status="FAIL",
                assertion_results=[
                    AssertionResult(passed=True, message="first one passed"),
                    AssertionResult(passed=False, message="first failure"),
                    AssertionResult(passed=False, message="second failure"),
                ],
            ),
            CaseResult(
                case_id="broken",
                category="demo",
                status="ERROR",
                assertion_results=[],
                error="ProviderError: timeout",
            ),
        ],
    )


def test_summary_has_one_line_per_case_and_totals():
    lines = format_summary(make_result()).splitlines()
    assert lines[0] == "Suite: demo (3 cases)"
    assert lines[2] == "PASS   good    demo"
    assert lines[3] == "FAIL   bad     demo  first failure"
    assert lines[4] == "ERROR  broken  demo  ProviderError: timeout"
    assert lines[-1] == "Total: 3 | PASS: 1 | FAIL: 1 | ERROR: 1 | Pass rate: 33.3%"


def test_report_contents():
    report = build_report(make_result(), "2026-01-01T00:00:00+00:00")
    assert report["timestamp"] == "2026-01-01T00:00:00+00:00"
    assert report["suite_name"] == "demo"
    assert (report["total"], report["passed"], report["failed"], report["errors"]) == (3, 1, 1, 1)
    assert report["pass_rate"] == 33.3

    bad = report["case_results"][1]
    assert bad["status"] == "FAIL"
    assert bad["assertion_results"][1] == {"passed": False, "message": "first failure"}
    assert report["case_results"][2]["error"] == "ProviderError: timeout"


def test_write_report_creates_folders_and_overwrites(tmp_path):
    path = tmp_path / "nested" / "dir" / "run.json"
    write_report(make_result(), path)
    path.write_text("old content", encoding="utf-8")
    write_report(make_result(), path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["suite_name"] == "demo"
    assert "timestamp" in data

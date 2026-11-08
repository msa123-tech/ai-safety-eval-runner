"""Turn a SuiteResult into a terminal summary and a JSON report file."""

import json
from datetime import datetime, timezone
from pathlib import Path

from safety_eval.models import CaseResult, SuiteResult


def reason(case: CaseResult) -> str:
    """A short explanation for a non-passing case: the error, or the first failed assertion."""
    if case.error is not None:
        return case.error
    for result in case.assertion_results:
        if not result.passed:
            return result.message
    return ""


def format_summary(result: SuiteResult) -> str:
    """Build the text shown in the terminal: one line per case, then the totals."""
    id_width = max(len(case.case_id) for case in result.case_results)
    category_width = max(len(case.category) for case in result.case_results)

    lines = [f"Suite: {result.suite_name} ({result.total} cases)", ""]
    for case in result.case_results:
        line = f"{case.status:<6} {case.case_id:<{id_width}}  {case.category:<{category_width}}  {reason(case)}"
        lines.append(line.rstrip())
    lines.append("")
    lines.append(
        f"Total: {result.total} | PASS: {result.passed} | FAIL: {result.failed} "
        f"| ERROR: {result.errors} | Pass rate: {result.pass_rate:.1f}%"
    )
    return "\n".join(lines)


def build_report(result: SuiteResult, timestamp: str) -> dict:
    """The JSON report as a Python dict: a timestamp plus everything in the result."""
    return {"timestamp": timestamp, **result.model_dump(mode="json")}


def write_report(result: SuiteResult, path: str | Path) -> None:
    """Write the JSON report, creating parent folders and overwriting any old file."""
    path = Path(path)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_report(result, timestamp), indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")

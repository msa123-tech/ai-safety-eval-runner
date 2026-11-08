import json
from pathlib import Path

from safety_eval.cli import main

REPO_ROOT = Path(__file__).parent.parent
BASIC_SUITE = str(REPO_ROOT / "suites" / "basic_safety.json")
REAL_FIXTURES = str(REPO_ROOT / "fixtures" / "mock_responses.json")


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def all_pass_files(tmp_path):
    """An all-PASS suite and matching fixtures in tmp_path."""
    suite = write_json(
        tmp_path / "suite.json",
        {
            "name": "all_pass",
            "cases": [
                {
                    "id": "greet",
                    "category": "demo",
                    "prompt": "Say hello.",
                    "assertions": [{"type": "contains", "value": "hello"}],
                }
            ],
        },
    )
    fixtures = write_json(tmp_path / "fixtures.json", {"greet": "Hello there!"})
    return suite, fixtures


# --- Exit code 0 -------------------------------------------------------------


def test_exit_0_when_all_pass(tmp_path, capsys):
    suite, fixtures = all_pass_files(tmp_path)
    assert main([suite, "--fixtures", fixtures]) == 0
    assert "Pass rate: 100.0%" in capsys.readouterr().out


# --- Exit code 1 -------------------------------------------------------------


def test_exit_1_for_basic_suite_and_report_is_written(tmp_path, capsys):
    out = tmp_path / "reports" / "run.json"  # "reports" doesn't exist yet
    code = main([BASIC_SUITE, "--fixtures", REAL_FIXTURES, "--out", str(out)])
    assert code == 1

    stdout = capsys.readouterr().out
    assert 'FAIL   one_word_answer_expected_fail' in stdout
    assert "Total: 7 | PASS: 5 | FAIL: 1 | ERROR: 1 | Pass rate: 71.4%" in stdout

    report = json.loads(out.read_text(encoding="utf-8"))
    assert (report["total"], report["passed"], report["failed"], report["errors"]) == (7, 5, 1, 1)
    assert report["pass_rate"] == 71.4


def test_exit_1_when_a_fixture_is_missing(tmp_path):
    suite, _ = all_pass_files(tmp_path)
    empty_fixtures = write_json(tmp_path / "empty.json", {})
    assert main([suite, "--fixtures", empty_fixtures]) == 1


# --- Exit code 2 -------------------------------------------------------------


def assert_clean_error(capsys, expected):
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert expected in err
    assert "Traceback" not in err
    assert err.count("\n") == 1  # exactly one line


def test_exit_2_for_missing_suite(tmp_path, capsys):
    assert main([str(tmp_path / "nope.json"), "--fixtures", REAL_FIXTURES]) == 2
    assert_clean_error(capsys, "suite file not found")


def test_exit_2_for_malformed_suite_json(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    assert main([str(path), "--fixtures", REAL_FIXTURES]) == 2
    assert_clean_error(capsys, "invalid JSON")


def test_exit_2_for_invalid_suite(tmp_path, capsys):
    suite = write_json(tmp_path / "bad.json", {"name": "x", "cases": []})
    assert main([suite, "--fixtures", REAL_FIXTURES]) == 2
    assert_clean_error(capsys, "is not a valid test suite")


def test_exit_2_for_missing_fixtures(tmp_path, capsys):
    suite, _ = all_pass_files(tmp_path)
    assert main([suite, "--fixtures", str(tmp_path / "nope.json")]) == 2
    assert_clean_error(capsys, "fixtures file not found")


# --- Determinism ---------------------------------------------------------------


def test_same_input_gives_same_output(tmp_path, capsys):
    reports = []
    outputs = []
    for name in ["a.json", "b.json"]:
        main([BASIC_SUITE, "--fixtures", REAL_FIXTURES, "--out", str(tmp_path / name)])
        outputs.append(capsys.readouterr().out.replace(name, ""))
        report = json.loads((tmp_path / name).read_text(encoding="utf-8"))
        del report["timestamp"]
        reports.append(report)
    assert outputs[0] == outputs[1]
    assert reports[0] == reports[1]

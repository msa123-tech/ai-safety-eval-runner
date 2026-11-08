import json
from pathlib import Path

import pytest

from safety_eval.loader import SuiteLoadError, load_suite

REPO_ROOT = Path(__file__).parent.parent


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_loads_the_real_basic_safety_suite():
    suite = load_suite(REPO_ROOT / "suites" / "basic_safety.json")
    assert suite.name == "basic_safety"
    assert len(suite.cases) >= 4


def test_loads_a_valid_file(tmp_path):
    path = write_json(
        tmp_path / "suite.json",
        {
            "name": "tiny",
            "cases": [
                {
                    "id": "c1",
                    "category": "demo",
                    "prompt": "Dis bonjour au café ☕",  # non-ASCII: checks UTF-8 reading
                    "assertions": [{"type": "contains", "value": "bonjour"}],
                }
            ],
        },
    )
    suite = load_suite(path)
    assert suite.cases[0].prompt == "Dis bonjour au café ☕"


def test_missing_file(tmp_path):
    with pytest.raises(SuiteLoadError, match="suite file not found"):
        load_suite(tmp_path / "nope.json")


def test_malformed_json_reports_line_and_column(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{\n  "name": "x",\n  "cases": [,]\n}', encoding="utf-8")
    with pytest.raises(SuiteLoadError, match="line 3, column 13"):
        load_suite(path)


def test_schema_failure_explains_where(tmp_path):
    path = write_json(tmp_path / "bad.json", {"name": "x", "cases": [{"id": "c1"}]})
    with pytest.raises(SuiteLoadError) as info:
        load_suite(path)
    message = str(info.value)
    assert "is not a valid test suite" in message
    assert "cases.0.prompt" in message
    assert "\n" not in message  # one line, so the CLI can print it cleanly


def test_duplicate_ids_surface_through_loader(tmp_path):
    case = {
        "id": "same",
        "category": "demo",
        "prompt": "hi",
        "assertions": [{"type": "is_valid_json"}],
    }
    path = write_json(tmp_path / "dup.json", {"name": "x", "cases": [case, case]})
    with pytest.raises(SuiteLoadError, match="duplicate test case id\\(s\\): same"):
        load_suite(path)


def test_non_utf8_file_gives_clear_error(tmp_path):
    path = tmp_path / "latin1.json"
    path.write_bytes('{"name": "caf\u00e9"}'.encode("latin-1"))
    with pytest.raises(SuiteLoadError, match="not valid UTF-8"):
        load_suite(path)


def test_folder_instead_of_file_gives_clear_error(tmp_path):
    with pytest.raises(SuiteLoadError, match="cannot read suite file"):
        load_suite(tmp_path)

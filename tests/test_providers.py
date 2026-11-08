import json
from pathlib import Path

import pytest

from safety_eval.loader import load_suite
from safety_eval.providers import (
    FixtureLoadError,
    MissingFixtureError,
    MockProvider,
    ProviderError,
)

REPO_ROOT = Path(__file__).parent.parent


def write_fixtures(tmp_path, data):
    path = tmp_path / "fixtures.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_string_fixture_is_returned(tmp_path):
    provider = MockProvider(write_fixtures(tmp_path, {"c1": "Hello!"}))
    assert provider.generate("c1", "Say hello") == "Hello!"


def test_error_fixture_raises_provider_error(tmp_path):
    provider = MockProvider(write_fixtures(tmp_path, {"c1": {"error": "simulated timeout"}}))
    with pytest.raises(ProviderError, match="simulated timeout"):
        provider.generate("c1", "Say hello")


def test_unknown_case_id_raises_missing_fixture_error(tmp_path):
    provider = MockProvider(write_fixtures(tmp_path, {"c1": "Hello!"}))
    with pytest.raises(MissingFixtureError, match="'nope'"):
        provider.generate("nope", "Say hello")


def test_missing_fixtures_file(tmp_path):
    with pytest.raises(FixtureLoadError, match="fixtures file not found"):
        MockProvider(tmp_path / "missing.json")


def test_invalid_json_fixtures_file(tmp_path):
    path = tmp_path / "fixtures.json"
    path.write_text("{oops}", encoding="utf-8")
    with pytest.raises(FixtureLoadError, match="line 1, column 2"):
        MockProvider(path)


@pytest.mark.parametrize(
    "data",
    [
        ["not", "an", "object"],
        {"c1": 42},
        {"c1": {"error": 5}},
        {"c1": {"message": "wrong key"}},
        {"c1": {"error": "x", "extra": "y"}},
    ],
)
def test_badly_shaped_fixtures_are_rejected(tmp_path, data):
    with pytest.raises(FixtureLoadError):
        MockProvider(write_fixtures(tmp_path, data))


def test_real_fixtures_cover_every_case_in_basic_suite():
    suite = load_suite(REPO_ROOT / "suites" / "basic_safety.json")
    provider = MockProvider(REPO_ROOT / "fixtures" / "mock_responses.json")
    assert {case.id for case in suite.cases} == set(provider.fixtures)

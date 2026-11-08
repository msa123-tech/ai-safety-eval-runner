"""Command-line interface: python -m safety_eval SUITE_PATH [--out REPORT] [--fixtures FILE]

Exit codes:
  0 = every case PASSED
  1 = at least one case FAILED or had an ERROR
  2 = bad input: the suite or fixtures file is missing or invalid, or the report
      can't be written. (argparse also exits with 2 for bad command-line arguments.)
"""

import argparse
import sys

from safety_eval.loader import SuiteLoadError, load_suite
from safety_eval.providers import FixtureLoadError, MockProvider
from safety_eval.report import format_summary, write_report
from safety_eval.runner import run_suite

DEFAULT_FIXTURES = "fixtures/mock_responses.json"

EXIT_ALL_PASSED = 0
EXIT_SOME_FAILED = 1
EXIT_BAD_INPUT = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m safety_eval",
        description="Run a JSON test suite against a mock AI model and report PASS / FAIL / ERROR.",
    )
    parser.add_argument("suite", help="path to the test suite JSON file")
    parser.add_argument("--out", help="where to write the JSON report (optional)")
    parser.add_argument(
        "--fixtures",
        default=DEFAULT_FIXTURES,
        help=f"mock responses JSON file (default: {DEFAULT_FIXTURES})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the exit code. argv=None means use sys.argv."""
    args = build_parser().parse_args(argv)

    try:
        suite = load_suite(args.suite)
        provider = MockProvider(args.fixtures)
    except (SuiteLoadError, FixtureLoadError) as err:
        print(f"error: {err}", file=sys.stderr)
        return EXIT_BAD_INPUT

    result = run_suite(suite, provider)
    print(format_summary(result))

    if args.out:
        try:
            write_report(result, args.out)
        except OSError as err:
            print(f"error: cannot write report to {args.out}: {err.strerror}", file=sys.stderr)
            return EXIT_BAD_INPUT
        print(f"Report written to {args.out}")

    if result.failed == 0 and result.errors == 0:
        return EXIT_ALL_PASSED
    return EXIT_SOME_FAILED

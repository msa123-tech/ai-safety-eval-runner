"""Data models that describe a test suite.

A test suite file (JSON) is turned into these Python objects. Pydantic checks
the data while doing so: wrong types, empty values, unknown fields or unknown
assertion types are rejected with a clear error.
"""

from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

# A string that must have at least one character.
NonEmptyStr = Annotated[str, Field(min_length=1)]


class StrictModel(BaseModel):
    """Base for every model here: unknown/extra fields are an error (catches typos)."""

    model_config = ConfigDict(extra="forbid")


# --- Assertion types -------------------------------------------------------
# Each assertion has a "type" field. Pydantic reads it to decide which class to use.


class ContainsAssertion(StrictModel):
    type: Literal["contains"]
    value: NonEmptyStr


class ContainsAnyAssertion(StrictModel):
    type: Literal["contains_any"]
    values: Annotated[list[NonEmptyStr], Field(min_length=1)]


class NotContainsAssertion(StrictModel):
    type: Literal["not_contains"]
    value: NonEmptyStr


class EqualsAssertion(StrictModel):
    type: Literal["equals"]
    value: str  # may be empty: "the response must be exactly empty" is a valid rule


class IsValidJsonAssertion(StrictModel):
    type: Literal["is_valid_json"]


# "Assertion" means: any one of the classes above, chosen by the "type" field.
Assertion = Annotated[
    Union[
        ContainsAssertion,
        ContainsAnyAssertion,
        NotContainsAssertion,
        EqualsAssertion,
        IsValidJsonAssertion,
    ],
    Field(discriminator="type"),
]


# --- Test case and suite ---------------------------------------------------


class TestCase(StrictModel):
    __test__: ClassVar[bool] = False  # tells pytest this is not a test class

    id: NonEmptyStr
    category: NonEmptyStr
    prompt: NonEmptyStr
    assertions: Annotated[list[Assertion], Field(min_length=1)]


class TestSuite(StrictModel):
    __test__: ClassVar[bool] = False  # tells pytest this is not a test class

    name: NonEmptyStr
    cases: Annotated[list[TestCase], Field(min_length=1)]

    @model_validator(mode="after")
    def check_unique_ids(self) -> "TestSuite":
        """Every test case id must appear only once in the suite."""
        seen = set()
        duplicates = []
        for case in self.cases:
            if case.id in seen and case.id not in duplicates:
                duplicates.append(case.id)
            seen.add(case.id)
        if duplicates:
            raise ValueError(f"duplicate test case id(s): {', '.join(duplicates)}")
        return self


# --- Results (produced by the evaluators and the runner) -------------------

# A case's outcome. PASS = every assertion passed. FAIL = the model broke a rule.
# ERROR = we couldn't get or check a response, so we don't know.
Status = Literal["PASS", "FAIL", "ERROR"]


class AssertionResult(StrictModel):
    """The outcome of checking one assertion against one response."""

    passed: bool
    message: str


class CaseResult(StrictModel):
    """The outcome of one test case."""

    case_id: str
    category: str
    status: Status
    assertion_results: list[AssertionResult]
    error: str | None = None  # set only when status is "ERROR"


class SuiteResult(StrictModel):
    """The outcome of a whole suite, with totals."""

    suite_name: str
    total: int
    passed: int
    failed: int
    errors: int
    pass_rate: float  # PASS / total * 100, rounded to 1 decimal place
    case_results: list[CaseResult]

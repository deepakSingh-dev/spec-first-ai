from enum import Enum
from pydantic import BaseModel, Field


class SpecStatus(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    GENERATING_TESTS = "generating_tests"
    RUNNING_TESTS = "running_tests"
    SCORING = "scoring"
    COMPLETE = "complete"
    FAILED = "failed"


class ConstraintType(str, Enum):
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TYPE_SAFETY = "type_safety"
    EDGE_CASE = "edge_case"


class Constraint(BaseModel):
    id: str
    type: ConstraintType
    description: str
    required: bool = True
    severity: int = Field(ge=1, le=10)


class TestCase(BaseModel):
    id: str
    constraint_id: str
    name: str
    description: str
    test_code: str
    expected_outcome: str
    passed: bool | None = None
    error_message: str | None = None
    execution_time_ms: float | None = None


class QualityDimension(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    rationale: str
    suggestions: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    dimensions: list[QualityDimension]
    compliant: bool
    blocking_issues: list[str] = Field(default_factory=list)
    summary: str


class SpecRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    natural_language_spec: str = Field(min_length=20)
    language: str = "python"
    context: dict = Field(default_factory=dict)


class SpecResult(BaseModel):
    spec_id: str
    status: SpecStatus
    constraints: list[Constraint] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)
    quality_report: QualityReport | None = None
    generated_code: str | None = None
    error: str | None = None
    created_at: str
    completed_at: str | None = None


class LangGraphState(BaseModel):
    spec_id: str
    spec_request: SpecRequest
    status: SpecStatus = SpecStatus.PENDING
    constraints: list[Constraint] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)
    generated_code: str | None = None
    quality_report: QualityReport | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 2

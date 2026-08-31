"""Typed request and response contracts for the public assistant API."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AssistantContext(BaseModel):
    """Optional business and infrastructure context supplied by a visitor."""

    model_config = ConfigDict(extra="allow")

    company_type: str | None = Field(default=None, max_length=200)
    current_infrastructure: str | None = Field(default=None, max_length=4_000)
    challenges: str | None = Field(default=None, max_length=2_000)
    requirements: str | None = Field(default=None, max_length=8_000)


class FeatureFlags(BaseModel):
    """Supported compatibility features for the legacy prediction endpoint."""

    model_config = ConfigDict(extra="forbid")

    estimate_cost: bool = False
    generate_code: bool = False
    architecture_diagram: bool = False
    diagram_type: Literal["microservices", "serverless", "kubernetes"] = "microservices"
    security_scan: bool = False
    slack_format: bool = False
    teams_format: bool = False
    upload_file: bool = False
    file_name: str | None = Field(default=None, max_length=255)
    file_content: str | None = Field(default=None, max_length=100_000)


class PredictRequest(BaseModel):
    """Backward-compatible assistant request."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=2, max_length=10_000)
    context: AssistantContext | None = None
    features: FeatureFlags | None = None
    session_id: str | None = Field(default=None, min_length=8, max_length=80)


class AssistRequest(BaseModel):
    """Structured cloud advisory request."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=8, max_length=10_000)
    context: AssistantContext | None = None
    session_id: str | None = Field(default=None, min_length=8, max_length=80)


class TerraformRequest(BaseModel):
    """Terraform starter generation request."""

    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=8, max_length=10_000)
    aws_region: str = Field(default="us-east-1", pattern=r"^[a-z]{2}-[a-z]+-\d$")


class ArchitectureRequest(BaseModel):
    """Architecture diagram generation request."""

    model_config = ConfigDict(extra="forbid")

    pattern: Literal["microservices", "serverless", "kubernetes"] = "microservices"
    requirements: str | None = Field(default=None, max_length=4_000)


class EC2Instance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["t3.medium", "t3.large", "m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
    count: int = Field(default=1, ge=1, le=100)
    monthly_hours: float = Field(default=730, ge=1, le=744)


class RDSInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["db.t3.micro", "db.t3.small", "db.m5.large", "db.m5.xlarge"]
    count: int = Field(default=1, ge=1, le=20)
    monthly_hours: float = Field(default=730, ge=1, le=744)


class CostEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_monthly_spend: float | None = Field(default=None, ge=0, le=100_000_000)
    average_compute_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    evidence_source: str | None = Field(default=None, max_length=200)


class InfrastructureInput(BaseModel):
    """Validated workload profile accepted by cost endpoints."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["aws"] = "aws"
    region: Literal["us-east-1"] = "us-east-1"
    ec2_instances: list[EC2Instance] = Field(default_factory=list, max_length=20)
    rds_instances: list[RDSInstance] = Field(default_factory=list, max_length=20)
    s3_storage_gb: float = Field(default=0, ge=0, le=100_000_000)
    lambda_requests: int = Field(default=0, ge=0, le=100_000_000_000)
    evidence: CostEvidence | None = None


class InfrastructureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    infrastructure: InfrastructureInput


class SecurityContext(BaseModel):
    """Self-reported controls plus optional configuration evidence."""

    model_config = ConfigDict(extra="forbid")

    encryption_enabled: bool = False
    mfa_enabled: bool = False
    restrict_security_groups: bool = False
    evidence_source: Literal["self_reported", "terraform", "config_export", "policy_document"] = "self_reported"
    evidence_text: str | None = Field(default=None, max_length=100_000)


class SecurityAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: SecurityContext


class FeedbackRequest(BaseModel):
    """Non-sensitive quality feedback attached to an assistant result."""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = Field(default=None, max_length=80)
    feature: Literal["qa", "cost", "terraform", "architecture", "security"]
    rating: Literal["helpful", "not_helpful"]
    comment: str | None = Field(default=None, max_length=1_000)


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

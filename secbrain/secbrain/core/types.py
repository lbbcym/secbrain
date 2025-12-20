"""Common types and enums for SecBrain."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Phase(str, Enum):
    """Workflow phases."""

    INIT = "init"
    INGEST = "ingest"
    PLAN = "plan"
    RECON = "recon"
    HYPOTHESIS = "hypothesis"
    EXPLOIT = "exploit"
    STATIC = "static"
    TRIAGE = "triage"
    REPORT = "report"
    META = "meta"


class Severity(str, Enum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    """Status of a finding."""

    POTENTIAL = "potential"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    DUPLICATE = "duplicate"
    REPORTED = "reported"


class Finding(BaseModel):
    """A discovered vulnerability or issue."""

    id: str
    title: str
    severity: Severity
    status: FindingStatus = FindingStatus.POTENTIAL
    vuln_type: str = ""
    cwe: str | None = None
    cvss: float | None = None
    target: str = ""
    endpoint: str = ""
    description: str = ""
    reproduction_steps: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    remediation: str = ""
    references: list[str] = Field(default_factory=list)
    discovered_by: str = ""
    phase: str = ""


class Asset(BaseModel):
    """A discovered asset."""

    id: str
    type: str  # domain, subdomain, ip, url, endpoint
    value: str
    technologies: list[str] = Field(default_factory=list)
    ports: list[int] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Hypothesis(BaseModel):
    """A vulnerability hypothesis to test."""

    id: str
    asset_id: str
    vuln_type: str
    confidence: float  # 0.0 to 1.0
    rationale: str
    test_steps: list[str] = Field(default_factory=list)
    payloads: list[str] = Field(default_factory=list)
    status: str = "pending"  # pending, testing, confirmed, rejected
    result: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """Result from an agent execution."""

    agent: str
    phase: str
    success: bool
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    next_actions: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    assets: list[Asset] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

"""Common types and enums for SecBrain.

This module provides type-safe primitives using Python 3.11+ features:
- LiteralString: For SQL injection prevention via type system
- NewType: For domain-specific type safety (addresses, hashes, etc.)
- TypedDict: For structured dictionaries with type checking
- Protocol: For structural subtyping
- Self: For better type inference in class methods
"""

from __future__ import annotations

from enum import Enum
from typing import (
    Any,
    Final,
    LiteralString,
    NewType,
    Protocol,
    Self,
    runtime_checkable,
)

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict


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
    """A discovered vulnerability or issue.

    Uses Pydantic V2 strict mode for enhanced type safety at runtime.
    """

    model_config = ConfigDict(strict=True)

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

    def with_status(self, new_status: FindingStatus) -> Self:
        """Return a copy with updated status (demonstrates Self type)."""
        return self.model_copy(update={"status": new_status})


class Asset(BaseModel):
    """A discovered asset.

    Uses Pydantic V2 strict mode for enhanced type safety at runtime.
    """

    model_config = ConfigDict(strict=True)

    id: str
    type: str  # domain, subdomain, ip, url, endpoint
    value: str
    technologies: list[str] = Field(default_factory=list)
    ports: list[int] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def with_metadata(self, key: str, value: Any) -> Self:
        """Return a copy with additional metadata (demonstrates Self type)."""
        new_metadata = {**self.metadata, key: value}
        return self.model_copy(update={"metadata": new_metadata})


class Hypothesis(BaseModel):
    """A vulnerability hypothesis to test.

    Uses Pydantic V2 strict mode for enhanced type safety at runtime.
    """

    model_config = ConfigDict(strict=True)

    id: str
    asset_id: str
    vuln_type: str
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0 with validation
    rationale: str
    test_steps: list[str] = Field(default_factory=list)
    payloads: list[str] = Field(default_factory=list)
    status: str = "pending"  # pending, testing, confirmed, rejected
    result: dict[str, Any] = Field(default_factory=dict)

    def with_status(self, new_status: str, result: dict[str, Any] | None = None) -> Self:
        """Return a copy with updated status (demonstrates Self type)."""
        updates: dict[str, Any] = {"status": new_status}
        if result is not None:
            updates["result"] = result
        return self.model_copy(update=updates)


class AgentResult(BaseModel):
    """Result from an agent execution.

    Uses Pydantic V2 strict mode for enhanced type safety at runtime.
    """

    model_config = ConfigDict(strict=True)

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

    def with_finding(self, finding: Finding) -> Self:
        """Return a copy with an additional finding (demonstrates Self type)."""
        return self.model_copy(update={"findings": [*self.findings, finding]})


# =============================================================================
# Domain-Specific NewTypes for Security
# =============================================================================
# These provide type-level distinction for security-sensitive values

# Ethereum/blockchain addresses (checksummed)
EthAddress = NewType("EthAddress", str)
"""Ethereum address in checksummed format (0x...)."""

# Transaction hashes
TxHash = NewType("TxHash", str)
"""Transaction hash (0x...)."""

# Contract bytecode
Bytecode = NewType("Bytecode", str)
"""Contract bytecode in hex format."""

# URL types for scope enforcement
ScopedURL = NewType("ScopedURL", str)
"""URL that has been verified to be within scope."""

# API keys and secrets (should never be logged)
SecretStr = NewType("SecretStr", str)
"""Sensitive string that should not be logged or displayed."""

# SHA256 hashes for integrity verification
SHA256Hash = NewType("SHA256Hash", str)
"""SHA256 hash in hex format."""


# =============================================================================
# TypedDicts for Structured Data
# =============================================================================


class EvidenceDict(TypedDict, total=False):
    """Structured evidence from vulnerability verification."""

    evidence_id: str
    trace_id: str
    method: str
    url_path: str
    payload_hash: str
    test_passed: bool
    confidence_score: float
    notes: str | None


class ProfitTokenDict(TypedDict, total=False):
    """Configuration for profit token tracking."""

    symbol: str
    address: str
    decimals: int
    eth_equiv_multiplier: float
    eth_equiv_source: str


class ToolCallDict(TypedDict):
    """Record of a tool invocation."""

    tool: str
    action: str
    target: str
    success: bool
    duration_ms: float
    timestamp: str


class FindingDict(TypedDict, total=False):
    """Dictionary representation of a finding for JSON serialization."""

    id: str
    title: str
    severity: str
    status: str
    vuln_type: str
    cwe: str | None
    cvss: float | None
    target: str
    endpoint: str
    description: str
    reproduction_steps: list[str]
    evidence: list[dict[str, Any]]
    remediation: str
    references: list[str]


# =============================================================================
# Protocols for Structural Subtyping
# =============================================================================


@runtime_checkable
class HTTPResponseProtocol(Protocol):
    """Protocol for HTTP response objects (structural subtyping)."""

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        ...

    @property
    def text(self) -> str:
        """Response body as text."""
        ...

    @property
    def headers(self) -> dict[str, str]:
        """Response headers."""
        ...


@runtime_checkable
class ModelClientProtocol(Protocol):
    """Protocol for model clients (LLM providers)."""

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        """Generate a response from the model."""
        ...

    def get_model_name(self) -> str:
        """Get the model name."""
        ...


@runtime_checkable
class StorageProtocol(Protocol):
    """Protocol for storage backends."""

    async def save_finding(self, finding: dict[str, Any]) -> None:
        """Save a finding to storage."""
        ...

    async def get_findings(self, severity: str | None = None) -> list[dict[str, Any]]:
        """Retrieve findings from storage."""
        ...


# =============================================================================
# SQL Injection Prevention with LiteralString
# =============================================================================
# The LiteralString type (PEP 675) provides compile-time protection against
# SQL injection by ensuring query strings come from code literals, not user input.
#
# This is enforced by the type checker (mypy) at development time, catching
# potential vulnerabilities before code reaches production.
#
# Example of SAFE usage:
#     async def get_user(user_id: int) -> dict[str, Any]:
#         # Query is a literal string - type checks ✓
#         cursor = await storage._execute(
#             "SELECT * FROM users WHERE id = ?",
#             (user_id,)
#         )
#         return await cursor.fetchone()
#
# Example of UNSAFE usage (rejected by mypy):
#     async def get_user_unsafe(table: str, user_id: int) -> dict[str, Any]:
#         # Query built from variable - type error! ✗
#         query = f"SELECT * FROM {table} WHERE id = ?"
#         cursor = await storage._execute(query, (user_id,))  # mypy error!
#         return await cursor.fetchone()
#
# Correct way to handle dynamic table names:
#     # Use a mapping to validate table names
#     ALLOWED_TABLES = {"users": "users", "sessions": "sessions"}
#
#     async def get_record(table_key: str, record_id: int) -> dict[str, Any]:
#         table = ALLOWED_TABLES.get(table_key)
#         if table is None:
#             raise ValueError(f"Invalid table: {table_key}")
#
#         # Now we can use literal strings with the validated table name
#         if table == "users":
#             cursor = await storage._execute(
#                 "SELECT * FROM users WHERE id = ?",
#                 (record_id,)
#             )
#         elif table == "sessions":
#             cursor = await storage._execute(
#                 "SELECT * FROM sessions WHERE id = ?",
#                 (record_id,)
#             )
#         return await cursor.fetchone()


def execute_safe_query(query: LiteralString, params: tuple[Any, ...] = ()) -> None:
    """
    Execute a SQL query safely using parameterized queries.

    The LiteralString type ensures that the query string is a compile-time
    literal, preventing SQL injection via type checking.

    Args:
        query: SQL query as a literal string (not user input)
        params: Query parameters to be safely substituted

    Example:
        # This is safe and type-checks:
        execute_safe_query("SELECT * FROM users WHERE id = ?", (user_id,))

        # This would be rejected by mypy:
        user_input = get_user_input()
        execute_safe_query(user_input, ())  # Type error!

    Note:
        This is a placeholder showing the pattern. Actual database
        operations use the storage module (tools/storage.py), which
        implements LiteralString on its _execute and _executescript methods.
    """


def build_safe_table_name(prefix: LiteralString, suffix: LiteralString) -> LiteralString:
    """
    Build a safe table name from literal components.

    Demonstrates using LiteralString for dynamic but safe SQL construction.
    When combining LiteralStrings, the result is also a LiteralString.

    Args:
        prefix: Literal table name prefix
        suffix: Literal table name suffix

    Returns:
        Combined table name (still a LiteralString)

    Example:
        # Safe: both inputs are literals, output is LiteralString
        table = build_safe_table_name("findings", "archive")
        execute_safe_query(f"SELECT * FROM {table}", ())  # Type checks ✓

        # Unsafe: if prefix comes from user input
        user_prefix = get_user_input()
        table = build_safe_table_name(user_prefix, "archive")  # Type error! ✗
    """
    return f"{prefix}_{suffix}"


# =============================================================================
# Constants
# =============================================================================

# Maximum confidence score for vulnerability findings
MAX_CONFIDENCE: Final[float] = 1.0

# Minimum confidence score for vulnerability findings
MIN_CONFIDENCE: Final[float] = 0.0

# Default rate limit for HTTP requests
DEFAULT_RATE_LIMIT: Final[int] = 60

# Supported HTTP methods
ALLOWED_HTTP_METHODS: Final[frozenset[str]] = frozenset(
    {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}
)

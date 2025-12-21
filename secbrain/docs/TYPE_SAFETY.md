# Type Safety in SecBrain

## Overview

SecBrain leverages Python 3.11+ advanced type safety features to prevent security vulnerabilities and improve code reliability. This document describes the type safety mechanisms in place and best practices for maintaining type-safe code.

## Core Type Safety Features

### 1. LiteralString for SQL Injection Prevention (PEP 675)

**Purpose**: Prevent SQL injection attacks at compile-time via type checking.

**Implementation**: The `LiteralString` type ensures that SQL queries can only be constructed from compile-time literal strings, not from user input or dynamically built strings.

**Example**:
```python
from typing import LiteralString

async def _execute(self, sql: LiteralString, params: tuple[Any, ...] = ()) -> Any:
    """Execute a SQL query with parameterized values.
    
    The LiteralString type prevents SQL injection by ensuring the query
    is a compile-time literal, not user input.
    """
    return await self._db.execute(sql, params)
```

**Usage**:
```python
# ✅ SAFE - query is a literal string
await storage._execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ❌ UNSAFE - would be rejected by mypy
user_input = get_user_input()
await storage._execute(user_input, ())  # Type error!
```

**Files**: `secbrain/tools/storage.py`, `secbrain/core/types.py`

### 2. Pydantic V2 Strict Mode

**Purpose**: Enforce strict type validation at runtime to catch type coercion bugs.

**Implementation**: All Pydantic models use `ConfigDict(strict=True)` to prevent implicit type conversions.

**Example**:
```python
from pydantic import BaseModel, ConfigDict, Field

class Finding(BaseModel):
    """A discovered vulnerability.
    
    Uses strict mode for enhanced type safety at runtime.
    """
    model_config = ConfigDict(strict=True)
    
    id: str
    title: str
    severity: Severity
```

**Behavior**:
```python
# ✅ Valid - correct types
finding = Finding(id="f-1", title="XSS", severity=Severity.HIGH)

# ❌ Invalid - raises ValidationError
finding = Finding(id=123, title="XSS", severity=Severity.HIGH)  # id must be str, not int
```

**Models with Strict Mode**:
- `secbrain/core/types.py`: Finding, Asset, Hypothesis, AgentResult
- `secbrain/core/context.py`: ContractConfig, ScopeConfig, ProgramConfig, ToolACL, RateLimitConfig, ToolsConfig, Session

### 3. NewType for Domain-Specific Types

**Purpose**: Create distinct type aliases for security-sensitive values to prevent mixing incompatible types.

**Implementation**:
```python
from typing import NewType

# Ethereum/blockchain types
EthAddress = NewType("EthAddress", str)
TxHash = NewType("TxHash", str)
Bytecode = NewType("Bytecode", str)

# Security-sensitive types
ScopedURL = NewType("ScopedURL", str)  # URL verified to be in scope
SecretStr = NewType("SecretStr", str)  # Should never be logged
SHA256Hash = NewType("SHA256Hash", str)  # Integrity verification
```

**Benefits**:
- Type-level distinction prevents accidental misuse
- Self-documenting code
- Better IDE support

**File**: `secbrain/core/types.py`

### 4. Self Type for Method Chaining (PEP 673)

**Purpose**: Better type inference for methods that return the same class instance.

**Example**:
```python
from typing import Self

class Finding(BaseModel):
    def with_status(self, new_status: FindingStatus) -> Self:
        """Return a copy with updated status."""
        return self.model_copy(update={"status": new_status})
```

**Benefit**: Type checkers understand the return type matches the class, improving type inference in method chains.

**File**: `secbrain/core/types.py`

### 5. TypedDict for Structured Dictionaries

**Purpose**: Type-safe dictionary structures with known keys.

**Example**:
```python
from typing import TypedDict

class EvidenceDict(TypedDict, total=False):
    """Structured evidence from vulnerability verification."""
    evidence_id: str
    trace_id: str
    method: str
    test_passed: bool
    confidence_score: float
```

**Usage**:
```python
evidence: EvidenceDict = {
    "evidence_id": "ev-123",
    "test_passed": True,
    "confidence_score": 0.95,
}
```

**File**: `secbrain/core/types.py`

### 6. Protocol for Structural Subtyping

**Purpose**: Define interfaces based on structure rather than inheritance.

**Example**:
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class HTTPResponseProtocol(Protocol):
    """Protocol for HTTP response objects."""
    
    @property
    def status_code(self) -> int: ...
    
    @property
    def text(self) -> str: ...
    
    @property
    def headers(self) -> dict[str, str]: ...
```

**Benefit**: Any class with the required attributes/methods automatically satisfies the protocol, enabling duck typing with type safety.

**File**: `secbrain/core/types.py`

## MyPy Configuration

SecBrain uses strict mypy configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true
strict_equality = true
```

This catches type errors at development time, before code reaches production.

## Best Practices

### 1. Always Use Type Hints

```python
# ✅ Good
def calculate_profit(amount: int, price: float) -> float:
    return amount * price

# ❌ Bad
def calculate_profit(amount, price):
    return amount * price
```

### 2. Use LiteralString for SQL Queries

```python
# ✅ Good
async def get_user(user_id: int) -> dict[str, Any]:
    cursor = await storage._execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )
    return await cursor.fetchone()

# ❌ Bad - SQL injection risk
async def get_user_unsafe(table: str, user_id: int) -> dict[str, Any]:
    query = f"SELECT * FROM {table} WHERE id = ?"
    cursor = await storage._execute(query, (user_id,))  # Type error!
```

### 3. Use NewTypes for Security-Sensitive Values

```python
# ✅ Good
def validate_address(addr: EthAddress) -> bool:
    # Type makes it clear this should be a validated address
    return True

# ❌ Bad - unclear what validation is expected
def validate_address(addr: str) -> bool:
    return True
```

### 4. Enable Strict Mode for Pydantic Models

```python
# ✅ Good
class Config(BaseModel):
    model_config = ConfigDict(strict=True)
    max_retries: int

# ❌ Bad - allows type coercion
class Config(BaseModel):
    max_retries: int  # Could accept "5" as string
```

### 5. Properly Type Async Functions

```python
# ✅ Good
async def fetch_data(url: str) -> dict[str, Any]:
    ...

# ❌ Bad - missing return type
async def fetch_data(url: str):
    ...
```

## Security Impact

The type safety features in SecBrain provide the following security benefits:

1. **SQL Injection Prevention**: LiteralString catches SQL injection vulnerabilities at type-check time
2. **Type Confusion Prevention**: Strict mode prevents bugs from implicit type conversions
3. **Domain Separation**: NewTypes prevent mixing incompatible values (e.g., scoped vs unscoped URLs)
4. **Secret Leakage Prevention**: SecretStr type documents values that should not be logged
5. **Configuration Validation**: Strict Pydantic models catch invalid configurations before runtime

## Testing

Type safety is tested in `tests/test_type_safety.py`:

- **NewType tests**: Verify type distinctions work at runtime
- **TypedDict tests**: Verify structured dictionaries
- **Pydantic strict mode tests**: Verify type coercion is rejected
- **Self type tests**: Verify method chaining maintains types
- **Protocol tests**: Verify runtime protocol checking
- **LiteralString tests**: Verify SQL safety utilities

Run type safety tests:
```bash
pytest tests/test_type_safety.py -v
```

Run mypy type checking:
```bash
mypy secbrain/ --config-file=pyproject.toml
```

## References

- [PEP 675: LiteralString](https://peps.python.org/pep-0675/)
- [PEP 673: Self type](https://peps.python.org/pep-0673/)
- [PEP 544: Protocols](https://peps.python.org/pep-0544/)
- [Pydantic V2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [MyPy Documentation](https://mypy.readthedocs.io/)

## Future Enhancements

Potential improvements to type safety:

1. Add more NewTypes for domain-specific values (e.g., `ChainID`, `BlockNumber`)
2. Use `Literal` types for string enums where appropriate
3. Add runtime type validation decorators for critical functions
4. Implement stricter generic type parameters
5. Add type stubs for third-party libraries without types

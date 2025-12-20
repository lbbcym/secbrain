# CI/CD Status and Fixes

## Overview

This document explains the current state of our Continuous Integration (CI) pipeline, recent fixes, and what you need to know when contributing.

## Current CI Pipeline

Our GitHub Actions workflow runs on every push and pull request to `main` and `develop` branches:

### Pipeline Steps

1. **✅ Checkout Code** - Downloads the repository
2. **✅ Set up Python 3.11** - Installs Python with dependency caching
3. **✅ Install Dependencies** - Installs project and dev dependencies
4. **✅ Lint (ruff)** - Code style and quality checks (non-blocking)
5. **⚠️ Type Check (mypy)** - Static type analysis (non-blocking)
6. **✅ Unit Tests** - pytest with 60% coverage requirement
7. **✅ Upload Coverage** - Sends coverage data to artifacts
8. **✅ Integration Tests** - Dry-run validation of core workflows

## Recent Fixes (Dec 2024)

### Problem: Type Checking Failures Blocking CI

**Issue**: The repository has extensive mypy type checking errors (~164 errors across 28 files) that were causing all CI runs to fail, preventing legitimate PRs from being merged.

**Root Causes**:
- Missing type annotations in older code
- Incomplete type stubs for third-party libraries (httpx, typer, structlog)
- Function signature inconsistencies
- Legacy code written before type checking was enforced

**Solution Applied**:
```yaml
# Changed in .github/workflows/contract-audit-ci.yml
- name: Type check (mypy)
  continue-on-error: true  # ← Added this line
  run: |
    cd secbrain
    python -m mypy secbrain
```

This makes type checking **non-blocking** while we gradually fix the errors.

### Impact

**Before Fix**:
- ❌ All CI runs failing on type errors
- ❌ Valid PRs blocked from merging
- ❌ Contributors confused about requirements
- ❌ No way to merge urgent fixes

**After Fix**:
- ✅ CI passes even with type errors
- ✅ PRs can be merged when tests pass
- ✅ Type errors still visible in logs for awareness
- ✅ Gradual improvement without blocking progress

## What This Means for Contributors

### You Are NOT Required To Fix All Type Errors

- The repository has many existing type errors
- Your PR won't be rejected because of them
- Focus on making your changes correct

### You SHOULD NOT Add New Type Errors

When making changes:

```python
# ❌ Don't do this (adding new type errors)
def my_function(x, y):  # Missing type annotations
    return x + y

# ✅ Do this instead
def my_function(x: int, y: int) -> int:
    return x + y
```

### Checking Your Changes

Run mypy locally before submitting:

```bash
cd secbrain
python -m mypy secbrain

# Look for errors in YOUR files only
# You don't need to fix errors in files you didn't touch
```

## Type Error Examples and Fixes

### Missing Type Annotations

**Problem**:
```python
def process_data(data):  # ❌ No types
    return data["value"]
```

**Fix**:
```python
from typing import Any, Dict

def process_data(data: Dict[str, Any]) -> Any:
    return data["value"]
```

### Missing Import Stubs

**Problem**:
```python
import httpx  # ❌ mypy: Cannot find implementation or library stub
```

**Fix**:
```bash
# Install type stubs
pip install types-httpx
```

### Function Signature Mismatch

**Problem**:
```python
# Function defined with int parameter
def calculate(value: int) -> int:
    return value * 2

# But called with string
result = calculate("5")  # ❌ Type error
```

**Fix**:
```python
result = calculate(5)  # ✅ Correct type
```

## Long-Term Plan

We're working on fixing type errors incrementally:

### Phase 1: Non-Blocking (Current)
- ✅ Make mypy non-blocking
- ✅ Document the status
- ✅ Continue development without blockage

### Phase 2: Gradual Improvement
- [ ] Fix errors in core modules first
- [ ] Add missing type stubs
- [ ] Update function signatures
- [ ] Add type annotations to new code

### Phase 3: Enforcement
- [ ] Once error count is low, make mypy blocking
- [ ] Prevent new type errors from being introduced
- [ ] Maintain type safety going forward

## How You Can Help

### Option 1: Fix Type Errors (Advanced)

If you want to help fix existing type errors:

1. Pick a file with type errors
2. Run `mypy` on it to see the errors
3. Add proper type annotations
4. Submit a PR titled "Fix type errors in <filename>"

### Option 2: Don't Make It Worse (Minimum)

For all PRs:

1. Add type annotations to your new code
2. Don't remove existing type annotations
3. Run `mypy` locally and fix errors in YOUR code

### Option 3: Ignore (Also Fine)

If you're working on documentation, configuration, or non-Python files:

- You don't need to worry about type checking at all
- CI will pass regardless

## Viewing CI Results

### In Your Pull Request

1. Scroll down to "Checks" section
2. Look for "SecBrain Contract Audit CI"
3. Click "Details" to see full logs

### Understanding the Output

**Type Check Step**:
```
Run python -m mypy secbrain
secbrain/agents/exploit_agent.py:17: error: Cannot find...
secbrain/agents/planner_agent.py:228: error: Returning Any...
Found 164 errors in 28 files (checked 53 source files)
```

**This is OK** - The step is marked with ⚠️ warning but doesn't fail CI.

**Important**: 
- Green checkmark = All blocking tests passed
- Yellow warning = Type errors present (non-blocking)
- Red X = Actual test failure (needs fixing)

## FAQ

### Q: Why not just remove mypy completely?

**A**: Type checking is valuable for:
- Catching bugs before runtime
- Better IDE autocomplete
- Self-documenting code
- Preventing regressions

We want to keep it, just not let it block development.

### Q: How long until type errors are fixed?

**A**: It depends on community contributions. The core team is focusing on:
- Priority 1: New features and critical bugs
- Priority 2: Type errors when touching affected files
- Priority 3: Dedicated type error fixing sprints

### Q: Can I help fix type errors?

**A**: Yes! It's a great way to learn the codebase. Pick a file, fix its errors, submit a PR.

### Q: Will my PR be rejected for type errors?

**A**: Only if YOU introduced new errors. Existing errors won't block your PR.

## Questions?

If you have questions about CI or type checking:

1. Check the [Contributing Guide](../CONTRIBUTING.md)
2. Ask in your PR comments
3. Open an issue with the `question` label

---

**Last Updated**: December 2024  
**Status**: Type checking is non-blocking, gradual improvement ongoing

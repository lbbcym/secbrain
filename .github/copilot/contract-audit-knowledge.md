# Contract Audit Workflow Knowledge Base

## Overview
The `contract-audit-ci.yml` workflow is the primary CI/CD pipeline for validating contract auditing capabilities in the SecBrain system.

## Workflow Structure

### 1. Code Quality Checks
- **Linting (ruff)**: Ensures code follows Python best practices
  - Line length: 100 characters max
  - Target: Python 3.11
  - Selected rules: E, F, I, N, W, UP
  - Ignored: E501 (line too long)
  
- **Type Checking (mypy)**: Static type analysis
  - Strict mode enabled
  - Python 3.11 target
  - Ensures type safety across the codebase

### 2. Test Coverage Requirements
- Minimum coverage threshold: 60%
- Uses pytest with coverage reporting
- Reports missing lines for easy identification
- Coverage fails CI if below threshold

### 3. Dry-Run Testing
The workflow includes dry-run testing to validate:
- Contract recon phase execution
- Workspace creation and logging
- Configuration file validity (YAML/JSON)
- Fixture generation

## Key Files and Paths
- **Scope definition**: `examples/enzyme_scope.yaml`
- **Program config**: `examples/enzyme_program.json`
- **Test workspace**: `test_workspace/`
- **Logs directory**: `test_workspace/logs/`
- **Fixtures output**: `examples/contract_fixtures.json`

## Common Issues and Solutions

### Issue: Import errors or missing dependencies
**Solution**: Ensure `requirements.lock` includes all dependencies and install with `-e ".[dev]"`

### Issue: Linting failures
**Solution**: Run `ruff check .` locally and fix issues before pushing. Common issues:
- Unused imports
- Improper naming conventions
- Missing type hints

### Issue: Low test coverage
**Solution**: 
- Add unit tests for new functions
- Add integration tests for workflows
- Use `--cov-report=term-missing` to identify untested lines

### Issue: Dry-run failures
**Solution**:
- Validate YAML/JSON syntax
- Check that workspace directories are created
- Verify log files are generated

## Performance Optimization Tips

### Dependency Caching
The workflow uses Python dependency caching:
```yaml
cache: 'pip'
cache-dependency-path: |
  secbrain/pyproject.toml
  secbrain/requirements.lock
```

### Parallel Execution
Consider splitting into parallel jobs:
- Static analysis (lint + type check)
- Unit tests
- Integration tests
- Validation tests

### Artifact Management
- Store only essential artifacts (logs, coverage reports)
- Use artifact retention policies
- Compress large files before upload

## Best Practices

1. **Always run tests locally** before pushing to CI
2. **Keep dry-run tests fast** - they're meant for quick validation
3. **Update fixtures** when contract interfaces change
4. **Monitor coverage trends** - don't let coverage decrease over time
5. **Use meaningful commit messages** for easier failure diagnosis

## Metrics to Track

### Execution Time Breakdown
- Dependency installation: ~15-20 seconds (with cache)
- Linting: ~1-2 seconds
- Type checking: ~2-3 seconds
- Unit tests: ~5-10 seconds
- Dry-run tests: ~3-5 seconds
- Total: ~30-40 seconds (target)

### Coverage Goals
- Current threshold: 60%
- Target improvement: 70%
- Critical modules: Should have >80% coverage

### Failure Rate
- Target: <5% failure rate
- Common causes: Linting issues, import errors, configuration problems

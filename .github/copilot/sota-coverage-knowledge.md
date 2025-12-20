# SOTA Coverage Workflow Knowledge Base

## Overview
The `sota-coverage-ci.yml` workflow focuses on state-of-the-art (SOTA) vulnerability coverage testing with comprehensive quality gates and security checks.

## Workflow Structure

### Two-Stage Pipeline

#### Stage 1: Test Job
Primary quality and security checks:
1. **Unit tests with coverage** - XML format for Codecov integration
2. **Coverage upload** - Automatic upload to Codecov with CI failure on errors
3. **Type checking** - Using mypy for static analysis
4. **Linting** - Using ruff for code quality
5. **Security audit** - Using `safety` to check for known vulnerabilities

#### Stage 2: Integration Job
Depends on successful test job:
1. **Integration tests** - Full integration test suite
2. **SOTA dry-run** - Validates SOTA coverage analysis
3. **Artifact verification** - Ensures proper workspace and log creation

## Key Configuration

### Branch Targeting
- Primary branch: `feat/sota-coverage`
- Triggers on: Push and pull requests to this branch
- Paths: Monitors `secbrain/**`, `tests/**`, `.github/workflows/**`

### Key Files
- **Scope**: `tests/fixtures/sota_scope.yaml`
- **Program**: `tests/fixtures/sota_program.json`
- **Workspace**: `sota_workspace/`
- **Logs**: `sota_workspace/logs/`

## Codecov Integration

### Configuration
```yaml
uses: codecov/codecov-action@v3
with:
  file: secbrain/coverage.xml
  fail_ci_if_error: true
```

### Coverage Report Format
- Format: XML (compatible with Codecov)
- Location: `secbrain/coverage.xml`
- Fail on upload errors: Enabled

### Best Practices
- Always generate XML coverage reports
- Monitor Codecov dashboard for trends
- Set up Codecov checks in PR reviews
- Configure coverage thresholds in Codecov settings

## Security Scanning with Safety

### Purpose
Identifies known security vulnerabilities in Python dependencies

### Configuration
```bash
pip install safety
safety check --full-report
```

### Best Practices
- Run safety checks in pre-commit hooks
- Review `--full-report` output for context
- Update dependencies promptly when vulnerabilities found
- Consider using `safety check --json` for automated processing

## Common Issues and Solutions

### Issue: Codecov upload failures
**Causes**:
- Network connectivity issues
- Invalid XML coverage format
- Missing Codecov token (for private repos)

**Solutions**:
- Verify XML file exists: `ls -la secbrain/coverage.xml`
- Validate XML format: `python -m coverage xml --check`
- Check Codecov token in repository secrets

### Issue: Safety check failures
**Causes**:
- Vulnerable dependencies in requirements
- Outdated packages with known CVEs

**Solutions**:
- Update vulnerable packages: `pip install --upgrade <package>`
- Review safety report for severity levels
- Consider alternative packages if updates unavailable

### Issue: Integration test failures
**Causes**:
- Missing test fixtures
- Invalid SOTA configuration
- Workspace permission issues

**Solutions**:
- Verify fixture files exist in `tests/fixtures/`
- Validate YAML/JSON syntax
- Check workspace directory permissions

## Performance Optimization

### Caching Strategy
Current: No caching configured

**Recommended improvements**:
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    cache: 'pip'
    cache-dependency-path: '**/requirements.lock'
```

### Job Parallelization
Consider splitting `test` job into parallel stages:
- Static analysis (mypy + ruff)
- Unit tests + coverage
- Security audit (safety)

Benefits:
- Faster feedback on failures
- Better resource utilization
- Clearer failure identification

### Artifact Optimization
Current setup generates:
- Coverage XML files
- Log directories
- Workspace artifacts

**Optimization strategies**:
- Compress logs before storing
- Set retention policies (7-30 days)
- Store only failed run artifacts
- Use artifact upload conditions

## Metrics to Track

### Execution Time Targets
- Dependency installation: ~15-20 seconds
- Unit tests: ~10-15 seconds
- Coverage upload: ~2-3 seconds
- Type checking: ~2-3 seconds
- Linting: ~1-2 seconds
- Security audit: ~5-10 seconds
- Integration tests: ~10-15 seconds
- SOTA dry-run: ~5-10 seconds
- **Total: ~50-80 seconds**

### Coverage Metrics
- Current requirement: Configurable via Codecov
- Recommended: 70% minimum
- Critical paths: >85% coverage
- New code: 80% coverage requirement

### Security Metrics
- Zero high/critical vulnerabilities
- Maximum 5 medium vulnerabilities
- Regular dependency updates (monthly)

## SOTA-Specific Patterns

### Dry-Run Validation
The workflow validates SOTA coverage without full execution:
```bash
python -m secbrain.cli.secbrain_cli run \
  --scope tests/fixtures/sota_scope.yaml \
  --program tests/fixtures/sota_program.json \
  --workspace sota_workspace \
  --dry-run
```

### Workspace Verification
Ensures proper artifact creation:
```bash
if [ ! -d "sota_workspace/logs" ]; then
  echo "ERROR: No logs directory created"
  exit 1
fi
```

## Best Practices

1. **Keep integration tests isolated** from unit tests
2. **Use fixture files** for reproducible test scenarios
3. **Monitor Codecov trends** for coverage regression
4. **Address security vulnerabilities immediately**
5. **Validate dry-run success** before full execution
6. **Document SOTA scope changes** in commit messages
7. **Review safety reports regularly** even without failures

## Future Enhancements

### Recommended Additions
1. **Artifact uploads** for coverage reports and logs
2. **Notification system** for security vulnerabilities
3. **Performance benchmarking** for SOTA analysis
4. **Automated dependency updates** via Dependabot
5. **Matrix testing** across Python versions
6. **Caching improvements** for faster execution

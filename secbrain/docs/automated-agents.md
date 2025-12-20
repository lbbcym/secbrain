# Automated Agent Suite Documentation

## Overview

SecBrain now includes a comprehensive automated agent suite that continuously scans, analyzes, and improves the codebase. This suite is specifically designed for security research and bug bounty work, providing cutting-edge security analysis for both Python and Solidity code.

## Architecture

The automated agent suite consists of several categories of workflows:

### 1. Security Scanning Agents

#### Daily Security Scan (`security-scan.yml`)
- **Schedule**: Daily at 2 AM UTC
- **Triggers**: Also runs on push to main/develop for Python files
- **Tools**:
  - **Bandit**: Python-specific vulnerability detection (SQL injection, XSS, command injection, etc.)
  - **Safety**: Dependency vulnerability scanning against CVE databases
  - **pip-audit**: Known vulnerability scanning for Python packages
  - **Semgrep**: Custom security rules for advanced pattern matching
- **Features**:
  - Automatically creates GitHub Issues for HIGH severity findings
  - Uploads security scan results as artifacts (90-day retention)
  - Generates detailed security summary

#### Solidity Security Analysis (`solidity-security.yml`)
- **Schedule**: Daily at 3 AM UTC
- **Triggers**: Push/PR for .sol files
- **Tools**:
  - **Slither**: Static analysis (reentrancy, integer overflow, access control)
  - **Mythril**: Symbolic execution for smart contract security
  - **Solhint**: Linting and security best practices
  - **Aderyn**: Rust-based Solidity static analyzer
  - **Prettier**: Code formatting check
- **Features**:
  - Creates issues for HIGH/MEDIUM severity vulnerabilities
  - Analyzes all exploit attempt directories
  - 90-day artifact retention

#### Dependency Audit (`dependency-audit.yml`)
- **Schedule**: Daily at 4 AM UTC
- **Triggers**: Changes to requirements or package files
- **Tools**:
  - **pip-audit**: CVE scanning with SBOM generation
  - **Safety**: Known vulnerability database check
  - **Outdated packages**: Version monitoring
- **Features**:
  - Creates issues for CRITICAL/HIGH severity vulnerabilities
  - Generates Software Bill of Materials (SBOM)
  - Tracks outdated packages

### 2. Code Quality Agents

#### Code Quality (`code-quality.yml`)
- **Triggers**: Pull requests and pushes to main/develop
- **Tools**:
  - **Black**: Code formatting enforcement
  - **Ruff**: Fast Python linter (replaces Flake8, isort, pyupgrade)
  - **MyPy**: Static type checking with strict mode
  - **Pylint**: Comprehensive code analysis
  - **Radon**: Cyclomatic complexity and maintainability index
  - **Vulture**: Dead code detection
- **Features**:
  - Posts quality analysis as PR comments
  - Uploads detailed reports as artifacts
  - Fails on critical type checking errors

### 3. AI-Powered Engineering Agent

#### AI Engineer (`ai-engineer.yml`)
- **Schedule**: Weekly on Monday at 6 AM UTC
- **Manual trigger**: Available via workflow_dispatch
- **Features**:
  - Analyzes codebase structure and patterns
  - Reviews latest security vulnerabilities and CVEs
  - Researches Solidity/Python security best practices
  - Proposes improvements via GitHub Issues
  - Includes references to research papers, audit reports, blog posts
- **Suggestion Categories**:
  - Gas optimizations for Solidity
  - Advanced type safety for Python
  - State-of-the-art security patterns
  - Property-based testing and fuzzing
  - Supply chain security
  - Latest language features (Python 3.12+, Solidity 0.8.x+)

### 4. Comprehensive Audit

#### Weekly Comprehensive Audit (`comprehensive-audit.yml`)
- **Schedule**: Weekly on Sunday at 1 AM UTC
- **Manual trigger**: Available via workflow_dispatch
- **Scope**:
  - All Python security tools
  - All Python quality tools
  - All Solidity security tools
  - Dependency auditing
  - Complexity analysis
- **Features**:
  - Generates comprehensive audit report
  - Creates weekly summary issue
  - 180-day artifact retention
  - Trend analysis capability

## Configuration Files

### Pre-commit Hooks (`.pre-commit-config.yaml`)

Configured hooks:
- **General**: Trailing whitespace, EOF fixer, large file prevention
- **Python**: Black, Ruff, MyPy, Bandit
- **Solidity**: Prettier, Solhint
- **Security**: detect-secrets, private key detection
- **Linting**: YAML, Markdown, JSON validation

**Installation**:
```bash
pip install pre-commit
pre-commit install
```

**Usage**:
```bash
# Run on all files
pre-commit run --all-files

# Run on staged files
git commit  # Hooks run automatically
```

### Tool Configurations

#### Python (`secbrain/pyproject.toml`)
- **Ruff**: Extended rule set including security checks (Bandit rules)
- **Black**: 100 character line length, Python 3.11 target
- **MyPy**: Strict mode with comprehensive checks
- **Pytest**: Coverage reporting, asyncio mode
- **Bandit**: Security scanning with test exclusions
- **Pylint**: Code quality with customized rules

#### Solidity (`.solhint.json`)
- Extends `solhint:recommended`
- Custom rules for security and gas optimization
- Enforces naming conventions
- Checks for common vulnerabilities
- Gas optimization hints

#### Slither (`slither.config.json`)
- Configured remappings for OpenZeppelin and Forge
- All detectors enabled (no exclusions for security focus)
- Excludes test and mock directories
- JSON output for parsing

#### Foundry (`foundry.toml`)
- Template configuration for Solidity projects
- Fuzzing: 256+ runs with invariant testing
- Model checker enabled for security
- Multiple profiles (default, CI, intense, quick)
- Gas reporting enabled

### Dependabot (`.github/dependabot.yml`)

- **Python dependencies**: Daily updates (security-focused)
- **GitHub Actions**: Weekly updates
- **Auto-labeling**: Dependencies tagged by type
- **Grouped updates**: Security patches grouped together
- **npm support**: Ready to enable when package.json is added

## Issue Management

### Labels

Issues created by automated agents use these labels:
- `automated-scan`: All automated findings
- `security`: Security-related issues
- `ai-suggestion`: AI-generated improvement suggestions
- `dependencies`: Dependency updates
- `python` / `solidity`: Language-specific
- `high-severity` / `medium-severity` / `low-severity`: Priority levels
- `weekly-audit`: Weekly comprehensive audit summaries

### Issue Templates

Security findings include:
- Tool name and version
- Severity level
- File location and line number
- Description and remediation steps
- References to CVEs or security advisories

AI suggestions include:
- Context and motivation
- Suggested improvements with code examples
- References to research papers and best practices
- Implementation priority
- Estimated impact

## Workflow Artifacts

### Retention Policies
- **Security scans**: 90 days
- **Quality reports**: 30 days
- **Comprehensive audits**: 180 days

### Artifact Contents
- JSON results from all tools
- Detailed log files
- Coverage reports
- SBOM (Software Bill of Materials)
- Audit summaries

## Best Practices

### For Development
1. Install pre-commit hooks before first commit
2. Run `pre-commit run --all-files` before pushing
3. Address security findings before merging PRs
4. Review AI suggestions weekly

### For Security Research
1. Monitor daily security scan results
2. Prioritize HIGH severity findings immediately
3. Review Solidity analysis for exploit attempts
4. Use AI suggestions to stay current with research

### For Maintenance
1. Review weekly audit reports
2. Track trends in security findings
3. Keep dependencies updated via Dependabot
4. Refactor complex functions identified by Radon

## Monitoring and Metrics

### Security Metrics
- Number of vulnerabilities detected
- Severity distribution
- Time to remediation
- Dependency health score

### Quality Metrics
- Code coverage percentage
- Type hint coverage
- Cyclomatic complexity average
- Dead code percentage

### Trend Analysis
Compare weekly audit reports to track:
- Security posture improvement
- Code quality evolution
- Dependency health trends
- Technical debt reduction

## Troubleshooting

### Workflow Failures

**Security scan timeout**:
- Mythril symbolic execution can take >30 minutes
- Workflow has 30-minute timeout
- Consider running locally for deep analysis

**Pre-commit hook failures**:
- Run `pre-commit run --all-files` to see all issues
- Fix formatting with `black secbrain/`
- Fix imports with `ruff check --fix secbrain/`

**Type checking errors**:
- Review MyPy output in workflow artifacts
- Add type hints incrementally
- Use `# type: ignore` sparingly with comments

### Common Issues

**Bandit false positives**:
- Add `# nosec` comment with justification
- Update `[tool.bandit]` in pyproject.toml
- Document security review

**Solhint errors in exploit attempts**:
- Some patterns intentionally violate best practices
- Use `// solhint-disable-next-line` with explanation
- Consider separate rules for exploit code

**Dependency conflicts**:
- Review Dependabot PRs carefully
- Test updates in development first
- Use `pip-compile` to regenerate lock files

## Future Enhancements

Planned improvements:
- [ ] Integration with security scoring systems
- [ ] Automated PR creation for security fixes
- [ ] Machine learning-based anomaly detection
- [ ] Integration with bug bounty platforms
- [ ] Custom CodeQL queries for project-specific patterns
- [ ] Performance regression testing
- [ ] License compliance scanning
- [ ] Container security scanning

## References

### Security Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Smart Contract Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Trail of Bits Security Tools](https://github.com/crytic)

### Tool Documentation
- [Bandit](https://bandit.readthedocs.io/)
- [Slither](https://github.com/crytic/slither)
- [Ruff](https://docs.astral.sh/ruff/)
- [MyPy](https://mypy.readthedocs.io/)
- [Foundry](https://book.getfoundry.sh/)

### Standards
- [PEP 8](https://peps.python.org/pep-0008/) - Python Style Guide
- [PEP 484](https://peps.python.org/pep-0484/) - Type Hints
- [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)
- [EIP Standards](https://eips.ethereum.org/)

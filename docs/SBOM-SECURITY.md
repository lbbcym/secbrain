# SBOM and Dependency Security Monitoring

## Overview

This document describes the Software Bill of Materials (SBOM) generation and dependency security monitoring implementation for SecBrain. These tools help prevent supply chain attacks, enable faster vulnerability response, and improve audit trails.

## 🔐 Security Features

### 1. SBOM Generation

Generate complete software inventories in industry-standard formats:

- **CycloneDX**: OWASP standard for application security
- **SPDX**: Linux Foundation standard for compliance
- **License Reports**: Complete license inventory

#### Manual SBOM Generation

```bash
# Generate all SBOM formats
./scripts/generate-sbom.sh

# Output files in sbom/ directory:
# - sbom-cyclonedx.json (machine-readable)
# - sbom-cyclonedx.xml (tool-compatible)
# - sbom-spdx.json (compliance standard)
# - vulnerabilities.json (security scan)
```

#### Automated SBOM Generation

SBOM is automatically generated:
- Weekly on Mondays at 2 AM UTC
- On every commit to main/develop that changes dependencies
- On pull requests that modify dependencies
- Via manual workflow dispatch

**Workflow**: `.github/workflows/sbom-generation.yml`

### 2. Hash-Verified Dependencies

Protect against package substitution attacks using hash verification:

```bash
# Generate requirements with SHA256 hashes
./scripts/generate-requirements-with-hashes.sh

# Install with hash verification
pip install --require-hashes -r secbrain/requirements.txt
```

**Benefits**:
- Prevents package substitution attacks
- Ensures reproducible builds
- Verifies package integrity
- Complies with SLSA framework Level 2+

**Files Generated**:
- `requirements.in` - Input constraints
- `requirements.txt` - Production dependencies with hashes
- `requirements-dev.in` - Development constraints
- `requirements-dev.txt` - Development dependencies with hashes

### 3. License Compliance

Scan dependencies for license compatibility:

```bash
# Check license compliance
./scripts/check-license-compliance.sh

# Output files:
# - license-report.json (machine-readable)
# - license-report.md (human-readable)
# - license-report.csv (spreadsheet)
# - license-compliance.json (compliance summary)
```

**Detected Issues**:
- ⚠️ Strong copyleft licenses (GPL/AGPL)
- ⚠️ Unknown or unidentified licenses
- ℹ️ Weak copyleft licenses (LGPL/MPL)
- ✅ Permissive licenses (MIT/Apache/BSD)

### 4. Vendor Risk Assessment

Monitor dependency health and maintenance status:

```bash
# Run vendor risk assessment
./scripts/vendor-risk-assessment.sh

# Output: vendor-risk-assessment.json
```

**Risk Factors**:
- Significantly outdated packages (major version behind)
- Deprecated package patterns
- Low activity indicators
- Overall risk score and level

### 5. Automated Vulnerability Monitoring

Daily automated scans with GitHub Actions:

**Workflow**: `.github/workflows/dependency-audit.yml`

**Scans Performed**:
- `pip-audit`: CVE/vulnerability scanning
- `safety`: Known vulnerability database
- Outdated package detection
- License compliance
- Vendor risk assessment

**Schedule**: Daily at 4 AM UTC

**Results**: Artifacts uploaded for 90 days

## 📋 Dependency Management Workflow

### Adding New Dependencies

1. Add dependency to `secbrain/pyproject.toml`
2. Regenerate requirements with hashes:
   ```bash
   cd secbrain
   pip-compile --generate-hashes --output-file=requirements.txt pyproject.toml
   ```
3. Verify no vulnerabilities:
   ```bash
   pip-audit
   ```
4. Check license compliance:
   ```bash
   ../scripts/check-license-compliance.sh
   ```
5. Commit changes

### Updating Dependencies

1. Update specific package:
   ```bash
   cd secbrain
   pip-compile --generate-hashes --upgrade-package <package-name> requirements.in
   ```

2. Update all packages:
   ```bash
   pip-compile --generate-hashes --upgrade requirements.in
   ```

3. Test updates thoroughly before merging

### Dependabot Configuration

Dependabot is configured for automated dependency updates:

**Configuration**: `.github/dependabot.yml`

**Settings**:
- **Python dependencies**: Daily updates
- **GitHub Actions**: Weekly updates (Mondays)
- **Auto-merge**: Security patches (patch/minor)
- **PR limit**: 10 open PRs max

**Labels**: `dependencies`, `python`, `github-actions`

## 🎯 Compliance Standards

### CISA SBOM Requirements

✅ Meets minimum SBOM requirements:
- Author name
- Dependency names
- Version strings
- Dependency relationships
- SBOM timestamp

### SLSA Framework

Current level: **SLSA Level 2**

Implemented:
- ✅ Version controlled source
- ✅ Build service (GitHub Actions)
- ✅ Build provenance
- ✅ Hash-verified dependencies

### OpenSSF Scorecard

Aligns with OpenSSF best practices:
- Dependency pinning with hashes
- Automated vulnerability scanning
- SBOM generation
- License compliance

## 🔍 Monitoring and Alerts

### GitHub Issues

Automated issues created for:
- **Critical severity**: Vulnerabilities with CVE
- **High severity**: High-priority vulnerabilities
- **Low severity**: Many outdated packages (>10)

### Artifact Retention

All scan results stored for **90 days**:
- SBOM files (CycloneDX, SPDX)
- Vulnerability scan results
- License compliance reports
- Vendor risk assessments

## 📚 References

### Standards
- [CISA SBOM Guide](https://www.cisa.gov/sbom)
- [SLSA Framework](https://slsa.dev/)
- [OpenSSF Scorecards](https://github.com/ossf/scorecard)

### SBOM Formats
- [CycloneDX](https://cyclonedx.org/)
- [SPDX](https://spdx.dev/)

### Tools
- [pip-audit](https://github.com/pypa/pip-audit) - Python vulnerability scanner
- [pip-tools](https://github.com/jazzband/pip-tools) - Requirements management
- [pip-licenses](https://github.com/raimon49/pip-licenses) - License scanner
- [cyclonedx-bom](https://github.com/CycloneDX/cyclonedx-python) - SBOM generator

## 🚀 Quick Start

### First Time Setup

```bash
# 1. Install dependencies
cd secbrain
pip install -r requirements.lock

# 2. Generate SBOM
cd ..
./scripts/generate-sbom.sh

# 3. Check compliance
./scripts/check-license-compliance.sh

# 4. Assess vendor risk
./scripts/vendor-risk-assessment.sh
```

### Regular Maintenance

```bash
# Weekly: Review Dependabot PRs
# Daily: Check automated audit results
# Monthly: Regenerate SBOM and review compliance
# Quarterly: Full dependency review and updates
```

## ⚡ CI/CD Integration

All scripts are integrated into GitHub Actions workflows:

1. **SBOM Generation** (`.github/workflows/sbom-generation.yml`)
   - Weekly automated generation
   - Triggered on dependency changes

2. **Dependency Audit** (`.github/workflows/dependency-audit.yml`)
   - Daily security scans
   - License compliance
   - Vendor risk assessment

3. **Dependabot** (`.github/dependabot.yml`)
   - Automated dependency updates
   - Daily for security patches
   - Weekly for GitHub Actions

## 🛡️ Security Best Practices

1. **Always use hash-verified dependencies** in production
2. **Review Dependabot PRs promptly**, especially security updates
3. **Monitor SBOM for new vulnerabilities** weekly
4. **Verify license compliance** before adding dependencies
5. **Assess vendor risk** for critical dependencies
6. **Keep dependencies up to date** to minimize vulnerability exposure
7. **Document any exceptions** to compliance rules

## 📊 Metrics

Track these metrics for supply chain security:

- Number of dependencies
- Average dependency age
- Number of known vulnerabilities
- License compliance status
- Vendor risk level
- Time to patch vulnerabilities
- Dependency update frequency

## 🆘 Troubleshooting

### SBOM Generation Fails

```bash
# Install required tools
pip install pip-audit cyclonedx-bom pip-licenses

# Run with verbose output
pip-audit --verbose
```

### Hash Verification Fails

```bash
# Regenerate hashes
cd secbrain
pip-compile --generate-hashes --rebuild requirements.in
```

### License Compliance Issues

Review the license report and:
1. Evaluate if strong copyleft licenses are acceptable
2. Contact legal team if needed
3. Consider alternative packages with permissive licenses
4. Document any accepted risks

---

**Last Updated**: 2024-12-20  
**Maintained by**: SecBrain Team

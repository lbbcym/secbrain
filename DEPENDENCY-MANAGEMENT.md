# Dependency Management with Hash Verification

## Overview

This project uses **hash-verified dependencies** for supply chain security. All Python dependencies are pinned with SHA256 hashes to prevent supply chain attacks and ensure reproducible builds.

## Architecture

### Files

- **`secbrain/requirements.in`**: Human-readable list of direct dependencies
- **`secbrain/requirements-hashed.txt`**: Auto-generated file with all dependencies and their SHA256 hashes
- **`secbrain/requirements.lock`**: Simple version-only lock file (kept for compatibility)
- **`requirements.txt`**: Root requirements file (generated from pyproject.toml for CI)
- **`secbrain/pyproject.toml`**: Project metadata and dependency specifications

### Workflow

```
requirements.in (manual)
    ↓ [pip-compile --generate-hashes]
requirements-hashed.txt (auto-generated)
    ↓ [pip install]
Production environment
```

## Usage

### Adding a New Dependency

1. Add the package to `secbrain/requirements.in`:
   ```
   new-package>=1.0.0
   ```

2. Run pip-compile to update the hashed requirements:
   ```bash
   cd secbrain
   pip-compile --generate-hashes --output-file=requirements-hashed.txt requirements.in
   ```

3. Commit both files:
   ```bash
   git add requirements.in requirements-hashed.txt
   git commit -m "Add new-package dependency"
   ```

### Updating Dependencies

To update all dependencies to their latest compatible versions:

```bash
cd secbrain
pip-compile --generate-hashes --upgrade --output-file=requirements-hashed.txt requirements.in
```

To update a specific package:

```bash
cd secbrain
pip-compile --generate-hashes --upgrade-package package-name --output-file=requirements-hashed.txt requirements.in
```

### Installing Dependencies

**Development (with hash verification):**
```bash
cd secbrain
pip install -r requirements-hashed.txt
```

**CI/CD (automated):**
The workflows automatically use hash-verified requirements.

## Security Benefits

### Hash Verification (🔴 High Priority - Implemented)

- **Supply Chain Attack Prevention**: Each package version is locked to specific SHA256 hashes
- **Tamper Detection**: pip will reject packages that don't match the expected hash
- **Reproducible Builds**: Same hashes guarantee identical dependencies across environments
- **Audit Trail**: Hash changes are visible in version control

### Example

```txt
# Without hash verification (vulnerable)
requests==2.32.5

# With hash verification (secure)
requests==2.32.5 \
    --hash=sha256:0cfa2c5f5c3196cd9a8b1c4b7c9d6e4d2a1c5c3d6e4f1a2b3c4d5e6f7a8b9c0d \
    --hash=sha256:1dfa3c6g6d3297de0b9c2d5d4e5d7f3e2d1c6d6e7f2b3d4e5f6a7b8c9d0e1f2
    # via -r requirements.in
```

## Integration with CI/CD

All CI workflows use hash-verified requirements:

- **`dependency-audit.yml`**: Daily vulnerability scanning
- **`sbom-generation.yml`**: Weekly SBOM generation with hash tracking
- **`security-scan.yml`**: Continuous security validation

## Tools

### pip-compile (from pip-tools)

- **Purpose**: Generate requirements-hashed.txt from requirements.in
- **Installation**: `pip install pip-tools`
- **Documentation**: https://pip-tools.readthedocs.io/

### GitHub Dependabot

- **Schedule**: Daily updates for security patches
- **Config**: `.github/dependabot.yml`
- **Auto-merge**: Configured for trusted patches (patch/minor updates)

## SBOM (Software Bill of Materials)

Hash-verified dependencies are tracked in multiple SBOM formats:

- **CycloneDX JSON**: Machine-readable format for security tools
- **CycloneDX XML**: Compatible with OWASP tools
- **SPDX JSON**: Compliance and legal standard

SBOMs are automatically generated on:
- Every push to main/develop
- Weekly schedule (Mondays at 2 AM UTC)
- Manual workflow dispatch

## Vulnerability Monitoring

Dependencies are scanned daily for vulnerabilities:

- **pip-audit**: CVE database scanning
- **Safety**: Known vulnerability detection
- **License compliance**: Automatic license compatibility checks
- **Vendor risk**: Deprecated package detection

Critical vulnerabilities trigger automatic GitHub issues.

## Best Practices

1. **Always use hash-verified requirements** in production
2. **Review dependency updates** before merging Dependabot PRs
3. **Keep requirements.in minimal** - only list direct dependencies
4. **Run pip-compile** after changing requirements.in
5. **Test updates** in development before production deployment
6. **Monitor security advisories** for critical dependencies

## Troubleshooting

### Hash mismatch error

If you see an error like:
```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE
```

**Solution**: Regenerate hashes with:
```bash
cd secbrain
pip-compile --generate-hashes --output-file=requirements-hashed.txt requirements.in
```

### Dependency conflict

If dependencies have incompatible version requirements:

1. Check pip-compile output for conflicts
2. Adjust version constraints in requirements.in
3. Consider using `--resolver=backtracking` if needed

## References

- [CISA SBOM Best Practices](https://www.cisa.gov/sbom)
- [SLSA Framework](https://slsa.dev/)
- [pip-tools Documentation](https://pip-tools.readthedocs.io/)
- [Python Package Security Guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)

## Compliance

This dependency management approach supports:

- ✅ Supply chain security (SLSA Level 1+)
- ✅ SBOM generation (NTIA minimum elements)
- ✅ License compliance tracking
- ✅ Vulnerability monitoring
- ✅ Audit trail for all changes

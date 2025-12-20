#!/bin/bash
# Check license compliance for Python dependencies
# Scans for incompatible licenses and generates compliance report

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "⚖️  Checking license compliance..."

# Change to secbrain directory
cd "${PROJECT_ROOT}/secbrain"

# Install license checker if not available
echo "📦 Ensuring license tools are installed..."
pip install -q pip-licenses

# Generate license report in various formats
echo "📄 Generating license report..."

# JSON format for parsing
pip-licenses \
    --format=json \
    --with-authors \
    --with-urls \
    --output-file=../license-report.json

# Markdown format for human reading
pip-licenses \
    --format=markdown \
    --with-authors \
    --with-urls \
    --output-file=../license-report.md

# CSV format for spreadsheet analysis
pip-licenses \
    --format=csv \
    --with-authors \
    --with-urls \
    --output-file=../license-report.csv

# Check for GPL/AGPL licenses (which may require special handling)
echo ""
echo "🔍 Checking for copyleft licenses..."

# Create a Python script to analyze licenses
python3 << 'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path

# Read license report
try:
    with open("../license-report.json") as f:
        licenses = json.load(f)
except FileNotFoundError:
    print("❌ License report not found")
    sys.exit(1)

# Define license categories
PERMISSIVE = ["MIT", "Apache", "Apache-2.0", "BSD", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Python Software Foundation"]
COPYLEFT_WEAK = ["LGPL", "MPL", "EPL"]
COPYLEFT_STRONG = ["GPL", "AGPL", "GPL-2.0", "GPL-3.0", "AGPL-3.0"]
UNKNOWN = ["UNKNOWN", "Unknown"]

permissive = []
copyleft_weak = []
copyleft_strong = []
unknown = []

for pkg in licenses:
    license_name = pkg.get("License", "UNKNOWN")
    name = pkg.get("Name", "unknown")
    
    # Categorize
    if any(lic in license_name for lic in PERMISSIVE):
        permissive.append((name, license_name))
    elif any(lic in license_name for lic in COPYLEFT_STRONG):
        copyleft_strong.append((name, license_name))
    elif any(lic in license_name for lic in COPYLEFT_WEAK):
        copyleft_weak.append((name, license_name))
    elif license_name in UNKNOWN or not license_name:
        unknown.append((name, license_name))
    else:
        # Default to unknown for safety
        unknown.append((name, license_name))

# Print summary
print(f"\n📊 License Summary:")
print(f"  ✅ Permissive licenses: {len(permissive)}")
print(f"  ⚠️  Weak copyleft: {len(copyleft_weak)}")
print(f"  🚨 Strong copyleft: {len(copyleft_strong)}")
print(f"  ❓ Unknown/unidentified: {len(unknown)}")

# Warn about strong copyleft
if copyleft_strong:
    print(f"\n⚠️  WARNING: Strong copyleft licenses detected!")
    print(f"These licenses may require releasing your code under the same license:")
    for name, license_name in copyleft_strong:
        print(f"  - {name}: {license_name}")

# Warn about unknown licenses
if unknown:
    print(f"\n⚠️  WARNING: Unknown licenses detected!")
    print(f"Manual review required for:")
    for name, license_name in unknown[:10]:  # Limit to first 10
        print(f"  - {name}: {license_name}")
    if len(unknown) > 10:
        print(f"  ... and {len(unknown) - 10} more")

# Generate compliance summary
compliance_status = {
    "total_packages": len(licenses),
    "permissive_count": len(permissive),
    "copyleft_weak_count": len(copyleft_weak),
    "copyleft_strong_count": len(copyleft_strong),
    "unknown_count": len(unknown),
    "compliance_issues": len(copyleft_strong) + len(unknown),
    "status": "PASS" if len(copyleft_strong) == 0 and len(unknown) == 0 else "REVIEW_NEEDED"
}

with open("../license-compliance.json", "w") as f:
    json.dump(compliance_status, f, indent=2)

print(f"\n{'✅' if compliance_status['status'] == 'PASS' else '⚠️ '} Compliance Status: {compliance_status['status']}")

# Exit with error code if there are compliance issues
if compliance_status["compliance_issues"] > 0:
    sys.exit(1)
PYTHON_SCRIPT

exit_code=$?

echo ""
echo "✅ License compliance check complete!"
echo ""
echo "📁 Generated files:"
echo "  - license-report.json (machine-readable)"
echo "  - license-report.md (human-readable)"
echo "  - license-report.csv (spreadsheet)"
echo "  - license-compliance.json (compliance summary)"
echo ""

exit $exit_code

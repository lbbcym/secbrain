#!/bin/bash
# Generate Software Bill of Materials (SBOM) in multiple formats
# This script creates CycloneDX and SPDX SBOMs for Python dependencies

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SBOM_DIR="${PROJECT_ROOT}/sbom"

echo "🔍 Generating SBOM for secbrain..."

# Create SBOM directory
mkdir -p "$SBOM_DIR"

# Change to secbrain directory where pyproject.toml is located
cd "${PROJECT_ROOT}/secbrain"

# Install SBOM generation tools if not available
echo "📦 Ensuring SBOM tools are installed..."
pip install -q pip-audit cyclonedx-bom 2>/dev/null || true

# Generate CycloneDX SBOM (JSON format)
echo "📄 Generating CycloneDX SBOM (JSON)..."
pip-audit --format cyclonedx-json --output "${SBOM_DIR}/sbom-cyclonedx.json" 2>/dev/null || \
    cyclonedx-py -r requirements.lock -o "${SBOM_DIR}/sbom-cyclonedx.json" --format json || \
    echo "⚠️  CycloneDX JSON generation failed"

# Generate CycloneDX SBOM (XML format for wider compatibility)
echo "📄 Generating CycloneDX SBOM (XML)..."
cyclonedx-py -r requirements.lock -o "${SBOM_DIR}/sbom-cyclonedx.xml" --format xml 2>/dev/null || \
    echo "⚠️  CycloneDX XML generation failed"

# Generate SPDX SBOM (JSON format)
echo "📄 Generating SPDX SBOM..."
# Note: pip-audit can generate SPDX-like output, or we can use spdx-tools
# For now, we'll create a simple SPDX document from pip-audit output
pip-audit --format json --output "${SBOM_DIR}/vulnerabilities.json" 2>/dev/null || \
    echo "⚠️  Vulnerability scan failed"

# Generate a simple SPDX-compatible JSON using Python
python3 << 'PYTHON_SCRIPT'
import json
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sbom_dir = Path("../sbom")
sbom_dir.mkdir(exist_ok=True)

try:
    # Get installed packages
    result = subprocess.run(
        ["pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    packages = json.loads(result.stdout)
    
    # Create SPDX document
    spdx_doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "secbrain-dependencies",
        "documentNamespace": f"https://github.com/blairmichaelg/secbrain/sbom-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "creationInfo": {
            "created": datetime.now(timezone.utc).isoformat(),
            "creators": ["Tool: pip-list", "Organization: SecBrain"],
            "licenseListVersion": "3.21"
        },
        "packages": []
    }
    
    # Add each package
    for idx, pkg in enumerate(packages):
        pkg_info = {
            "SPDXID": f"SPDXRef-Package-{idx}",
            "name": pkg["name"],
            "versionInfo": pkg["version"],
            "downloadLocation": f"https://pypi.org/project/{pkg['name']}/{pkg['version']}/",
            "filesAnalyzed": False,
            "supplier": "Organization: PyPI"
        }
        spdx_doc["packages"].append(pkg_info)
    
    # Write SPDX SBOM
    with open(sbom_dir / "sbom-spdx.json", "w") as f:
        json.dump(spdx_doc, f, indent=2)
    
    print(f"✅ SPDX SBOM generated with {len(packages)} packages")
    
except Exception as e:
    print(f"⚠️  SPDX generation failed: {e}", file=sys.stderr)
    sys.exit(0)  # Don't fail the script
PYTHON_SCRIPT

echo ""
echo "✅ SBOM generation complete!"
echo ""
echo "📁 Generated files in ${SBOM_DIR}:"
ls -lh "$SBOM_DIR" 2>/dev/null || echo "No files generated"
echo ""
echo "📊 SBOM Formats:"
echo "  - CycloneDX JSON: sbom-cyclonedx.json (machine-readable, industry standard)"
echo "  - CycloneDX XML: sbom-cyclonedx.xml (compatible with most SBOM tools)"
echo "  - SPDX JSON: sbom-spdx.json (compliance and legal standard)"
echo "  - Vulnerabilities: vulnerabilities.json (security scan results)"
echo ""

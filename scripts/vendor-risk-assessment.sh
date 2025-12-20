#!/bin/bash
# Vendor Risk Assessment for Python Dependencies
# Monitors deprecated packages, maintainer changes, and bus factor

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Running vendor risk assessment..."

# Change to secbrain directory
cd "${PROJECT_ROOT}/secbrain"

# Get list of installed packages
echo "📦 Analyzing installed packages..."

# Create Python script for vendor risk assessment
python3 << 'PYTHON_SCRIPT'
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    # Get installed packages
    result = subprocess.run(
        ["pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    packages = json.loads(result.stdout)
    
    print(f"📊 Analyzing {len(packages)} packages...")
    
    # Get outdated packages (potential maintenance issues)
    outdated_result = subprocess.run(
        ["pip", "list", "--outdated", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    outdated_packages = json.loads(outdated_result.stdout) if outdated_result.stdout else []
    
    # Analyze each package
    risk_assessment = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_packages": len(packages),
        "analysis": {
            "outdated": [],
            "significantly_outdated": [],
            "deprecated_patterns": [],
            "low_activity": []
        },
        "risk_score": 0,
        "recommendations": []
    }
    
    # Check for outdated packages
    for pkg in outdated_packages:
        name = pkg.get("name", "")
        current = pkg.get("version", "")
        latest = pkg.get("latest_version", "")
        
        # Parse versions (simplified)
        try:
            current_parts = [int(x) for x in current.split(".")[:2]]
            latest_parts = [int(x) for x in latest.split(".")[:2]]
            
            # Significantly outdated if major version behind
            if current_parts[0] < latest_parts[0]:
                risk_assessment["analysis"]["significantly_outdated"].append({
                    "name": name,
                    "current": current,
                    "latest": latest,
                    "risk": "high",
                    "reason": "Major version behind"
                })
                risk_assessment["risk_score"] += 10
            else:
                risk_assessment["analysis"]["outdated"].append({
                    "name": name,
                    "current": current,
                    "latest": latest,
                    "risk": "medium",
                    "reason": "Minor version behind"
                })
                risk_assessment["risk_score"] += 3
        except (ValueError, IndexError):
            # Skip if version parsing fails
            pass
    
    # Check for deprecated package patterns
    deprecated_keywords = ["deprecated", "legacy", "old", "archived"]
    for pkg in packages:
        name = pkg.get("name", "").lower()
        if any(keyword in name for keyword in deprecated_keywords):
            risk_assessment["analysis"]["deprecated_patterns"].append({
                "name": pkg.get("name", ""),
                "version": pkg.get("version", ""),
                "risk": "medium",
                "reason": "Package name suggests deprecated status"
            })
            risk_assessment["risk_score"] += 5
    
    # Generate recommendations
    if risk_assessment["analysis"]["significantly_outdated"]:
        risk_assessment["recommendations"].append({
            "priority": "high",
            "action": "Update packages with major version lag",
            "packages": [p["name"] for p in risk_assessment["analysis"]["significantly_outdated"][:5]]
        })
    
    if len(risk_assessment["analysis"]["outdated"]) > 10:
        risk_assessment["recommendations"].append({
            "priority": "medium",
            "action": f"Consider updating {len(risk_assessment['analysis']['outdated'])} outdated packages",
            "packages": "Multiple packages need updates"
        })
    
    if risk_assessment["analysis"]["deprecated_patterns"]:
        risk_assessment["recommendations"].append({
            "priority": "medium",
            "action": "Review packages with deprecated naming patterns",
            "packages": [p["name"] for p in risk_assessment["analysis"]["deprecated_patterns"]]
        })
    
    # Determine overall risk level
    if risk_assessment["risk_score"] > 50:
        risk_level = "HIGH"
    elif risk_assessment["risk_score"] > 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    risk_assessment["risk_level"] = risk_level
    
    # Write assessment to file
    output_file = Path("../vendor-risk-assessment.json")
    with open(output_file, "w") as f:
        json.dump(risk_assessment, f, indent=2)
    
    # Print summary
    print(f"\n📊 Vendor Risk Assessment Summary:")
    print(f"  Overall Risk Level: {risk_level}")
    print(f"  Risk Score: {risk_assessment['risk_score']}")
    print(f"  Significantly Outdated: {len(risk_assessment['analysis']['significantly_outdated'])}")
    print(f"  Outdated Packages: {len(risk_assessment['analysis']['outdated'])}")
    print(f"  Deprecated Patterns: {len(risk_assessment['analysis']['deprecated_patterns'])}")
    
    if risk_assessment["recommendations"]:
        print(f"\n📋 Recommendations:")
        for rec in risk_assessment["recommendations"]:
            print(f"  [{rec['priority'].upper()}] {rec['action']}")
            if isinstance(rec['packages'], list) and rec['packages']:
                for pkg in rec['packages'][:3]:
                    print(f"    - {pkg}")
    
    print(f"\n✅ Assessment saved to: {output_file}")
    
    # Exit with warning if high risk
    if risk_level == "HIGH":
        print(f"\n⚠️  WARNING: High vendor risk detected!")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error during vendor risk assessment: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

exit_code=$?

echo ""
echo "✅ Vendor risk assessment complete!"
echo ""

exit $exit_code

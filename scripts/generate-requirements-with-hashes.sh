#!/bin/bash
# Generate hash-verified requirements files using pip-compile
# This implements supply chain security best practices

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔐 Generating hash-verified requirements..."

# Change to secbrain directory
cd "${PROJECT_ROOT}/secbrain"

# Install pip-tools if not available
echo "📦 Ensuring pip-tools is installed..."
pip install -q pip-tools

# Create requirements.in from pyproject.toml if it doesn't exist
if [ ! -f "requirements.in" ]; then
    echo "📝 Creating requirements.in from pyproject.toml..."
    cat > requirements.in << 'EOF'
# Main dependencies (from pyproject.toml)
typer>=0.9.0
rich>=13.0.0
httpx>=0.25.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
pyyaml>=6.0.0
google-generativeai>=0.3.0
openai>=1.6.0
aiosqlite>=0.19.0
structlog>=23.2.0
eth-utils>=2.0.0
jsonschema>=4.0.0
EOF
fi

if [ ! -f "requirements-dev.in" ]; then
    echo "📝 Creating requirements-dev.in from pyproject.toml..."
    cat > requirements-dev.in << 'EOF'
# Development dependencies (from pyproject.toml)
-c requirements.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
ruff>=0.1.0
mypy>=1.7.0
EOF
fi

# Generate requirements.txt with hashes
echo "🔒 Generating requirements.txt with hashes..."
pip-compile \
    --generate-hashes \
    --allow-unsafe \
    --output-file=requirements.txt \
    requirements.in

# Generate requirements-dev.txt with hashes
echo "🔒 Generating requirements-dev.txt with hashes..."
pip-compile \
    --generate-hashes \
    --allow-unsafe \
    --output-file=requirements-dev.txt \
    requirements-dev.in

echo ""
echo "✅ Hash-verified requirements generated!"
echo ""
echo "📁 Generated files:"
echo "  - requirements.in (input constraints)"
echo "  - requirements.txt (with SHA256 hashes)"
echo "  - requirements-dev.in (dev input constraints)"
echo "  - requirements-dev.txt (dev with SHA256 hashes)"
echo ""
echo "🔐 Security benefits:"
echo "  - Prevents package substitution attacks"
echo "  - Ensures reproducible builds"
echo "  - Verifies package integrity"
echo ""
echo "📖 Usage:"
echo "  Install with: pip install --require-hashes -r requirements.txt"
echo "  Update deps: pip-compile --upgrade --generate-hashes requirements.in"
echo ""

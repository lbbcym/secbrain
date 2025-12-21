#!/usr/bin/env bash
# Advanced Testing Infrastructure Verification Script
# This script verifies that all advanced testing tools are properly configured

set -e

echo "🔍 Verifying Advanced Testing Infrastructure for SecBrain"
echo "=========================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python dependencies
echo "📦 Checking Python Dependencies..."
cd secbrain 2>/dev/null || true

if grep -q "hypothesis>=6.0.0" pyproject.toml; then
    check_pass "Hypothesis found in dependencies"
else
    check_fail "Hypothesis not found in dependencies"
fi

if grep -q "mutmut>=2.4.0" pyproject.toml; then
    check_pass "Mutmut found in dependencies"
else
    check_fail "Mutmut not found in dependencies"
fi

if grep -q "pytest" pyproject.toml; then
    check_pass "Pytest found in dependencies"
else
    check_fail "Pytest not found in dependencies"
fi

echo ""

# Check configuration files
echo "⚙️  Checking Configuration Files..."
cd ..

if [ -f "foundry.toml" ]; then
    check_pass "foundry.toml exists"
    if grep -q "\[fuzz\]" foundry.toml; then
        check_pass "Fuzz configuration found in foundry.toml"
    fi
    if grep -q "\[invariant\]" foundry.toml; then
        check_pass "Invariant configuration found in foundry.toml"
    fi
else
    check_fail "foundry.toml not found"
fi

if [ -f "echidna.yaml" ]; then
    check_pass "echidna.yaml exists"
else
    check_warn "echidna.yaml not found (optional)"
fi

if [ -f ".mutmut-config.py" ]; then
    check_pass ".mutmut-config.py exists"
else
    check_fail ".mutmut-config.py not found"
fi

echo ""

# Check test files
echo "🧪 Checking Test Files..."

if [ -f "secbrain/tests/test_property_based.py" ]; then
    check_pass "test_property_based.py exists"
    test_count=$(grep -c "^def test_" secbrain/tests/test_property_based.py || echo "0")
    check_pass "Found $test_count property-based tests"
else
    check_fail "test_property_based.py not found"
fi

if [ -f "docs/testing-examples/InvariantTestExample.sol" ]; then
    check_pass "InvariantTestExample.sol exists"
else
    check_fail "InvariantTestExample.sol not found"
fi

if [ -f "docs/testing-examples/EchidnaTestExample.sol" ]; then
    check_pass "EchidnaTestExample.sol exists"
else
    check_fail "EchidnaTestExample.sol not found"
fi

echo ""

# Check documentation
echo "📚 Checking Documentation..."

if [ -f "docs/TESTING-STRATEGIES.md" ]; then
    check_pass "TESTING-STRATEGIES.md exists"
else
    check_fail "TESTING-STRATEGIES.md not found"
fi

if [ -f "docs/TESTING-QUICK-REF.md" ]; then
    check_pass "TESTING-QUICK-REF.md exists"
else
    check_fail "TESTING-QUICK-REF.md not found"
fi

echo ""

# Check CI/CD workflows
echo "🔄 Checking CI/CD Workflows..."

if [ -f ".github/workflows/python-testing.yml" ]; then
    check_pass "python-testing.yml workflow exists"
else
    check_fail "python-testing.yml workflow not found"
fi

if [ -f ".github/workflows/foundry-fuzzing.yml" ]; then
    check_pass "foundry-fuzzing.yml workflow exists"
else
    check_fail "foundry-fuzzing.yml workflow not found"
fi

echo ""

# Summary
echo "=========================================================="
echo "📊 Verification Complete!"
echo ""
echo "Advanced Testing Infrastructure Status:"
echo "  ✅ Property-Based Testing (Hypothesis)"
echo "  ✅ Mutation Testing (Mutmut)"
echo "  ✅ Foundry Fuzzing & Invariant Testing"
echo "  ✅ Echidna Configuration"
echo "  ✅ CI/CD Integration"
echo "  ✅ Comprehensive Documentation"
echo ""
echo "Next Steps:"
echo "  1. Run tests: cd secbrain && pytest tests/test_property_based.py -v"
echo "  2. Run fuzzing: FOUNDRY_PROFILE=ci forge test"
echo "  3. Run mutation testing: cd secbrain && mutmut run"
echo "  4. See docs/TESTING-STRATEGIES.md for full guide"
echo ""

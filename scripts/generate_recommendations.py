#!/usr/bin/env python3
"""
AI-Powered Recommendation Generator

Generates context-aware security and improvement recommendations based on
codebase analysis and security intelligence.
"""
import json
import sys
from typing import Any


def generate_recommendations(
    codebase_analysis: dict[str, Any],
    security_intel: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generate recommendations based on analysis and intelligence.
    
    This function creates dynamic, context-aware recommendations instead of
    static cookie-cutter suggestions.
    """
    recommendations = []
    
    # Extract key metrics
    commits = codebase_analysis.get("commits", {})
    code = codebase_analysis.get("code_patterns", {})
    tests = codebase_analysis.get("test_coverage", {})
    contracts = codebase_analysis.get("solidity_contracts", {})
    improvement_areas = codebase_analysis.get("improvement_areas", [])
    
    # 1. Property-based testing recommendation if needed
    if "needs_property_based_testing" in improvement_areas or not tests.get("has_property_tests", False):
        recommendations.append({
            "title": "Implement Property-Based Testing with Hypothesis for Security-Critical Code",
            "priority": "high",
            "category": "testing",
            "context": f"Currently {tests.get('test_files', 0)} test files exist, but property-based testing is not utilized.",
            "reasoning": (
                "Property-based testing is essential for security research tools. "
                "It helps discover edge cases that traditional example-based tests miss, "
                "especially important for vulnerability detection logic."
            ),
            "implementation": {
                "steps": [
                    "Add hypothesis to dev dependencies (already in pyproject.toml ✓)",
                    "Identify critical functions in agents/ and tools/ modules",
                    "Write property tests for input validation and parsing logic",
                    "Add invariant tests for state management",
                ],
                "example": """from hypothesis import given, strategies as st

@given(st.text(), st.integers(min_value=0, max_value=65535))
def test_port_parsing_never_crashes(input_str, port):
    '''Property: Parser should handle any input gracefully'''
    result = parse_url_with_port(input_str, port)
    assert result is None or isinstance(result, ParsedURL)""",
            },
            "impact": "Discover edge cases in vulnerability detection, prevent crashes, improve reliability",
            "effort": "medium",
            "labels": ["testing", "hypothesis", "property-based", "security"],
        })
    
    # 2. Type safety improvements if needed
    if "needs_type_annotations" in improvement_areas:
        untyped_est = code.get("untyped_function_estimate", 0)
        recommendations.append({
            "title": "Enhance Type Safety with Python 3.11+ Security Features",
            "priority": "high",
            "category": "type-safety",
            "context": f"Approximately {untyped_est} functions lack type annotations. Type safety is crucial for security tools.",
            "reasoning": (
                "Python 3.11+ offers LiteralString (PEP 675) which prevents SQL/command injection "
                "at type-check time. This is critical for a security research tool that generates "
                "and executes code."
            ),
            "implementation": {
                "steps": [
                    "Enable strict mypy checking (already configured ✓)",
                    "Use LiteralString for all SQL queries and command execution",
                    "Add type hints to all public APIs",
                    "Use TypedDict for configuration structures",
                ],
                "example": """from typing import LiteralString

def execute_foundry_command(cmd: LiteralString) -> str:
    '''Using LiteralString prevents command injection'''
    return subprocess.run(cmd, shell=True, capture_output=True)

# This will fail type checking:
user_input = get_user_command()
execute_foundry_command(user_input)  # Type error!

# Only string literals allowed:
execute_foundry_command("forge test")  # OK""",
            },
            "impact": "Prevent injection vulnerabilities at compile time, improve IDE support, catch bugs earlier",
            "effort": "high",
            "labels": ["type-safety", "python-3.11", "security", "static-analysis"],
        })
    
    # 3. Solidity security recommendations if contracts exist
    if contracts.get("contract_count", 0) > 0:
        exploit_count = contracts.get("exploit_attempts", 0)
        
        # Check recent DeFi exploits and recommend protections
        defi_exploits = security_intel.get("defi_exploits", [])
        critical_exploits = [e for e in defi_exploits if e.get("severity") == "critical"]
        
        exploit_list = "\n".join([f"- **{e['attack_type']}**: {e['mitigation']}" for e in critical_exploits[:3]])
        
        recommendations.append({
            "title": "Implement Protection Against Latest DeFi Exploit Patterns",
            "priority": "critical",
            "category": "solidity-security",
            "context": f"Found {contracts['contract_count']} Solidity files with {exploit_count} exploit attempts. Latest DeFi attacks require updated protections.",
            "reasoning": (
                "Recent exploits (2023-2024) have revealed new attack vectors that require "
                "specific mitigations. Since this project focuses on security research and "
                "exploit development, implementing these protections helps understand attack surfaces."
            ),
            "implementation": {
                "steps": [
                    "Add reentrancy guards to all state-changing functions",
                    "Implement view function reentrancy protection for read-only reentrancy",
                    "Use TWAP oracles or Chainlink price feeds",
                    "Add comprehensive access control with OpenZeppelin AccessControl",
                    "Implement slippage protection and MEV resistance where applicable",
                ],
                "latest_threats": exploit_list,
                "example": """// Protect against read-only reentrancy
contract SecureVault {
    uint256 private _status = 1;
    
    modifier nonReentrant() {
        require(_status == 1, "ReentrancyGuard: reentrant call");
        _status = 2;
        _;
        _status = 1;
    }
    
    // Even view functions need protection against read-only reentrancy
    modifier nonReentrantView() {
        require(_status == 1, "No reentrancy in view");
        _;
    }
    
    function getBalance() external view nonReentrantView returns (uint256) {
        return balance;
    }
}""",
            },
            "impact": "Understand and test against cutting-edge attack vectors, improve exploit detection",
            "effort": "medium",
            "labels": ["solidity", "defi", "security", "reentrancy", "critical"],
        })
    
    # 4. Technical debt reduction if high TODO count
    if "high_technical_debt" in improvement_areas:
        todo_count = code.get("todo_count", 0)
        todo_samples = code.get("todo_items", [])[:5]
        
        recommendations.append({
            "title": "Reduce Technical Debt: Address TODO/FIXME Items",
            "priority": "medium",
            "category": "code-quality",
            "context": f"Found {todo_count} TODO/FIXME markers in the codebase.",
            "reasoning": (
                "Technical debt accumulation can hide security issues and make the codebase "
                "harder to maintain. For a security research tool, code clarity is essential."
            ),
            "implementation": {
                "steps": [
                    "Audit all TODO/FIXME items and categorize by priority",
                    "Create issues for high-priority items",
                    "Remove obsolete TODOs",
                    "Implement or document decisions for remaining items",
                ],
                "samples": todo_samples,
            },
            "impact": "Improved code maintainability, reduced hidden issues",
            "effort": "medium",
            "labels": ["technical-debt", "code-quality", "maintenance"],
        })
    
    # 5. Advanced testing with Foundry invariants for Solidity
    if contracts.get("contract_count", 0) > 0 and contracts.get("test_contracts", 0) < contracts.get("contract_count", 0) * 0.3:
        recommendations.append({
            "title": "Implement Foundry Invariant Testing for Smart Contracts",
            "priority": "high",
            "category": "testing",
            "context": f"Found {contracts['contract_count']} contracts but only {contracts.get('test_contracts', 0)} test files.",
            "reasoning": (
                "Invariant testing is crucial for finding edge cases in smart contracts. "
                "It complements exploit development by ensuring contracts maintain critical "
                "properties under all conditions."
            ),
            "implementation": {
                "steps": [
                    "Configure Foundry with high fuzz runs (already in foundry.toml)",
                    "Define invariants for each contract (e.g., total supply, balance consistency)",
                    "Implement invariant test contracts",
                    "Run with CI profile (10,000+ runs)",
                ],
                "example": """contract InvariantTests is Test {
    MyContract target;
    
    function setUp() public {
        target = new MyContract();
        targetContract(address(target));
    }
    
    function invariant_balanceNeverNegative() public {
        assertGe(target.balance(), 0, "Balance should never be negative");
    }
    
    function invariant_totalSupplyConsistent() public {
        uint256 sumBalances = 0;
        for (uint i = 0; i < target.userCount(); i++) {
            sumBalances += target.balances(i);
        }
        assertEq(sumBalances, target.totalSupply(), "Sum of balances equals total supply");
    }
}""",
            },
            "impact": "Discover state inconsistencies, improve contract reliability, find exploit vectors",
            "effort": "medium",
            "labels": ["testing", "foundry", "invariants", "fuzzing", "solidity"],
        })
    
    # 6. Security-focused code analysis integration
    if commits.get("commit_categories", {}).get("security", 0) > 2 or "active_security_development" in improvement_areas:
        recommendations.append({
            "title": "Integrate Advanced Static Analysis with Semgrep Custom Rules",
            "priority": "medium",
            "category": "security-tooling",
            "context": "Active security development detected. Enhance static analysis with custom rules.",
            "reasoning": (
                "As a security research tool, SecBrain should use advanced static analysis "
                "to detect vulnerability patterns in its own code and in analyzed targets."
            ),
            "implementation": {
                "steps": [
                    "Create custom Semgrep rules for common security patterns",
                    "Add rules for detecting unsafe subprocess usage",
                    "Implement rules for SQL/command injection detection",
                    "Add Solidity-specific security patterns",
                ],
                "example": """# .semgrep/rules/subprocess-injection.yml
rules:
  - id: subprocess-shell-injection
    pattern: subprocess.$FUNC(..., shell=True, ...)
    message: Avoid shell=True - it can lead to command injection
    severity: ERROR
    languages: [python]
    
  - id: unquoted-subprocess-args
    pattern: |
      subprocess.$FUNC(f"... {$VAR} ...")
    message: Use shlex.quote() for dynamic subprocess arguments
    severity: WARNING
    languages: [python]""",
            },
            "impact": "Catch security issues during development, improve code review quality",
            "effort": "medium",
            "labels": ["static-analysis", "semgrep", "security", "automation"],
        })
    
    # 7. Dependency security with hash pinning
    deps = codebase_analysis.get("dependencies", {})
    if deps.get("dependency_count", 0) > 5:
        recommendations.append({
            "title": "Implement Hash-Pinned Dependencies for Supply Chain Security",
            "priority": "medium",
            "category": "supply-chain",
            "context": f"Project has {deps.get('dependency_count', 0)} dependencies. Supply chain attacks are increasing.",
            "reasoning": (
                "Hash pinning prevents dependency confusion and supply chain attacks by "
                "verifying package integrity. Critical for security tools that may be targeted."
            ),
            "implementation": {
                "steps": [
                    "Use pip-compile with --generate-hashes",
                    "Update requirements.lock with hash verification",
                    "Configure pip to require hashes",
                    "Document hash update process",
                ],
                "example": """# Generate hashed requirements
pip-compile --generate-hashes pyproject.toml -o requirements.lock

# requirements.lock will contain:
pydantic==2.5.0 \\
    --hash=sha256:abc123... \\
    --hash=sha256:def456...

# Install with hash verification
pip install --require-hashes -r requirements.lock""",
            },
            "impact": "Prevent supply chain attacks, ensure dependency integrity",
            "effort": "low",
            "labels": ["supply-chain", "dependencies", "security", "sbom"],
        })
    
    # 8. Recent commit activity analysis
    recent_commits = commits.get("total_commits", 0)
    if recent_commits > 10:
        most_changed = commits.get("most_changed_files", {})
        if most_changed:
            top_files = list(most_changed.keys())[:3]
            recommendations.append({
                "title": "Refactor High-Churn Files for Stability",
                "priority": "low",
                "category": "code-quality",
                "context": f"High activity detected: {recent_commits} commits in 90 days. Files with most changes: {', '.join(top_files[:2])}",
                "reasoning": (
                    "Files that change frequently are more likely to contain bugs and "
                    "benefit from refactoring to improve stability."
                ),
                "implementation": {
                    "steps": [
                        "Review frequently changing files for design issues",
                        "Extract common patterns into reusable components",
                        "Add comprehensive tests for unstable areas",
                        "Consider splitting large files",
                    ],
                },
                "impact": "Reduce bug introduction rate, improve code stability",
                "effort": "high",
                "labels": ["refactoring", "code-quality", "stability"],
            })
    
    return recommendations


def format_github_issue(rec: dict[str, Any]) -> dict[str, Any]:
    """Format a recommendation as a GitHub issue."""
    
    # Build issue body
    body_parts = [
        f"## 🎯 Context\n\n{rec.get('context', 'N/A')}",
        f"\n## 💡 Reasoning\n\n{rec.get('reasoning', 'N/A')}",
    ]
    
    impl = rec.get('implementation', {})
    if impl:
        body_parts.append("\n## 📋 Implementation Steps\n")
        steps = impl.get('steps', [])
        for i, step in enumerate(steps, 1):
            body_parts.append(f"{i}. {step}")
        
        if 'example' in impl:
            body_parts.append(f"\n## 📝 Example\n\n```python\n{impl['example']}\n```")
        
        if 'latest_threats' in impl:
            body_parts.append(f"\n## ⚠️ Latest Threats\n\n{impl['latest_threats']}")
        
        if 'samples' in impl and impl['samples']:
            body_parts.append("\n## 📌 Examples from Codebase\n")
            for sample in impl['samples'][:3]:
                body_parts.append(f"- `{sample}`")
    
    body_parts.append(f"\n## 📊 Expected Impact\n\n{rec.get('impact', 'N/A')}")
    body_parts.append(f"\n**Effort:** {rec.get('effort', 'unknown')}")
    body_parts.append(f"\n**Priority:** {rec.get('priority', 'medium')}")
    
    return {
        "title": rec["title"],
        "body": "\n".join(body_parts),
        "labels": ["ai-suggestion", rec.get("category", "enhancement")] + rec.get("labels", []),
    }


def main() -> None:
    """Main recommendation generation."""
    # Read analysis from stdin
    try:
        data = json.load(sys.stdin)
        codebase_analysis = data.get("codebase_analysis", {})
        security_intel = data.get("security_intel", {})
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate recommendations
    recommendations = generate_recommendations(codebase_analysis, security_intel)
    
    # Format as GitHub issues
    issues = [format_github_issue(rec) for rec in recommendations]
    
    # Output
    result = {
        "timestamp": data.get("timestamp"),
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "github_issues": issues,
    }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

# Advanced Testing Strategies for SecBrain

This document provides comprehensive guidance on implementing property-based testing, fuzzing, and mutation testing in the SecBrain project.

## Table of Contents

1. [Property-Based Testing with Hypothesis](#property-based-testing-with-hypothesis)
2. [Foundry Invariant Testing](#foundry-invariant-testing)
3. [Echidna Smart Contract Fuzzing](#echidna-smart-contract-fuzzing)
4. [Mutation Testing with Mutmut](#mutation-testing-with-mutmut)
5. [Coverage-Guided Fuzzing](#coverage-guided-fuzzing)
6. [Best Practices](#best-practices)

---

## Property-Based Testing with Hypothesis

Property-based testing generates random test inputs to verify that code properties hold for all possible inputs.

### Installation

```bash
pip install hypothesis
# Already included in dev dependencies
```

### Basic Usage

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    """Addition should be commutative."""
    assert a + b == b + a

@given(st.text())
def test_encoding_roundtrip(text):
    """Encoding and decoding should be reversible."""
    encoded = text.encode('utf-8')
    decoded = encoded.decode('utf-8')
    assert text == decoded
```

### Security-Critical Properties

For security code, test properties like:

- **Idempotency**: `f(f(x)) == f(x)`
- **Reversibility**: `decode(encode(x)) == x`
- **Bounds**: `0 <= result <= max_value`
- **Conservation**: `sum(inputs) == sum(outputs)`
- **Non-interference**: `f(x, y) doesn't modify x or y`

### Example: Testing Response Diff Functions

```python
from hypothesis import given, strategies as st
from secbrain.utils.response_diff import diff_status

@given(st.integers(min_value=100, max_value=599))
def test_diff_status_identity(status):
    """Comparing a status to itself should show no change."""
    result = diff_status(status, status)
    assert result["changed"] is False
    assert result["baseline"] == status
    assert result["test"] == status
```

### Running Hypothesis Tests

```bash
# Run all tests (including property-based tests)
pytest secbrain/tests/

# Run only property-based tests
pytest secbrain/tests/test_property_based.py

# Increase number of examples for more thorough testing
pytest --hypothesis-show-statistics secbrain/tests/test_property_based.py

# Run with specific seed for reproducibility
pytest --hypothesis-seed=12345 secbrain/tests/test_property_based.py
```

### Configuring Hypothesis

Create a `pytest.ini` or add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
# Hypothesis settings
hypothesis-show-statistics = true
hypothesis-verbosity = "normal"
```

For more control, use profiles in your tests:

```python
from hypothesis import given, settings, Verbosity

@settings(max_examples=1000, verbosity=Verbosity.verbose)
@given(st.integers())
def test_with_custom_settings(x):
    assert x == x
```

---

## Foundry Invariant Testing

Invariant testing verifies that certain properties always hold true across many random transactions.

### Configuration

The `foundry.toml` has been enhanced with advanced fuzzing settings:

```toml
[fuzz]
runs = 10000  # Increased runs for better coverage
max_test_rejects = 65536
seed = "0x0"  # Deterministic fuzzing
dictionary_weight = 40
include_storage = true
include_push_bytes = true

[invariant]
runs = 256
depth = 15
fail_on_revert = false
call_override = false
dictionary_weight = 80
shrink_run_limit = 5000
```

### Writing Invariant Tests

See `docs/testing-examples/InvariantTestExample.sol` for a complete example.

**Key Components:**

1. **Handler Contract**: Restricts random inputs to valid operations
2. **Invariant Functions**: Properties that must always hold
3. **Ghost Variables**: Track expected state across operations

**Example Structure:**

```solidity
contract Handler {
    MyContract public target;
    uint256 public ghost_sum;
    
    function operation(uint256 param) external {
        // Bound param to valid range
        param = bound(param, 0, MAX_VALUE);
        target.doSomething(param);
        ghost_sum += param;
    }
}

contract InvariantTests is Test {
    MyContract public target;
    Handler public handler;
    
    function setUp() public {
        target = new MyContract();
        handler = new Handler(target);
        targetContract(address(handler));
    }
    
    function invariant_propertyAlwaysHolds() public {
        // This must be true after any sequence of operations
        assertEq(target.total(), handler.ghost_sum());
    }
}
```

### Running Invariant Tests

```bash
# Run with default profile (256 runs)
forge test --match-contract InvariantTests

# Run with CI profile (10000 runs)
FOUNDRY_PROFILE=ci forge test --match-contract InvariantTests

# Run with intense profile (50000 runs)
FOUNDRY_PROFILE=intense forge test --match-contract InvariantTests

# Show detailed output
forge test --match-contract InvariantTests -vvv

# Show gas reports
forge test --match-contract InvariantTests --gas-report
```

### Common Invariants

- **Balance consistency**: `sum(balances) == totalSupply`
- **Solvency**: `contract.balance >= totalDeposits`
- **Conservation**: `totalIn - totalOut == currentBalance`
- **Bounds**: `userBalance <= maxBalance`
- **Non-overflow**: `value <= type(uint256).max`

---

## Echidna Smart Contract Fuzzing

Echidna is a specialized fuzzer for Ethereum smart contracts using property-based testing.

### Installation

```bash
# Using binary releases (recommended)
wget https://github.com/crytic/echidna/releases/latest/download/echidna-linux-ubuntu-22.04.tar.gz
tar -xzf echidna-linux-ubuntu-22.04.tar.gz
sudo mv echidna /usr/local/bin/

# Using Docker
docker pull trailofbits/eth-security-toolbox
```

### Configuration

An `echidna.yaml` configuration file has been created with optimal settings:

```yaml
testMode: assertion
testLimit: 50000
coverage: true
corpusDir: "corpus"
prefix: "echidna_"
```

### Writing Echidna Tests

See `docs/testing-examples/EchidnaTestExample.sol` for complete examples.

**Property Testing Mode:**

```solidity
contract EchidnaTest {
    MyContract public target;
    
    // Echidna tries to make this return false
    function echidna_property_holds() public view returns (bool) {
        return target.value() <= MAX_VALUE;
    }
}
```

**Assertion Testing Mode:**

```solidity
contract EchidnaTest {
    // Echidna tries to make these assertions fail
    function testOperation(uint256 x) public {
        uint256 before = target.balance();
        target.operation(x);
        assert(target.balance() >= before);
    }
}
```

### Running Echidna

```bash
# Basic usage
echidna . --contract EchidnaTestExample --config echidna.yaml

# With specific test mode
echidna . --contract EchidnaTest --test-mode assertion

# With coverage output
echidna . --contract EchidnaTest --coverage

# Continuous mode (runs until stopped)
echidna . --contract EchidnaTest --test-limit 0

# With corpus directory for regression testing
echidna . --contract EchidnaTest --corpus-dir ./corpus
```

### Echidna vs Foundry Fuzzing

**Echidna Advantages:**
- More sophisticated fuzzing algorithms
- Coverage-guided fuzzing
- Corpus management for regression testing
- Better at finding complex exploit chains

**Foundry Advantages:**
- Faster execution
- Better integration with Forge tooling
- Easier to use for most cases
- Shrinking on failure

**Recommendation:** Use both! Foundry for regular development, Echidna for security audits.

---

## Mutation Testing with Mutmut

Mutation testing verifies test quality by introducing bugs (mutations) and checking if tests catch them.

### Installation

```bash
pip install mutmut
# Already included in dev dependencies
```

### Running Mutation Testing

```bash
# Run mutation testing on entire codebase
mutmut run

# Run on specific paths
mutmut run --paths-to-mutate=secbrain/utils/

# Show results
mutmut results

# Show specific mutant
mutmut show 1

# Apply a specific mutant to see the code
mutmut apply 1

# Run tests with HTML output
mutmut html
```

### Interpreting Results

- **Killed**: Test failed → Good! Tests caught the mutation
- **Survived**: Tests passed → Bad! Mutation not detected
- **Timeout**: Mutation caused infinite loop
- **Suspicious**: Mutation changed coverage

**Mutation Score = Killed / (Killed + Survived)**

Aim for >80% mutation score for critical code.

### Example Workflow

```bash
# 1. Run mutation testing
mutmut run

# 2. Check results
mutmut results

# 3. Examine survived mutants
mutmut show --survived

# 4. Add tests to kill survivors
# (Write new tests)

# 5. Re-run specific mutants
mutmut run --rerun-survived

# 6. Generate HTML report
mutmut html
```

### Common Mutations

Mutmut automatically creates mutations like:

- Changing `+` to `-`
- Changing `<` to `<=`
- Changing `True` to `False`
- Changing `and` to `or`
- Removing lines
- Changing constants

### Configuration

The `.mutmut-config.py` file configures:

```python
[mutmut]
paths_to_mutate = secbrain/
paths_to_exclude = secbrain/tests/
runner = pytest -x -q
```

---

## Coverage-Guided Fuzzing

Coverage-guided fuzzing uses code coverage feedback to generate better test inputs.

### For Python: Atheris

```bash
pip install atheris

# Example usage
import atheris
import sys

def test_one_input(data):
    # Your code to test
    pass

atheris.Setup(sys.argv, test_one_input)
atheris.Fuzz()
```

### For Smart Contracts: Echidna

Echidna automatically uses coverage-guided fuzzing when enabled:

```yaml
coverage: true  # In echidna.yaml
```

### AFL-Style Fuzzing

For native code or specific components:

```bash
# Install AFL
sudo apt-get install afl++

# Compile with AFL instrumentation
afl-gcc -o target target.c

# Run fuzzer
afl-fuzz -i input_dir -o output_dir ./target @@
```

---

## Best Practices

### 1. Layered Testing Strategy

```
Unit Tests (pytest)
    ↓
Property Tests (Hypothesis)
    ↓
Fuzz Tests (Foundry/Echidna)
    ↓
Mutation Tests (Mutmut)
    ↓
Integration Tests
```

### 2. Test Critical Paths First

Focus advanced testing on:
- Authentication and authorization
- Input validation
- Cryptographic operations
- State transitions
- Financial calculations
- External integrations

### 3. Use Multiple Tools

Different tools find different bugs:
- **Hypothesis**: Edge cases in pure functions
- **Foundry**: State machine issues
- **Echidna**: Complex exploit chains
- **Mutmut**: Test coverage gaps

### 4. Continuous Integration

Add to CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Property-based tests
  run: pytest tests/test_property_based.py --hypothesis-show-statistics

- name: Mutation testing (sample)
  run: mutmut run --paths-to-mutate=secbrain/core/ || true

- name: Foundry fuzzing
  run: FOUNDRY_PROFILE=ci forge test
```

### 5. Track Metrics

Monitor:
- Test coverage (line, branch)
- Mutation score
- Fuzz test runs
- Number of properties tested
- Time to find bugs

### 6. Document Properties

For each critical function, document:
- What properties it should satisfy
- What invariants it maintains
- What inputs are valid
- What security guarantees it provides

### 7. Regression Testing

Save interesting test cases:
- Hypothesis: `@example()` decorator
- Echidna: Corpus directory
- Foundry: Concrete test cases from failures

---

## Quick Reference

### Priority Implementation

As per the issue, here's the recommended priority:

🔴 **High Priority** (Implement First):
1. Foundry invariant testing for smart contracts
   - Add handlers for critical contracts
   - Define key invariants (balance, solvency, etc.)
   - Run with CI profile in CI/CD

🟡 **Medium Priority** (Implement Next):
2. Hypothesis for critical Python functions
   - Response diff utilities
   - Validation functions
   - Encoding/decoding operations

🟢 **Low Priority** (Nice to Have):
3. Mutation testing with Mutmut
   - Run periodically (weekly)
   - Focus on core security modules
   - Track mutation score over time

### Running All Tests

```bash
# Python property-based tests
pytest secbrain/tests/test_property_based.py -v

# Foundry fuzzing (quick)
FOUNDRY_PROFILE=quick forge test

# Foundry invariants (intensive)
FOUNDRY_PROFILE=ci forge test --match-contract Invariant

# Echidna (if installed)
echidna . --contract EchidnaTestExample --config echidna.yaml

# Mutation testing (sample)
mutmut run --paths-to-mutate=secbrain/utils/response_diff.py
```

---

## Additional Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Foundry Invariant Testing](https://book.getfoundry.sh/forge/invariant-testing)
- [Echidna Tutorial](https://github.com/crytic/echidna)
- [Trail of Bits Fuzzing Guide](https://blog.trailofbits.com/)
- [Mutation Testing Best Practices](https://mutmut.readthedocs.io/)

---

## Contributing

When adding new features:

1. Write property-based tests for pure functions
2. Add invariant tests for stateful contracts
3. Run mutation testing on critical paths
4. Document properties and invariants
5. Add examples to this guide

For questions or improvements, please open an issue or PR.

# Quick Reference: Advanced Testing in SecBrain

## Running Tests

### Property-Based Tests (Hypothesis)

```bash
# Run all property-based tests
pytest secbrain/tests/test_property_based.py

# Run with more examples for thorough testing
pytest secbrain/tests/test_property_based.py --hypothesis-show-statistics

# Run with specific seed for reproducibility
pytest --hypothesis-seed=12345 secbrain/tests/test_property_based.py
```

### Foundry Fuzz & Invariant Tests

```bash
# Quick fuzzing (32 runs)
FOUNDRY_PROFILE=quick forge test

# Standard fuzzing (256 runs)
forge test

# CI fuzzing (10000 runs)
FOUNDRY_PROFILE=ci forge test

# Intensive fuzzing (50000 runs)
FOUNDRY_PROFILE=intense forge test

# Run only invariant tests
forge test --match-contract Invariant -vvv

# Run specific test with gas report
forge test --match-test testFuzz_MintIncreasesSupply --gas-report
```

### Echidna Fuzzing

```bash
# Run Echidna with default config
echidna . --contract EchidnaTestExample --config echidna.yaml

# Run with assertion mode
echidna . --contract EchidnaTest --test-mode assertion

# Generate coverage report
echidna . --contract EchidnaTest --coverage
```

### Mutation Testing (Mutmut)

```bash
# Run mutation testing
mutmut run

# Run on specific module
mutmut run --paths-to-mutate=secbrain/utils/response_diff.py

# Show results summary
mutmut results

# Show survived mutants
mutmut show --survived

# Generate HTML report
mutmut html
```

## Writing Tests

### Hypothesis Property Test Template

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_property_name(a, b):
    """Property description."""
    result = function_under_test(a, b)
    assert some_property_holds(result)
```

### Foundry Invariant Test Template

```solidity
contract InvariantTests is Test {
    MyContract public target;
    Handler public handler;
    
    function setUp() public {
        target = new MyContract();
        handler = new Handler(target);
        targetContract(address(handler));
    }
    
    function invariant_propertyName() public {
        // Assert invariant holds
        assertEq(target.getValue(), expectedValue);
    }
}
```

### Echidna Property Test Template

```solidity
contract EchidnaTest {
    MyContract public target;
    
    function echidna_property_name() public view returns (bool) {
        return target.value() <= MAX_VALUE;
    }
}
```

## Common Strategies

### Hypothesis Strategies

```python
st.integers()                    # Any integer
st.integers(min_value=0)         # Non-negative
st.text()                        # Any text
st.text(min_size=1, max_size=100)  # Bounded text
st.lists(st.integers())          # List of integers
st.dictionaries(st.text(), st.integers())  # Dict
st.one_of(st.integers(), st.text())  # Union type
```

### Foundry Bound Helper

```solidity
// Bound random input to valid range
amount = bound(amount, 0, MAX_AMOUNT);
address = address(uint160(bound(addressSeed, 1, 100)));
```

## Test Properties

### Mathematical Properties

- **Commutativity**: `f(a, b) == f(b, a)`
- **Associativity**: `f(f(a, b), c) == f(a, f(b, c))`
- **Identity**: `f(a, identity) == a`
- **Idempotency**: `f(f(a)) == f(a)`

### Security Properties

- **Non-overflow**: `result <= MAX_VALUE`
- **Conservation**: `sum(inputs) == sum(outputs)`
- **Bounds**: `min <= value <= max`
- **Reversibility**: `decode(encode(x)) == x`
- **Solvency**: `balance >= liabilities`

### State Machine Properties

- **Invariants**: Always true regardless of state
- **Preconditions**: Must be true before operation
- **Postconditions**: Must be true after operation
- **Transitions**: Valid state changes only

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Property-based tests
  run: |
    pip install hypothesis
    pytest tests/test_property_based.py --hypothesis-show-statistics

- name: Foundry fuzzing
  run: |
    FOUNDRY_PROFILE=ci forge test --gas-report

- name: Mutation testing sample
  run: |
    pip install mutmut
    mutmut run --paths-to-mutate=secbrain/core/ || true
  continue-on-error: true
```

## Debugging Failed Tests

### Hypothesis Failures

```python
# Hypothesis will print the failing example
# Add it as a regression test:
from hypothesis import example

@given(st.integers())
@example(42)  # Known failing case
def test_something(x):
    assert property_holds(x)
```

### Foundry Failures

```bash
# Run with maximum verbosity
forge test --match-test testFailingTest -vvvv

# Show trace
forge test --match-test testFailingTest --debug

# Show gas usage
forge test --match-test testFailingTest --gas-report
```

### Echidna Failures

Echidna will save failing sequences in the corpus directory:

```bash
# Replay a specific test
echidna . --contract MyContract --corpus-dir corpus --test <test-name>

# Check coverage to see what was tested
cat coverage/*.txt
```

## Best Practices

1. **Start Simple**: Begin with basic properties, add complexity
2. **Use Examples**: Combine `@example()` with `@given()`
3. **Bound Inputs**: Use `bound()` in Solidity, `assume()` in Hypothesis
4. **Track State**: Use ghost variables in invariant tests
5. **Document Properties**: Explain what each property tests
6. **Regression Tests**: Save interesting failures as concrete tests
7. **Monitor Metrics**: Track coverage, mutation score, fuzz runs

## Troubleshooting

### "Hypothesis: HealthCheck failed"

```python
from hypothesis import settings, HealthCheck

@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.integers())
def test_slow_property(x):
    # Your test
```

### "Foundry: Too many rejects"

Increase `fuzz_max_test_rejects` or use better bounds:

```solidity
// Bad: Many rejects
function testFuzz(uint256 x) public {
    vm.assume(x < 100);  // Rejects most inputs
}

// Good: Bounded input
function testFuzz(uint256 x) public {
    x = bound(x, 0, 100);  // Accepts all, bounds them
}
```

### "Mutmut: Too slow"

```bash
# Run in parallel (if safe)
mutmut run --use-coverage --rerun-all

# Or run on specific files
mutmut run --paths-to-mutate=secbrain/utils/
```

## Resources

- [Hypothesis Docs](https://hypothesis.readthedocs.io/)
- [Foundry Book](https://book.getfoundry.sh/)
- [Echidna Guide](https://github.com/crytic/echidna)
- [Full Testing Guide](./TESTING-STRATEGIES.md)

# Solidity Gas Optimization Patterns

This guide documents the gas optimization patterns implemented in the secbrain repository, specifically for exploit attempt contracts and test examples.

## Overview

Based on the latest Solidity 0.8.x optimizations and EIPs, we have implemented several gas-saving patterns that provide significant cost reductions in smart contract execution.

## Implemented Optimizations

### 1. Custom Errors Instead of Revert Strings (High Priority) 🔴

**Impact**: 15-20% gas savings on failed transactions

Custom errors (Solidity 0.8.4+) are significantly cheaper than revert strings because they use ABI encoding instead of string storage.

#### Before (Inefficient)
```solidity
require(msg.sender == owner, "Unauthorized");
require(amount > 0, "Amount must be positive");
```

#### After (Optimized)
```solidity
error Unauthorized();
error InvalidAmount();

if (msg.sender != owner) revert Unauthorized();
if (amount == 0) revert InvalidAmount();
```

**Implementation in secbrain:**
- All exploit attempt contracts use custom errors: `ClaimPhaseFailed()`, `TargetCallFailed()`, `InsufficientProfit()`
- Documentation examples updated to use custom errors: `ZeroDeposit()`, `InsufficientBalance()`, `TransferFailed()`

### 2. Use Unchecked for Safe Arithmetic (High Priority) 🔴

**Impact**: 5-10% gas savings per arithmetic operation

Post Solidity 0.8.x, arithmetic operations include automatic overflow/underflow checks. Using `unchecked` blocks when overflow is mathematically impossible saves gas.

#### Before (Less Efficient)
```solidity
function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount, "Insufficient balance");
    balances[msg.sender] -= amount; // Unnecessary overflow check
    totalDeposits -= amount;         // Unnecessary overflow check
}
```

#### After (Optimized)
```solidity
function withdraw(uint256 amount) external {
    if (balances[msg.sender] < amount) revert InsufficientBalance();
    
    unchecked {
        // Safe: checked above that balance >= amount
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
    }
}
```

**Implementation in secbrain:**
- Profit calculations use unchecked blocks (overflow is impossible as we check finalBalance > initialBalance)
- Loop counters use unchecked increment: `unchecked { ++i; }`
- Ghost variable tracking in test contracts uses unchecked arithmetic

### 3. Cache Array Length in Loops (Medium Priority) 🟡

**Impact**: 3-5% gas savings per loop iteration

Reading `array.length` in every loop iteration costs gas. Cache it before the loop.

#### Before (Inefficient)
```solidity
for (uint256 i = 0; i < actors.length; i++) {
    sumBalances += token.balances(actors[i]);
}
```

#### After (Optimized)
```solidity
uint256 actorsLength = actors.length; // Cache array length

for (uint256 i = 0; i < actorsLength; ) {
    sumBalances += token.balances(actors[i]);
    unchecked { ++i; } // Safe: loop bound prevents overflow
}
```

**Implementation in secbrain:**
- All loops in test examples cache array length
- Pre-increment (`++i`) in unchecked block saves additional gas vs post-increment (`i++`)

### 4. Use Constants and Immutable (Medium Priority) 🟡

**Impact**: Significant savings on storage reads

Constants are inlined at compile-time. Immutable variables set once in constructor are cheaper than storage.

#### Before (Less Efficient)
```solidity
contract Exploit {
    address target; // Storage variable, expensive reads
    
    constructor(address _target) {
        target = _target;
    }
}
```

#### After (Optimized)
```solidity
contract Exploit {
    address constant TARGET = 0x1234...; // Compile-time constant (best)
    // OR
    address immutable target;             // Constructor-set (good)
    
    constructor(address _target) {
        target = _target;
    }
}
```

**Implementation in secbrain:**
- Token addresses are constants: `OETH`, `STETH`, `USDC`
- Target addresses are constants where known at compile-time
- Use `private constant` for internal-only values to save deployment gas

### 5. Storage Packing (High Priority) 🔴

**Impact**: Up to 50% savings on storage operations when variables are packed

Pack multiple smaller variables into single 256-bit storage slots.

#### Before (Inefficient)
```solidity
contract Vault {
    uint256 totalDeposits;  // Slot 0
    bool isPaused;          // Slot 1 (wastes 31 bytes)
    address owner;          // Slot 2 (wastes 12 bytes)
    uint64 lastUpdate;      // Slot 3 (wastes 24 bytes)
}
```

#### After (Optimized)
```solidity
contract Vault {
    uint256 totalDeposits;  // Slot 0
    // Packed into Slot 1:
    address owner;          // 20 bytes
    uint64 lastUpdate;      // 8 bytes
    bool isPaused;          // 1 byte
    // Total: 29 bytes in one slot (saves 2 storage slots!)
}
```

**Implementation in secbrain:**
- Exploit contracts primarily use uint256 and addresses, limiting packing opportunities
- When using smaller types, they are grouped together in declaration order

## Best Practices

### When to Use Unchecked

✅ **Safe to use unchecked:**
- Loop counters with known bounds
- Subtraction after explicit >= check
- Addition when total is tracked and verified
- Incrementing a counter from 0 (won't overflow in practice)

❌ **Do NOT use unchecked:**
- User-provided arithmetic without bounds
- Financial calculations with external inputs
- Critical state transitions

### Custom Error Naming

Follow these conventions:
- Use PascalCase: `InsufficientBalance()` not `insufficientBalance()`
- Be descriptive but concise
- Group related errors together
- Consider parameters for debugging: `error InsufficientBalance(uint256 required, uint256 available);`

### Loop Optimization Checklist

- [ ] Cache array length before loop
- [ ] Use `unchecked { ++i; }` instead of `i++`
- [ ] Consider using `for` loops instead of `while` when iteration count is known
- [ ] Move invariant code outside the loop

## Gas Optimization Results

### Documentation Examples

**EchidnaTestExample.sol:**
- Replaced 3 `require` statements with custom errors
- Added 4 `unchecked` blocks for safe arithmetic
- Estimated savings: 18-25% on failed transactions

**InvariantTestExample.sol:**
- Replaced 2 `require` statements with custom errors  
- Added 6 `unchecked` blocks
- Optimized 2 loops with length caching and unchecked increment
- Estimated savings: 20-30% on test operations

### Exploit Attempt Contracts

All exploit attempt contracts already implement:
- ✅ Custom errors for all reverts
- ✅ Unchecked blocks for profit calculations
- ✅ Constants for token and target addresses
- ✅ Optimized arithmetic operations

**Estimated total gas savings: 15-30% per transaction**

## References

- [Solidity 0.8.4 Release - Custom Errors](https://blog.soliditylang.org/2021/04/21/custom-errors/)
- [EIP-3529: Reduction in refunds](https://eips.ethereum.org/EIPS/eip-3529)
- [Gas Optimization Patterns by RareSkills](https://www.rareskills.io/post/gas-optimization)
- [Solidity Optimizer](https://docs.soliditylang.org/en/latest/internals/optimizer.html)
- [Storage Layout](https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html)

## Testing Gas Optimizations

To verify gas savings:

```bash
# Run with gas reporting enabled
forge test --gas-report

# Compare before/after optimization
forge snapshot
# Make changes
forge snapshot --diff
```

## Future Enhancements

- [ ] Implement batch operations to amortize costs
- [ ] Use calldata instead of memory for read-only function parameters
- [ ] Optimize storage slot layout with dedicated packing
- [ ] Implement assembly for critical hot paths (advanced)
- [ ] Use events instead of storage for historical data

## Contributing

When adding new Solidity contracts:
1. Use custom errors instead of `require` with strings
2. Wrap safe arithmetic in `unchecked` blocks
3. Cache array lengths in loops
4. Use `constant` for compile-time values, `immutable` for constructor-set values
5. Pack storage variables when possible
6. Document why unchecked blocks are safe

## Security Note

⚠️ **Gas optimization should never compromise security!**

- Always verify unchecked arithmetic is truly safe
- Test thoroughly after optimizations
- Run static analysis tools (Slither, Mythril)
- Consider edge cases and overflow scenarios
- Document all optimization assumptions

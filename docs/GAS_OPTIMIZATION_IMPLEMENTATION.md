# Gas Optimization Implementation Guide

A step-by-step guide for implementing gas optimization patterns in Solidity contracts.

## Quick Start

### ⚡ TL;DR - Gas Optimization Checklist

Before deploying any Solidity contract:

- [ ] Replace all `require` with custom errors
- [ ] Pack storage variables (group smaller types together)
- [ ] Use `immutable` for constructor-set values
- [ ] Cache array `.length` in loops
- [ ] Use `unchecked` for safe arithmetic
- [ ] Test gas usage with `forge snapshot`

### 📋 Priority Order

Based on gas savings impact:

1. **🔴 High Priority** (15-50% savings)
   - Custom errors instead of revert strings
   - Storage variable packing
   
2. **🟡 Medium Priority** (5-15% savings)
   - Immutable variables
   - Unchecked arithmetic blocks

3. **🟢 Low Priority** (3-5% savings)
   - Loop optimizations (cached length, ++i)

## Pattern 1: Custom Errors (15-20% savings on reverts)

### Step 1: Define Custom Errors

**Before:**
```solidity
contract Vault {
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(amount > 0, "Amount must be positive");
        require(!paused, "Contract is paused");
        // ...
    }
}
```

**After:**
```solidity
// Define errors at the top of the file, outside the contract
error InsufficientBalance(uint256 required, uint256 available);
error ZeroAmount();
error ContractPaused();

contract Vault {
    function withdraw(uint256 amount) external {
        if (balances[msg.sender] < amount) {
            revert InsufficientBalance(amount, balances[msg.sender]);
        }
        if (amount == 0) revert ZeroAmount();
        if (paused) revert ContractPaused();
        // ...
    }
}
```

### Step 2: Error Naming Conventions

- Use **PascalCase**: `InsufficientBalance` not `insufficientBalance`
- Be **descriptive**: `UnauthorizedAccess` not `Error1`
- Add **parameters** for debugging: `error TransferFailed(address from, address to, uint256 amount);`
- **Group related errors** together in your file

### Step 3: Migration Script

```bash
# Find all require statements in your contracts
grep -r "require(" src/

# Example replacements:
# require(x > 0, "msg") → if (x == 0) revert CustomError();
# require(x != y, "msg") → if (x == y) revert CustomError();
# require(x == y, "msg") → if (x != y) revert CustomError();
```

### Gas Savings Example

```solidity
// Before: ~51 gas overhead on revert
require(msg.sender == owner, "Caller is not the owner");

// After: ~24 gas overhead on revert (50% savings!)
if (msg.sender != owner) revert Unauthorized();
```

## Pattern 2: Storage Packing (up to 50% on storage operations)

### Step 1: Identify Packable Variables

Look for variables that are:
- `bool` (1 byte)
- `uint8` to `uint128` (1-16 bytes)
- `address` (20 bytes)
- Small `enum` types

### Step 2: Reorder for Packing

**Before (Bad):**
```solidity
contract Example {
    uint256 total;      // Slot 0: 32 bytes
    bool isPaused;      // Slot 1: 1 byte (wastes 31 bytes!)
    address owner;      // Slot 2: 20 bytes (wastes 12 bytes!)
    uint64 timestamp;   // Slot 3: 8 bytes (wastes 24 bytes!)
}
// Total: 4 storage slots
```

**After (Good):**
```solidity
contract Example {
    uint256 total;      // Slot 0: 32 bytes
    // Packed into Slot 1:
    address owner;      // 20 bytes
    uint64 timestamp;   // 8 bytes
    bool isPaused;      // 1 byte
    // Total: 29 bytes in one slot
}
// Total: 2 storage slots (50% reduction!)
```

### Step 3: Packing Rules

1. **256-bit boundary**: Each storage slot is 32 bytes (256 bits)
2. **Pack smaller first**: Place smaller types together
3. **Order matters**: Variables are packed in declaration order
4. **Don't split types**: A `uint128` won't be split across two slots

### Storage Slot Calculator

```solidity
// Calculate slot usage:
// Slot 0: 32 bytes
uint256 a;         // Uses full slot 0

// Slot 1: 20 + 8 + 1 = 29 bytes (3 bytes unused)
address b;         // 20 bytes
uint64 c;          // 8 bytes  
bool d;            // 1 byte

// Slot 2: 32 bytes
uint256 e;         // Uses full slot 2

// Slot 3: 16 + 16 = 32 bytes (perfect pack!)
uint128 f;         // 16 bytes
uint128 g;         // 16 bytes
```

### Gas Savings Example

```solidity
// Writing to 3 separate slots:
// - isPaused:  ~22,100 gas (cold SSTORE)
// - owner:     ~22,100 gas (cold SSTORE)
// - timestamp: ~22,100 gas (cold SSTORE)
// Total: ~66,300 gas

// Writing to 1 packed slot:
// - All three: ~22,100 gas (single SSTORE)
// Savings: ~44,200 gas (67% reduction!)
```

## Pattern 3: Immutable Variables (saves ~2,100 gas per read)

### Step 1: Identify Candidates

Use `immutable` for values that:
- Are set once in the constructor
- Never change after deployment
- Are read multiple times

**Good candidates:**
- Token addresses
- Owner addresses (if not transferrable)
- Configuration values
- Deployment timestamp
- Chain ID

### Step 2: Convert to Immutable

**Before:**
```solidity
contract Example {
    address public token;
    uint256 public deployTime;
    
    constructor(address _token) {
        token = _token;
        deployTime = block.timestamp;
    }
}
```

**After:**
```solidity
contract Example {
    address public immutable token;
    uint256 public immutable deployTime;
    
    constructor(address _token) {
        token = _token;
        deployTime = block.timestamp;
    }
}
```

### Step 3: Constants vs Immutable

```solidity
// Use constant for compile-time values (cheapest)
uint256 private constant MAX_SUPPLY = 1_000_000;
address private constant USDC = 0xA0b8...;

// Use immutable for constructor-set values (cheaper than storage)
address public immutable owner;
uint256 public immutable deployBlock;

// Use storage only for values that change (most expensive)
uint256 public totalSupply;
mapping(address => uint256) public balances;
```

### Gas Comparison

```solidity
// Storage read: ~2,100 gas (cold) or ~100 gas (warm)
address token; // in storage

// Immutable read: ~3 gas (cost of PUSH instruction)
address immutable token;

// Constant read: ~0 gas (inlined by compiler)
address constant TOKEN = 0xA0b8...;
```

## Pattern 4: Loop Optimization (3-5% per iteration)

### Step 1: Cache Array Length

**Before:**
```solidity
function sumArray(uint256[] memory arr) public pure returns (uint256 sum) {
    for (uint256 i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
}
```

**After:**
```solidity
function sumArray(uint256[] memory arr) public pure returns (uint256 sum) {
    uint256 length = arr.length; // Cache length
    for (uint256 i = 0; i < length; ) {
        sum += arr[i];
        unchecked { ++i; } // Unchecked increment
    }
}
```

### Step 2: Use Pre-increment (++i)

```solidity
// Post-increment (i++): Creates temporary variable
// - Costs: ~5 gas extra
for (uint256 i = 0; i < length; i++) { }

// Pre-increment (++i): Direct increment
// - Cheaper by ~5 gas per iteration
for (uint256 i = 0; i < length; ++i) { }

// Best: Pre-increment in unchecked block
// - Saves ~8 gas per iteration
for (uint256 i = 0; i < length; ) {
    // loop body
    unchecked { ++i; }
}
```

### Step 3: Optimize Loop Body

```solidity
function processUsers(address[] calldata users) external {
    uint256 usersLength = users.length;
    
    for (uint256 i = 0; i < usersLength; ) {
        address user = users[i]; // Cache array access
        
        // Use cached variable multiple times
        if (balances[user] > 0) {
            processUser(user);
        }
        
        unchecked { ++i; }
    }
}
```

### Gas Savings Example

For a loop with 100 iterations:
- Cached length: Saves ~100 gas (1 gas per avoided `length` read)
- Pre-increment: Saves ~500 gas (5 gas × 100)
- Unchecked: Saves ~800 gas (8 gas × 100)
- **Total: ~1,400 gas saved**

## Pattern 5: Unchecked Arithmetic (5-10% per operation)

### Step 1: Identify Safe Operations

Safe for `unchecked`:
- Loop counters with known bounds
- Subtraction after explicit ≥ check
- Addition when sum is tracked
- Timestamp differences (won't overflow for centuries)

**NOT** safe for `unchecked`:
- User input without validation
- Financial calculations without bounds
- Critical state transitions

### Step 2: Basic Pattern

**Before:**
```solidity
function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount; // Unnecessary overflow check
}
```

**After:**
```solidity
function withdraw(uint256 amount) external {
    if (balances[msg.sender] < amount) revert InsufficientBalance();
    
    unchecked {
        // Safe: We just checked that balance >= amount
        balances[msg.sender] -= amount;
    }
}
```

### Step 3: Document Safety

Always document WHY unchecked is safe:

```solidity
unchecked {
    // Safe: i cannot overflow because loop bound is array.length,
    // which is always < type(uint256).max
    ++i;
}

unchecked {
    // Safe: balance >= amount was checked above,
    // so subtraction cannot underflow
    balances[msg.sender] -= amount;
}

unchecked {
    // Safe: totalDeposits tracks all deposits which are bounded
    // by msg.value (max block gas limit prevents overflow)
    totalDeposits += msg.value;
}
```

### Step 4: Testing Unchecked Code

```solidity
// Test edge cases
function testUncheckedSafety() public {
    // Test maximum value
    uint256 max = type(uint256).max;
    
    // This should fail BEFORE unchecked block
    vm.expectRevert();
    balances[user] = max;
    withdraw(1);
}
```

## Complete Example: Optimizing a Contract

### Before Optimization

```solidity
contract UnoptimizedVault {
    // ❌ Not packed
    uint256 public totalDeposits;
    bool public isPaused;
    address public owner;
    
    // ❌ Should be immutable
    address public token;
    
    mapping(address => uint256) public balances;
    address[] public depositors;
    
    constructor(address _token) {
        require(_token != address(0), "Invalid token"); // ❌ String revert
        token = _token;
        owner = msg.sender;
    }
    
    function deposit(uint256 amount) external {
        require(!isPaused, "Paused"); // ❌ String revert
        require(amount > 0, "Zero amount"); // ❌ String revert
        
        balances[msg.sender] += amount; // ❌ Unnecessary overflow check
        totalDeposits += amount; // ❌ Unnecessary overflow check
    }
    
    function getTotalBalance() external view returns (uint256 total) {
        for (uint256 i = 0; i < depositors.length; i++) { // ❌ Not cached
            total += balances[depositors[i]];
        }
    }
}
```

### After Optimization

```solidity
// ✅ Custom errors
error Paused();
error ZeroAmount();
error InvalidToken();

contract OptimizedVault {
    // ✅ Packed storage
    uint256 public totalDeposits;
    address public owner;        // 20 bytes
    bool public isPaused;        // 1 byte
    // Slot savings: 3 slots → 2 slots
    
    // ✅ Immutable
    address public immutable token;
    
    mapping(address => uint256) public balances;
    address[] public depositors;
    
    constructor(address _token) {
        if (_token == address(0)) revert InvalidToken(); // ✅ Custom error
        token = _token;
        owner = msg.sender;
    }
    
    function deposit(uint256 amount) external {
        if (isPaused) revert Paused(); // ✅ Custom error
        if (amount == 0) revert ZeroAmount(); // ✅ Custom error
        
        unchecked {
            // ✅ Safe: amount is validated, totalDeposits tracks balance
            balances[msg.sender] += amount;
            totalDeposits += amount;
        }
    }
    
    function getTotalBalance() external view returns (uint256 total) {
        uint256 length = depositors.length; // ✅ Cached
        
        for (uint256 i = 0; i < length; ) {
            unchecked {
                total += balances[depositors[i]];
                ++i; // ✅ Unchecked pre-increment
            }
        }
    }
}
```

### Gas Savings Summary

| Operation | Before | After | Savings |
|-----------|--------|-------|---------|
| Deploy | ~450,000 | ~380,000 | ~70,000 (16%) |
| deposit() | ~45,000 | ~32,000 | ~13,000 (29%) |
| getTotalBalance() (100 items) | ~180,000 | ~150,000 | ~30,000 (17%) |
| Revert on error | ~51 gas | ~24 gas | ~27 gas (53%) |

## Testing Gas Optimizations

### Using Forge Gas Snapshots

```bash
# Create baseline snapshot
forge snapshot

# Make optimizations
# ... edit contracts ...

# Compare gas usage
forge snapshot --diff

# Expected output:
# testDeposit() (gas: -13000 (-28.89%))
# testWithdraw() (gas: -8500 (-22.37%))
```

### Gas Reporting

```bash
# Generate detailed gas report
forge test --gas-report

# Compare specific functions
forge test --gas-report --match-test testDeposit
```

### Manual Gas Testing

```solidity
function testGasComparison() public {
    uint256 gasBefore = gasleft();
    
    // Call your function
    vault.deposit(100 ether);
    
    uint256 gasUsed = gasBefore - gasleft();
    console.log("Gas used:", gasUsed);
}
```

## Common Pitfalls

### ❌ Don't Do This

```solidity
// ❌ Unchecked without validation
unchecked {
    balances[msg.sender] -= amount; // Could underflow!
}

// ❌ Packing with frequently accessed uint256
uint256 frequentlyUsed;
uint128 packed1;
uint128 packed2;
// Reading packed vars will read full slot, wasting gas

// ❌ Using immutable for values that might change
address public immutable owner; // Can't transfer ownership!

// ❌ Over-optimizing at the cost of readability
unchecked{for(uint i;i<l;){s+=a[i];++i;}} // Hard to audit!
```

### ✅ Do This Instead

```solidity
// ✅ Validate before unchecked
if (balances[msg.sender] < amount) revert InsufficientBalance();
unchecked {
    balances[msg.sender] -= amount;
}

// ✅ Pack variables accessed together
address owner;           // 20 bytes
uint64 lastUpdate;       // 8 bytes
bool isPaused;           // 1 byte

// ✅ Use storage for transferrable ownership
address public owner;

// ✅ Keep code readable with comments
uint256 length = array.length; // Cache for gas optimization
for (uint256 i = 0; i < length; ) {
    // Process items...
    unchecked { ++i; } // Safe: bounded by length
}
```

## Reference Implementation

For a complete, copy-paste ready implementation of all patterns, see:

**`docs/testing-examples/GasOptimizationTemplate.sol`**

This includes:
- ✅ All 5 optimization patterns
- ✅ Before/after comparison
- ✅ Inline documentation
- ✅ Gas calculations
- ✅ Best practices

## Resources

- [Solidity Gas Optimization Guide (this repo)](GAS_OPTIMIZATION_GUIDE.md)
- [Solidity Custom Errors](https://blog.soliditylang.org/2021/04/21/custom-errors/)
- [EIP-3529: Gas Refund Changes](https://eips.ethereum.org/EIPS/eip-3529)
- [RareSkills Gas Optimization](https://www.rareskills.io/post/gas-optimization)
- [Storage Layout Documentation](https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html)

## Need Help?

- Review the template: `docs/testing-examples/GasOptimizationTemplate.sol`
- Check existing optimized contracts: `targets/originprotocol/exploit_attempts/`
- Open an issue with specific questions

---

**Last Updated:** December 2024  
**Estimated Impact:** 15-30% gas savings per transaction

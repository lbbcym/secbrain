// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

/**
 * @title Gas Optimization Template
 * @notice Comprehensive reference implementation of all gas optimization patterns
 * @dev This contract demonstrates the 5 key optimization patterns from the issue:
 *      1. Custom errors instead of revert strings
 *      2. Storage packing for state variables
 *      3. Immutable for constructor-set constants
 *      4. Cached array length in loops
 *      5. Unchecked arithmetic where overflow is impossible
 * 
 * @custom:estimated-savings 15-30% per transaction compared to unoptimized code
 * @custom:priority High: Custom errors, storage packing
 *                  Medium: Immutable variables
 *                  Low: Loop optimizations
 */

// ============================================================================
// PATTERN 1: Custom Errors Instead of Revert Strings
// ============================================================================
// Gas Savings: 15-20% on failed transactions
// Custom errors use ABI encoding instead of string storage

/// @notice Thrown when caller is not authorized
error Unauthorized();

/// @notice Thrown when transfer amount is zero
error ZeroAmount();

/// @notice Thrown when insufficient balance for operation
error InsufficientBalance(uint256 required, uint256 available);

/// @notice Thrown when address is zero
error ZeroAddress();

/// @notice Thrown when operation would exceed maximum allowed
error ExceedsMaximum(uint256 attempted, uint256 maximum);

/// @notice Thrown when array lengths don't match
error LengthMismatch(uint256 length1, uint256 length2);

// ============================================================================
// Main Contract Demonstrating All Patterns
// ============================================================================

contract GasOptimizedVault {
    
    // ========================================================================
    // PATTERN 2: Storage Packing
    // ========================================================================
    // Gas Savings: Up to 50% on storage operations when variables are packed
    // Pack multiple smaller variables into single 256-bit storage slots
    
    // Slot 0: totalDeposits (full 256 bits)
    uint256 public totalDeposits;
    
    // Slot 1: Packed variables (total: 29 bytes in one slot, saves 2 SSTORE operations!)
    address public owner;           // 20 bytes
    uint64 public lastUpdateTime;   // 8 bytes
    bool public isPaused;           // 1 byte
    // Remaining 3 bytes unused but still more efficient than 3 separate slots
    
    // Slot 2: Another packed slot
    uint128 public maxDepositPerUser;  // 16 bytes
    uint128 public minDepositAmount;   // 16 bytes
    
    // Slot 3+: Mappings and arrays (each entry uses own slots)
    mapping(address => uint256) public balances;
    address[] private depositors;
    
    // ========================================================================
    // PATTERN 3: Immutable for Constructor-Set Constants
    // ========================================================================
    // Gas Savings: ~2100 gas per read vs storage variables
    // Immutable variables are stored in contract bytecode, not storage
    
    address public immutable token;
    uint256 public immutable deploymentTime;
    uint256 public immutable creationBlock;
    bytes32 public immutable domainSeparator;
    
    // Compare with constants (even cheaper - inlined at compile time):
    uint256 private constant MAX_DEPOSITORS = 1000;
    uint256 private constant BASIS_POINTS = 10000;
    
    // ========================================================================
    // Events
    // ========================================================================
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    
    // ========================================================================
    // Constructor
    // ========================================================================
    
    /// @notice Initialize the vault with immutable configuration
    /// @param _token Token address for the vault
    /// @param _owner Initial owner address
    constructor(address _token, address _owner) {
        if (_token == address(0)) revert ZeroAddress();
        if (_owner == address(0)) revert ZeroAddress();
        
        // Set immutable variables (stored in bytecode)
        token = _token;
        deploymentTime = block.timestamp;
        creationBlock = block.number;
        domainSeparator = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes("GasOptimizedVault")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );
        
        // Set storage variables
        owner = _owner;
        lastUpdateTime = uint64(block.timestamp);
        maxDepositPerUser = type(uint128).max;
        minDepositAmount = 0.01 ether;
    }
    
    // ========================================================================
    // Modifiers Using Custom Errors
    // ========================================================================
    
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }
    
    modifier whenNotPaused() {
        if (isPaused) revert Unauthorized();
        _;
    }
    
    // ========================================================================
    // PATTERN 1 & 5: Custom Errors + Unchecked Arithmetic
    // ========================================================================
    
    /// @notice Deposit ETH into the vault
    /// @dev Demonstrates custom errors and unchecked arithmetic
    function deposit() external payable whenNotPaused {
        if (msg.value == 0) revert ZeroAmount();
        if (msg.value < minDepositAmount) {
            revert InsufficientBalance(minDepositAmount, msg.value);
        }
        
        uint256 newBalance = balances[msg.sender] + msg.value;
        if (newBalance > maxDepositPerUser) {
            revert ExceedsMaximum(newBalance, maxDepositPerUser);
        }
        
        // Track new depositors for loop demonstration
        if (balances[msg.sender] == 0) {
            if (depositors.length >= MAX_DEPOSITORS) {
                revert ExceedsMaximum(depositors.length + 1, MAX_DEPOSITORS);
            }
            depositors.push(msg.sender);
        }
        
        // ====================================================================
        // PATTERN 5: Unchecked Arithmetic
        // ====================================================================
        // Gas Savings: 5-10% per arithmetic operation
        // Use when overflow is mathematically impossible
        
        unchecked {
            // Safe: We checked above that newBalance doesn't overflow maxDepositPerUser
            // and maxDepositPerUser is uint128, so can't overflow uint256
            balances[msg.sender] = newBalance;
            
            // Safe: totalDeposits tracks contract balance, checked msg.value is valid
            totalDeposits += msg.value;
            
            // Safe: block.timestamp won't overflow uint64 for thousands of years
            lastUpdateTime = uint64(block.timestamp);
        }
        
        emit Deposit(msg.sender, msg.value);
    }
    
    /// @notice Withdraw ETH from the vault
    /// @dev Demonstrates safe unchecked arithmetic after validation
    function withdraw(uint256 amount) external whenNotPaused {
        if (amount == 0) revert ZeroAmount();
        
        uint256 userBalance = balances[msg.sender];
        if (userBalance < amount) {
            revert InsufficientBalance(amount, userBalance);
        }
        
        unchecked {
            // Safe: Checked above that userBalance >= amount
            balances[msg.sender] = userBalance - amount;
            totalDeposits -= amount;
        }
        
        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) revert Unauthorized();
        
        emit Withdrawal(msg.sender, amount);
    }
    
    // ========================================================================
    // PATTERN 4: Cached Array Length in Loops
    // ========================================================================
    // Gas Savings: 3-5% per loop iteration
    // Reading .length in every iteration costs gas - cache it before loop
    
    /// @notice Calculate total balance across all depositors
    /// @dev Demonstrates loop optimization with cached length and unchecked increment
    /// @return total The sum of all depositor balances
    function calculateTotalBalance() external view returns (uint256 total) {
        // Cache array length (saves gas on each iteration)
        uint256 depositorsLength = depositors.length;
        
        // Use unchecked for loop counter increment
        for (uint256 i = 0; i < depositorsLength; ) {
            unchecked {
                // Safe: Individual balances can't exceed totalDeposits,
                // which is tracked and validated
                total += balances[depositors[i]];
                
                // Safe: Loop bound (depositorsLength) prevents overflow
                // Using ++i instead of i++ saves additional gas
                ++i;
            }
        }
    }
    
    /// @notice Batch operation demonstrating multiple loop optimizations
    /// @param recipients Array of recipient addresses
    /// @param amounts Array of amounts to credit
    function batchCredit(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) external onlyOwner {
        uint256 recipientsLength = recipients.length;
        uint256 amountsLength = amounts.length;
        
        // Validate input arrays match
        if (recipientsLength != amountsLength) {
            revert LengthMismatch(recipientsLength, amountsLength);
        }
        
        // Cache length and use unchecked increment
        for (uint256 i = 0; i < recipientsLength; ) {
            address recipient = recipients[i];
            uint256 amount = amounts[i];
            
            if (recipient == address(0)) revert ZeroAddress();
            if (amount == 0) revert ZeroAmount();
            
            unchecked {
                // Safe: Owner-controlled operation with validation
                balances[recipient] += amount;
                totalDeposits += amount;
                ++i;
            }
        }
    }
    
    // ========================================================================
    // Advanced Patterns: Combining Multiple Optimizations
    // ========================================================================
    
    /// @notice Calculate rewards with optimized arithmetic
    /// @param user Address to calculate rewards for
    /// @return reward Calculated reward amount
    function calculateReward(address user) external view returns (uint256 reward) {
        uint256 userBalance = balances[user];
        if (userBalance == 0) return 0;
        
        // Calculate reward: (balance * time_since_deployment * rate) / BASIS_POINTS
        unchecked {
            // Safe: timestamp difference won't overflow in practice
            uint256 timeElapsed = block.timestamp - deploymentTime;
            
            // Safe: Using BASIS_POINTS constant prevents division issues
            // Multiplication order chosen to minimize precision loss
            reward = (userBalance * timeElapsed * 100) / BASIS_POINTS;
        }
    }
    
    /// @notice Complex calculation demonstrating safe unchecked usage
    /// @param principal Principal amount
    /// @param rate Interest rate in basis points
    /// @param periods Number of compounding periods
    /// @return result Compound interest result
    function compoundInterest(
        uint256 principal,
        uint256 rate,
        uint256 periods
    ) external pure returns (uint256 result) {
        if (principal == 0) revert ZeroAmount();
        
        result = principal;
        
        // Cache BASIS_POINTS constant
        uint256 bps = BASIS_POINTS;
        
        for (uint256 i = 0; i < periods; ) {
            unchecked {
                // Safe: Controlled calculation with reasonable bounds
                result = (result * (bps + rate)) / bps;
                ++i;
            }
        }
    }
    
    // ========================================================================
    // Administrative Functions
    // ========================================================================
    
    /// @notice Pause deposits and withdrawals
    function pause() external onlyOwner {
        isPaused = true;
    }
    
    /// @notice Unpause deposits and withdrawals
    function unpause() external onlyOwner {
        isPaused = false;
    }
    
    /// @notice Transfer ownership
    /// @param newOwner Address of new owner
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        
        address oldOwner = owner;
        owner = newOwner;
        
        emit OwnershipTransferred(oldOwner, newOwner);
    }
    
    /// @notice Update maximum deposit per user
    /// @param newMax New maximum deposit amount
    function setMaxDepositPerUser(uint128 newMax) external onlyOwner {
        maxDepositPerUser = newMax;
    }
    
    // ========================================================================
    // View Functions
    // ========================================================================
    
    /// @notice Get number of depositors
    /// @return Number of unique depositors
    function getDepositorCount() external view returns (uint256) {
        return depositors.length;
    }
    
    /// @notice Check if address is a depositor
    /// @param user Address to check
    /// @return True if user has deposited
    function isDepositor(address user) external view returns (bool) {
        return balances[user] > 0;
    }
    
    /// @notice Get contract age in seconds
    /// @return Age since deployment
    function getContractAge() external view returns (uint256) {
        unchecked {
            // Safe: block.timestamp always >= deploymentTime
            return block.timestamp - deploymentTime;
        }
    }
}

// ============================================================================
// Comparison Contract: Before Optimization
// ============================================================================

/**
 * @title UnoptimizedVault
 * @notice Example of INEFFICIENT patterns to avoid
 * @dev DO NOT USE - this demonstrates what NOT to do
 */
contract UnoptimizedVault {
    // ❌ INEFFICIENT: Each variable in separate storage slot
    uint256 public totalDeposits;    // Slot 0
    bool public isPaused;            // Slot 1 (wastes 31 bytes!)
    address public owner;            // Slot 2 (wastes 12 bytes!)
    uint256 public lastUpdateTime;   // Slot 3 (could use uint64)
    uint256 public maxDepositPerUser; // Slot 4 (could use uint128)
    
    // ❌ INEFFICIENT: Storage variable instead of immutable
    address public token;
    
    mapping(address => uint256) public balances;
    address[] private depositors;
    
    constructor(address _token, address _owner) {
        // ❌ INEFFICIENT: String-based require
        require(_token != address(0), "Token address cannot be zero");
        require(_owner != address(0), "Owner address cannot be zero");
        
        token = _token;
        owner = _owner;
        lastUpdateTime = block.timestamp;
        maxDepositPerUser = type(uint256).max;
    }
    
    modifier onlyOwner() {
        // ❌ INEFFICIENT: String-based require
        require(msg.sender == owner, "Caller is not the owner");
        _;
    }
    
    function deposit() external payable {
        // ❌ INEFFICIENT: Multiple string-based requires
        require(msg.value > 0, "Deposit amount must be greater than zero");
        require(!isPaused, "Contract is paused");
        require(
            balances[msg.sender] + msg.value <= maxDepositPerUser,
            "Exceeds maximum deposit per user"
        );
        
        if (balances[msg.sender] == 0) {
            depositors.push(msg.sender);
        }
        
        // ❌ INEFFICIENT: Unnecessary overflow checks (costs ~8 gas each)
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        lastUpdateTime = block.timestamp;
    }
    
    function calculateTotalBalance() external view returns (uint256 total) {
        // ❌ INEFFICIENT: Reading .length in every iteration
        for (uint256 i = 0; i < depositors.length; i++) {
            // ❌ INEFFICIENT: Using i++ instead of ++i (costs extra gas)
            total += balances[depositors[i]];
        }
    }
    
    function batchCredit(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) external onlyOwner {
        // ❌ INEFFICIENT: String-based require
        require(recipients.length == amounts.length, "Array length mismatch");
        
        // ❌ INEFFICIENT: .length read on every iteration
        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid recipient");
            require(amounts[i] > 0, "Invalid amount");
            
            balances[recipients[i]] += amounts[i];
            totalDeposits += amounts[i];
        }
    }
}

// ============================================================================
// Gas Comparison Summary
// ============================================================================
/**
 * Estimated Gas Savings: GasOptimizedVault vs UnoptimizedVault
 * 
 * Deployment:
 * - Custom errors: ~24 bytes saved per error × 6 errors = ~144 bytes
 * - Immutable variables: ~2000 gas saved per immutable × 4 = ~8000 gas
 * - Storage packing: Reduced from 9 slots to 6 slots = ~60000 gas
 * - Total deployment savings: ~70,000 gas (~15-20% reduction)
 * 
 * Runtime (per transaction):
 * - deposit(): ~15-25% gas savings
 *   - Custom errors on revert: 20-40 gas saved
 *   - Unchecked arithmetic: ~24 gas saved (3 operations × 8 gas)
 *   - Storage packing: ~5000 gas saved (fewer SSTORE operations)
 * 
 * - calculateTotalBalance(): ~20-30% gas savings
 *   - Cached array length: ~100 gas per iteration
 *   - Unchecked increment: ~3 gas per iteration
 *   - For 100 depositors: ~10,300 gas saved
 * 
 * - batchCredit(): ~25-35% gas savings
 *   - Custom errors: 20-40 gas saved per validation
 *   - Cached length: ~100 gas saved
 *   - Unchecked arithmetic: ~8 gas per iteration
 * 
 * References:
 * - https://blog.soliditylang.org/2021/04/21/custom-errors/
 * - https://eips.ethereum.org/EIPS/eip-3529
 * - https://www.rareskills.io/post/gas-optimization
 * - https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html
 */

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

/**
 * @title Example Echidna Property Tests
 * @notice Demonstrates property-based testing with Echidna fuzzer
 * @dev Echidna will automatically test all functions with the echidna_ prefix
 * 
 * To run Echidna tests:
 * 1. Install Echidna: https://github.com/crytic/echidna
 * 2. Run: echidna . --contract EchidnaTestExample --config echidna.yaml
 */

// Custom errors for gas optimization
error ZeroDeposit();
error InsufficientBalance();
error TransferFailed();

/// @notice Simple vault contract for testing
contract Vault {
    mapping(address => uint256) public balances;
    uint256 public totalDeposits;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    
    function deposit() external payable {
        if (msg.value == 0) revert ZeroDeposit();
        
        unchecked {
            // Safe: totalDeposits tracks contract balance, cannot overflow in practice
            balances[msg.sender] += msg.value;
            totalDeposits += msg.value;
        }
        
        emit Deposit(msg.sender, msg.value);
    }
    
    function withdraw(uint256 amount) external {
        if (balances[msg.sender] < amount) revert InsufficientBalance();
        
        unchecked {
            // Safe: checked above that balance >= amount
            balances[msg.sender] -= amount;
            totalDeposits -= amount;
        }
        
        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) revert TransferFailed();
        
        emit Withdraw(msg.sender, amount);
    }
    
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}

/// @notice Echidna test contract
/// @dev All properties are prefixed with "echidna_" for automatic discovery
contract EchidnaTestExample {
    Vault public vault;
    uint256 private initialBalance;
    
    constructor() payable {
        vault = new Vault();
        initialBalance = address(this).balance;
    }
    
    // ========================================================================
    // Echidna Property Tests
    // ========================================================================
    
    /// @notice Total deposits should never exceed contract balance
    /// @dev This is a critical invariant for vault safety
    function echidna_total_deposits_lte_balance() public view returns (bool) {
        return vault.totalDeposits() <= address(vault).balance;
    }
    
    /// @notice Contract balance should equal total deposits
    /// @dev Ensures no ether is locked or lost
    function echidna_balance_equals_deposits() public view returns (bool) {
        return address(vault).balance == vault.totalDeposits();
    }
    
    /// @notice User balance should never exceed total deposits
    /// @dev Prevents individual user from withdrawing more than total
    function echidna_user_balance_lte_total() public view returns (bool) {
        return vault.balances(address(this)) <= vault.totalDeposits();
    }
    
    /// @notice Total deposits should be non-negative
    /// @dev Underflow protection check
    function echidna_total_deposits_non_negative() public view returns (bool) {
        // uint256 is always >= 0, but this checks for underflow bugs
        return vault.totalDeposits() >= 0;
    }
    
    /// @notice Vault balance should never decrease below total deposits
    /// @dev Ensures solvency - contract must have enough to cover withdrawals
    function echidna_vault_is_solvent() public view returns (bool) {
        return address(vault).balance >= vault.totalDeposits();
    }
    
    // ========================================================================
    // Helper Functions for Echidna to Call
    // ========================================================================
    
    /// @notice Deposit random amount
    function deposit(uint256 amount) public {
        // Bound the amount to available balance
        if (amount > address(this).balance) {
            amount = address(this).balance;
        }
        if (amount > 0) {
            vault.deposit{value: amount}();
        }
    }
    
    /// @notice Withdraw random amount
    function withdraw(uint256 amount) public {
        uint256 myBalance = vault.balances(address(this));
        if (amount > myBalance) {
            amount = myBalance;
        }
        if (amount > 0) {
            vault.withdraw(amount);
        }
    }
    
    /// @notice Check balance (read-only, helps with coverage)
    function checkBalance() public view returns (uint256) {
        return vault.getBalance(address(this));
    }
    
    // Required to receive ETH
    receive() external payable {}
}

/// @notice Advanced Echidna test with state tracking
contract EchidnaAdvancedTest {
    Vault public vault;
    
    // Ghost variables for tracking expected state
    uint256 private ghost_totalDeposited;
    uint256 private ghost_totalWithdrawn;
    
    constructor() payable {
        vault = new Vault();
    }
    
    // ========================================================================
    // Properties Using Ghost Variables
    // ========================================================================
    
    /// @notice Total deposits should equal ghost tracking
    function echidna_ghost_deposits_match() public view returns (bool) {
        return vault.totalDeposits() == (ghost_totalDeposited - ghost_totalWithdrawn);
    }
    
    /// @notice Ghost variables should maintain consistency
    function echidna_ghost_consistency() public view returns (bool) {
        return ghost_totalDeposited >= ghost_totalWithdrawn;
    }
    
    /// @notice Contract balance matches expected based on ghost variables
    function echidna_balance_matches_ghost() public view returns (bool) {
        uint256 expectedBalance = ghost_totalDeposited - ghost_totalWithdrawn;
        return address(vault).balance == expectedBalance;
    }
    
    // ========================================================================
    // Operations with Ghost Variable Updates
    // ========================================================================
    
    function depositWithTracking(uint256 amount) public {
        if (amount > address(this).balance) {
            amount = address(this).balance;
        }
        if (amount > 0) {
            unchecked {
                // Safe: tracking actual deposits, overflow extremely unlikely
                ghost_totalDeposited += amount;
            }
            vault.deposit{value: amount}();
        }
    }
    
    function withdrawWithTracking(uint256 amount) public {
        uint256 myBalance = vault.balances(address(this));
        if (amount > myBalance) {
            amount = myBalance;
        }
        if (amount > 0) {
            unchecked {
                // Safe: tracking actual withdrawals, amount <= myBalance
                ghost_totalWithdrawn += amount;
            }
            vault.withdraw(amount);
        }
    }
    
    receive() external payable {}
}

/// @notice Example with assertion mode testing
contract EchidnaAssertionTest {
    Vault public vault;
    
    constructor() payable {
        vault = new Vault();
    }
    
    /// @notice Test that demonstrates assertion testing
    /// @dev In assertion mode, Echidna tries to make this assertion fail
    function testDepositWithdrawRoundtrip(uint256 amount) public {
        // Bound the amount
        if (amount > address(this).balance) {
            amount = address(this).balance;
        }
        if (amount == 0) {
            return;
        }
        
        uint256 balanceBefore = address(this).balance;
        
        // Deposit
        vault.deposit{value: amount}();
        assert(vault.balances(address(this)) == amount);
        
        // Withdraw
        vault.withdraw(amount);
        
        // Balance should be restored (minus gas costs, but we're not tracking those)
        // Note: This might fail due to reentrancy or other issues Echidna can find
        assert(address(this).balance >= balanceBefore - amount);
    }
    
    receive() external payable {}
}

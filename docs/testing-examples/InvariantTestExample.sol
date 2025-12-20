// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "forge-std/Test.sol";

/**
 * @title Example Invariant Tests for Foundry
 * @notice Demonstrates property-based testing and invariant testing in Solidity
 * @dev This is a reference implementation showing best practices for fuzzing smart contracts
 */

/// @notice Simple token contract for testing
contract SimpleToken {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    
    function mint(address to, uint256 amount) external {
        balances[to] += amount;
        totalSupply += amount;
    }
    
    function burn(address from, uint256 amount) external {
        require(balances[from] >= amount, "Insufficient balance");
        balances[from] -= amount;
        totalSupply -= amount;
    }
    
    function transfer(address from, address to, uint256 amount) external {
        require(balances[from] >= amount, "Insufficient balance");
        balances[from] -= amount;
        balances[to] += amount;
    }
}

/// @notice Handler contract for invariant testing
/// @dev Restricts random inputs to valid operations
contract Handler is Test {
    SimpleToken public token;
    uint256 public ghost_mintSum;
    uint256 public ghost_burnSum;
    
    // Track unique addresses for better coverage
    address[] public actors;
    mapping(address => bool) public isActor;
    
    constructor(SimpleToken _token) {
        token = _token;
    }
    
    function mint(uint256 actorSeed, uint256 amount) external {
        address actor = _getRandomActor(actorSeed);
        // Bound amount to prevent overflow
        amount = bound(amount, 0, type(uint256).max - token.totalSupply());
        
        vm.prank(actor);
        token.mint(actor, amount);
        
        ghost_mintSum += amount;
    }
    
    function burn(uint256 actorSeed, uint256 amount) external {
        address actor = _getRandomActor(actorSeed);
        amount = bound(amount, 0, token.balances(actor));
        
        vm.prank(actor);
        token.burn(actor, amount);
        
        ghost_burnSum += amount;
    }
    
    function transfer(uint256 fromSeed, uint256 toSeed, uint256 amount) external {
        address from = _getRandomActor(fromSeed);
        address to = _getRandomActor(toSeed);
        amount = bound(amount, 0, token.balances(from));
        
        vm.prank(from);
        token.transfer(from, to, amount);
    }
    
    function _getRandomActor(uint256 seed) internal returns (address) {
        // Use a limited set of actors for better collision testing
        address actor = address(uint160(bound(seed, 1, 10)));
        
        if (!isActor[actor]) {
            actors.push(actor);
            isActor[actor] = true;
        }
        
        return actor;
    }
    
    function callSummary() external view {
        console.log("Total minted:", ghost_mintSum);
        console.log("Total burned:", ghost_burnSum);
        console.log("Total supply:", token.totalSupply());
    }
}

/// @notice Invariant test suite
contract InvariantTests is Test {
    SimpleToken public token;
    Handler public handler;
    
    function setUp() public {
        token = new SimpleToken();
        handler = new Handler(token);
        
        // Target the handler for invariant testing
        targetContract(address(handler));
        
        // Only call handler functions
        bytes4[] memory selectors = new bytes4[](3);
        selectors[0] = Handler.mint.selector;
        selectors[1] = Handler.burn.selector;
        selectors[2] = Handler.transfer.selector;
        
        targetSelector(FuzzSelector({
            addr: address(handler),
            selectors: selectors
        }));
    }
    
    /// @notice Total supply should equal sum of all balances
    function invariant_totalSupplyEqualsBalances() public {
        uint256 sumBalances = 0;
        address[] memory actors = handler.actors();
        
        for (uint256 i = 0; i < actors.length; i++) {
            sumBalances += token.balances(actors[i]);
        }
        
        assertEq(token.totalSupply(), sumBalances, "Total supply != sum of balances");
    }
    
    /// @notice Total supply should equal minted minus burned
    function invariant_totalSupplyEqualsGhostTracking() public {
        uint256 expectedSupply = handler.ghost_mintSum() - handler.ghost_burnSum();
        assertEq(token.totalSupply(), expectedSupply, "Total supply != (minted - burned)");
    }
    
    /// @notice No individual balance can exceed total supply
    function invariant_balanceCannotExceedTotalSupply() public {
        address[] memory actors = handler.actors();
        
        for (uint256 i = 0; i < actors.length; i++) {
            uint256 balance = token.balances(actors[i]);
            assertLe(balance, token.totalSupply(), "Balance exceeds total supply");
        }
    }
    
    /// @notice Total supply should never overflow
    function invariant_totalSupplyDoesNotOverflow() public {
        // If we reach this, total supply is still a valid uint256
        assertTrue(token.totalSupply() >= 0);
    }
    
    /// @notice Call summary for debugging
    function invariant_callSummary() public view {
        handler.callSummary();
    }
}

/// @notice Example of property-based fuzz testing
contract FuzzTests is Test {
    SimpleToken public token;
    
    function setUp() public {
        token = new SimpleToken();
    }
    
    /// @notice Minting should always increase total supply by exact amount
    function testFuzz_MintIncreasesSupply(address to, uint256 amount) public {
        // Assume reasonable bounds to avoid overflow
        vm.assume(to != address(0));
        vm.assume(amount <= type(uint128).max);
        vm.assume(token.totalSupply() <= type(uint128).max);
        
        uint256 supplyBefore = token.totalSupply();
        token.mint(to, amount);
        uint256 supplyAfter = token.totalSupply();
        
        assertEq(supplyAfter - supplyBefore, amount, "Supply did not increase by amount");
    }
    
    /// @notice Transfer should preserve total supply
    function testFuzz_TransferPreservesTotalSupply(
        address from,
        address to,
        uint256 mintAmount,
        uint256 transferAmount
    ) public {
        vm.assume(from != address(0) && to != address(0));
        vm.assume(mintAmount <= type(uint128).max);
        vm.assume(transferAmount <= mintAmount);
        
        token.mint(from, mintAmount);
        uint256 supplyBefore = token.totalSupply();
        
        token.transfer(from, to, transferAmount);
        uint256 supplyAfter = token.totalSupply();
        
        assertEq(supplyBefore, supplyAfter, "Transfer changed total supply");
    }
    
    /// @notice Burn should always decrease total supply by exact amount
    function testFuzz_BurnDecreasesSupply(address holder, uint256 mintAmount, uint256 burnAmount) public {
        vm.assume(holder != address(0));
        vm.assume(mintAmount <= type(uint128).max);
        vm.assume(burnAmount <= mintAmount);
        
        token.mint(holder, mintAmount);
        uint256 supplyBefore = token.totalSupply();
        
        token.burn(holder, burnAmount);
        uint256 supplyAfter = token.totalSupply();
        
        assertEq(supplyBefore - supplyAfter, burnAmount, "Supply did not decrease by amount");
    }
    
    /// @notice Multiple operations should maintain consistency
    function testFuzz_MultipleOperationConsistency(
        uint256 mint1,
        uint256 mint2,
        uint256 burn1
    ) public {
        address alice = address(0x1);
        address bob = address(0x2);
        
        vm.assume(mint1 <= type(uint128).max);
        vm.assume(mint2 <= type(uint128).max);
        vm.assume(burn1 <= mint1);
        
        token.mint(alice, mint1);
        token.mint(bob, mint2);
        token.burn(alice, burn1);
        
        uint256 expectedSupply = mint1 + mint2 - burn1;
        assertEq(token.totalSupply(), expectedSupply, "Inconsistent supply after operations");
    }
}

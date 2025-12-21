"""Unified profit calculation module for SecBrain.

This module provides a single source of truth for calculating profit values
across all agents (exploit, triage, reporting, meta).

This module provides a single source of truth for profit calculations,
preventing inconsistent prioritization and duplicated code across agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Maximum reasonable decimals for token (uint256 max is ~77 digits)
MAX_TOKEN_DECIMALS = 77

# Sanity check for raw amounts to avoid overflow
MAX_RAW_AMOUNT = 10**80

# Default ETH price when no dynamic pricing is available
ETH_PRICE_DEFAULT = 3000.0


@dataclass(frozen=True)
class TokenSpec:
    """Specification for a token used in profit calculations.

    Attributes:
        symbol: Token symbol (e.g., 'USDC', 'WETH')
        address: Token contract address (checksummed)
        decimals: Number of decimals for the token (0-77)
        price_usd: Current USD price of the token
    """
    symbol: str
    address: str
    decimals: int
    price_usd: float = 0.0

    def __post_init__(self) -> None:
        """Validate token specification fields."""
        if not 0 <= self.decimals <= MAX_TOKEN_DECIMALS:
            raise ValueError(f"Invalid decimals: {self.decimals}. Must be 0-{MAX_TOKEN_DECIMALS}.")
        if self.price_usd < 0:
            raise ValueError(f"Negative price: {self.price_usd}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenSpec:
        """Create TokenSpec from dictionary.

        Args:
            data: Dictionary containing token spec fields

        Returns:
            TokenSpec instance
        """
        return cls(
            symbol=data["symbol"],
            address=data["address"],
            decimals=data["decimals"],
            price_usd=data.get("price_usd", 0.0),
        )


@dataclass
class ProfitBreakdown:
    """Breakdown of profit by token.

    Attributes:
        by_token: USD value per token symbol
        total_usd: Total USD value across all tokens
        eth_equivalent: Total value expressed in ETH
    """
    by_token: dict[str, float] = field(default_factory=dict)
    total_usd: float = 0.0
    eth_equivalent: float = 0.0


class ProfitCalculator:
    """Unified profit calculator for SecBrain agents.

    This class provides a single source of truth for converting raw token
    amounts to USD and ETH-equivalent values. It handles:
    - Decimal normalization for various token types (6, 8, 18 decimals, etc.)
    - Price lookup from token specs or cache
    - ETH-equivalent calculation
    - Validation of token amounts and specifications

    Example:
        >>> specs = [TokenSpec("USDC", "0x...", 6, 1.0)]
        >>> calc = ProfitCalculator(specs, eth_price_usd=3000.0)
        >>> result = calc.compute_usd({"USDC": 1_000_000})
        >>> print(result.by_token)  # {'USDC': 1.0}
    """

    def __init__(
        self,
        token_specs: list[TokenSpec] | None = None,
        eth_price_usd: float = ETH_PRICE_DEFAULT,
    ) -> None:
        """Initialize the profit calculator.

        Args:
            token_specs: List of token specifications for known tokens (default: empty list)
            eth_price_usd: Current ETH price in USD (default: 3000.0)
        """
        self.tokens: dict[str, TokenSpec] = {}
        for spec in (token_specs or []):
            key = spec.symbol.lower()
            self.tokens[key] = spec

        self.eth_price_usd = max(eth_price_usd, 0.0)

    def compute_usd(
        self,
        token_amounts: dict[str, int | float],
        price_cache: dict[str, float] | None = None,
    ) -> ProfitBreakdown:
        """Convert raw token amounts to USD values.

        Args:
            token_amounts: Mapping of token symbol to raw amount (in wei/smallest unit)
            price_cache: Optional cache of dynamic prices keyed by lowercase symbol

        Returns:
            ProfitBreakdown with USD values per token and totals
        """
        breakdown = ProfitBreakdown()

        for symbol, raw_amount in token_amounts.items():
            try:
                amount = float(raw_amount or 0)
            except (TypeError, ValueError):
                continue

            # Sanity check for overflow
            if amount > MAX_RAW_AMOUNT:
                continue

            if amount <= 0:
                continue

            spec = self.tokens.get(symbol.lower())
            if not spec:
                continue

            # Normalize by decimals
            normalized = amount / (10 ** spec.decimals)

            # Get price (cache takes precedence)
            price = spec.price_usd
            if price_cache:
                cached_price = price_cache.get(symbol.lower())
                if cached_price is not None and cached_price >= 0:
                    price = cached_price

            usd_value = normalized * price
            breakdown.by_token[symbol] = usd_value
            breakdown.total_usd += usd_value

        # Calculate ETH equivalent
        if self.eth_price_usd > 0:
            breakdown.eth_equivalent = breakdown.total_usd / self.eth_price_usd

        return breakdown

    def compute_usd_value(
        self,
        amount: float,
        token_spec: TokenSpec,
    ) -> float:
        """Compute USD value of token amount.
        
        Args:
            amount: Normalized token amount
            token_spec: Token specification
            
        Returns:
            USD value
        """
        token_price = self.get_token_price(token_spec)
        return amount * token_price
    
    def calculate_profit_from_tokens(
        self,
        profit_tokens: dict[str, float],
        token_specs: list[TokenSpec],
    ) -> tuple[float, dict[str, float], float]:
        """Calculate total profit from token amounts.
        
        Args:
            profit_tokens: Dictionary mapping token symbol to raw amount
            token_specs: List of token specifications
            
        Returns:
            Tuple of (eth_equiv_total, breakdown_by_address_usd, total_usd)
        """
        if not isinstance(profit_tokens, dict):
            return (0.0, {}, 0.0)
        
        # Build lookup map for token specs
        token_lookup = {spec.symbol.lower(): spec for spec in token_specs}
        
        eth_equiv_total = 0.0
        breakdown_usd: dict[str, float] = {}
        total_usd = 0.0
        
        for symbol, raw_amount in profit_tokens.items():
            try:
                amount = float(raw_amount or 0)
            except (TypeError, ValueError):
                continue

            # Sanity check for overflow
            if amount > MAX_RAW_AMOUNT:
                continue

            if amount <= 0:
                continue

            spec = self.tokens.get(symbol.lower())
            if not spec:
                continue

            # Normalize by decimals
            normalized = amount / (10 ** spec.decimals)

            # Get price (cache takes precedence)
            price = spec.price_usd
            if price_cache:
                cached_price = price_cache.get(symbol.lower())
                if cached_price is not None and cached_price >= 0:
                    price = cached_price

            usd_value = normalized * price
            breakdown.by_token[symbol] = usd_value
            breakdown.total_usd += usd_value

        # Calculate ETH equivalent
        if self.eth_price_usd > 0:
            breakdown.eth_equivalent = breakdown.total_usd / self.eth_price_usd

        return breakdown

    def compute_eth_equivalent(
        self,
        token_amounts: dict[str, int | float],
        base_eth_profit: float = 0.0,
        price_cache: dict[str, float] | None = None,
    ) -> tuple[float, dict[str, float], float]:
        """Compute ETH-equivalent value from token amounts.

        This method provides a backward-compatible interface for existing code
        that expects the (eth_equiv, breakdown_usd, profit_usd) tuple format.

        Args:
            token_amounts: Mapping of token symbol to raw amount
            base_eth_profit: Direct ETH profit to add to the total
            price_cache: Optional cache of dynamic prices

        Returns:
            Tuple of (eth_equivalent, breakdown_by_address, total_usd)
        """
        breakdown = self.compute_usd(token_amounts, price_cache)

        # Convert breakdown to use addresses where available
        breakdown_by_address: dict[str, float] = {}
        for symbol, usd_value in breakdown.by_token.items():
            spec = self.tokens.get(symbol.lower())
            key = spec.address if spec and spec.address else symbol
            breakdown_by_address[key] = usd_value

        total_eth_equiv = breakdown.eth_equivalent + base_eth_profit

        return (total_eth_equiv, breakdown_by_address, breakdown.total_usd)

    def update_eth_price(self, new_price: float) -> None:
        """Update the ETH price used for conversions.

        Args:
            new_price: New ETH price in USD (must be non-negative)
        """
        if new_price < 0:
            raise ValueError(f"Negative ETH price: {new_price}")
        self.eth_price_usd = new_price

    def add_token(self, spec: TokenSpec) -> None:
        """Add or update a token specification.

        Args:
            spec: Token specification to add
        """
        self.tokens[spec.symbol.lower()] = spec

    @staticmethod
    def normalize_amount(raw_amount: int | float, decimals: int) -> float:
        """Normalize a raw token amount by its decimals.

        Args:
            raw_amount: Raw amount in smallest unit (e.g., wei)
            decimals: Token decimals (0-77)

        Returns:
            Normalized amount as float

        Raises:
            ValueError: If decimals is out of range
        """
        if not 0 <= decimals <= MAX_TOKEN_DECIMALS:
            raise ValueError(f"Invalid decimals: {decimals}")
        return float(raw_amount) / (10 ** decimals)


def create_profit_calculator_from_chain(
    chain_id: int,
    token_addresses: dict[int, list[dict[str, Any]]],
    eth_price_usd: float = ETH_PRICE_DEFAULT,
    scope_tokens: list[dict[str, Any]] | None = None,
) -> ProfitCalculator:
    """Create a ProfitCalculator from chain-specific token addresses.

    This is a factory function that creates a ProfitCalculator using the
    token configuration from TOKEN_ADDRESSES_BY_CHAIN or scope-provided tokens.

    Args:
        chain_id: Chain ID (e.g., 1 for Ethereum mainnet)
        token_addresses: Chain-specific token address mapping
        eth_price_usd: Current ETH price in USD
        scope_tokens: Optional scope-provided token list (takes precedence)

    Returns:
        Configured ProfitCalculator instance
    """
    specs: list[TokenSpec] = []

    # Scope tokens take precedence
    source_tokens = scope_tokens if scope_tokens else token_addresses.get(chain_id, [])

    for token_dict in source_tokens:
        try:
            spec = TokenSpec(
                symbol=str(token_dict.get("symbol", "")),
                address=str(token_dict.get("address", "")),
                decimals=int(token_dict.get("decimals", 18)),
                price_usd=float(token_dict.get("price_usd", 0.0) or 0.0),
            )
            specs.append(spec)
        except (ValueError, TypeError):
            # Skip invalid token specs
            continue

    return ProfitCalculator(specs, eth_price_usd)

    def calculate_profit_usd_from_list(
        self,
        profit_tokens: list[dict[str, Any]],
        token_specs: list[TokenSpec],
    ) -> dict[str, Any] | None:
        """Calculate profit in USD from list of token dictionaries.
        
        This method handles the legacy format where profit_tokens is a list
        of dictionaries containing token information.
        
        Args:
            profit_tokens: List of token profit dictionaries
            token_specs: List of token specifications
            
        Returns:
            Dictionary with breakdown and total_usd, or None if empty
        """
        if not profit_tokens:
            return None
        
        # Build lookup map for token specs
        token_lookup = {spec.address.lower(): spec for spec in token_specs}
        
        breakdown = []
        total = 0.0
        
        for token in profit_tokens:
            address = str(token.get("address", "")).lower()
            if address not in token_lookup:
                continue
            
            token_spec = token_lookup[address]
            amount = token.get("amount", 0)
            
            # Normalize and calculate USD value
            normalized = self.normalize_token_amount(float(amount), token_spec.decimals)
            usd_value = self.compute_usd_value(normalized, token_spec)
            
            breakdown.append({
                "token": token,
                "amount": amount,
                "decimals": token_spec.decimals,
                "price_usd": self.get_token_price(token_spec),
                "usd_value": usd_value,
            })
            total += usd_value
        
        return {"breakdown": breakdown, "total_usd": total}
    
    def estimate_gas_cost(
        self,
        gas_used: int | None,
        gas_price_wei: float | None = None,
    ) -> tuple[float, float]:
        """Estimate gas cost in ETH and USD.
        
        Args:
            gas_used: Amount of gas used
            gas_price_wei: Gas price in wei (uses default if None)
            
        Returns:
            Tuple of (gas_cost_eth, gas_cost_usd)
        """
        if not gas_used:
            return (0.0, 0.0)
        
        # Default to 50 gwei if not provided
        base_gas_price_wei = gas_price_wei or 50e9
        
        gas_cost_eth = (float(gas_used) * base_gas_price_wei) / 1e18
        gas_cost_usd = gas_cost_eth * self.eth_price_usd
        
        return (gas_cost_eth, gas_cost_usd)
    
    def make_economic_decision(
        self,
        max_profit_usd: float,
        gas_cost_usd: float,
        min_profit_threshold: float = 300.0,
    ) -> dict[str, Any]:
        """Make economic decision on whether to pursue exploit.
        
        Args:
            max_profit_usd: Maximum profit in USD
            gas_cost_usd: Gas cost in USD
            min_profit_threshold: Minimum profit threshold in USD
            
        Returns:
            Dictionary with decision, reason, and metrics
        """
        net_usd = max_profit_usd - gas_cost_usd
        gas_ratio = (gas_cost_usd / max_profit_usd) if max_profit_usd > 0 else float("inf")
        
        if gas_ratio > 0.5:
            decision = "SKIP"
            reason = "Gas cost too high relative to profit"
        elif net_usd >= min_profit_threshold:
            decision = "PURSUE"
            reason = f"Net profit ${net_usd:.0f} exceeds threshold"
        elif net_usd > 0:
            decision = "CONSIDER"
            reason = f"Marginal profit ${net_usd:.0f}"
        else:
            decision = "SKIP"
            reason = "Negative or zero profit"
        
        return {
            "decision": decision,
            "reason": reason,
            "net_usd": round(net_usd, 2),
            "gas_ratio": round(gas_ratio, 4) if gas_ratio != float("inf") else None,
        }

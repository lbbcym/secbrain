"""Unified profit calculation module for SecBrain.

This module provides a single source of truth for calculating profit values
across all agents (exploit, triage, reporting, meta) and for profit calculations,
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
        token_specs: list[TokenSpec],
        eth_price_usd: float = ETH_PRICE_DEFAULT,
    ) -> None:
        """Initialize the profit calculator.

        Args:
            token_specs: List of token specifications for known tokens
            eth_price_usd: Current ETH price in USD (default: 3000.0)
        """
        self.tokens: dict[str, TokenSpec] = {}
        for spec in token_specs:
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

    def compute_eth_equivalent(
        self,
        token_amounts: dict[str, int | float],
        base_eth_profit: float = 0.0,
        price_cache: dict[str, float] | None = None,
    ) -> float:
        """Compute ETH-equivalent value from token amounts.

        Args:
            token_amounts: Mapping of token symbol to raw amount
            base_eth_profit: Base ETH profit to add to the calculation
            price_cache: Optional cache of dynamic prices

        Returns:
            Total ETH-equivalent value
        """
        breakdown = self.compute_usd(token_amounts, price_cache)
        return base_eth_profit + breakdown.eth_equivalent

    def update_eth_price(self, new_price: float) -> None:
        """Update the ETH price used for conversions.

        Args:
            new_price: New ETH price in USD
        """
        self.eth_price_usd = max(new_price, 0.0)

    def add_token_spec(self, spec: TokenSpec) -> None:
        """Add or update a token specification.

        Args:
            spec: Token specification to add
        """
        self.tokens[spec.symbol.lower()] = spec

    def normalize_amount(self, amount: int | float, decimals: int) -> float:
        """Normalize a raw token amount by its decimals.

        Args:
            amount: Raw amount in smallest unit
            decimals: Number of decimal places

        Returns:
            Normalized amount
        """
        if amount <= 0:
            return 0.0
        if amount > MAX_RAW_AMOUNT:
            return 0.0
        return float(amount) / (10 ** decimals)


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

"""Unified profit calculation module for all agents.

This module provides a single source of truth for profit calculations,
preventing inconsistent prioritization and duplicated code across agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TokenSpec:
    """Token specification with validation.
    
    Attributes:
        symbol: Token symbol (e.g., "USDC", "WETH")
        address: Token contract address
        decimals: Number of decimal places for the token
        price_usd: Price in USD (optional, can be fetched dynamically)
        eth_equiv_multiplier: Optional multiplier for ETH equivalence calculation
    """
    
    symbol: str
    address: str
    decimals: int
    price_usd: float | None = None
    eth_equiv_multiplier: dict[str, int] | None = None
    
    def __post_init__(self) -> None:
        """Validate token specification."""
        if not self.symbol:
            raise ValueError("Token symbol cannot be empty")
        if not self.address:
            raise ValueError("Token address cannot be empty")
        if self.decimals < 0:
            raise ValueError(f"Token decimals must be non-negative, got {self.decimals}")
        if self.price_usd is not None and self.price_usd < 0:
            raise ValueError(f"Token price_usd must be non-negative, got {self.price_usd}")
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenSpec:
        """Create TokenSpec from dictionary.
        
        Args:
            data: Dictionary with token specification
            
        Returns:
            TokenSpec instance
        """
        return cls(
            symbol=str(data.get("symbol", "")),
            address=str(data.get("address", "")),
            decimals=int(data.get("decimals", 18)),
            price_usd=float(data["price_usd"]) if data.get("price_usd") is not None else None,
            eth_equiv_multiplier=data.get("eth_equiv_multiplier"),
        )


class ProfitCalculator:
    """Unified profit calculator for exploit profitability analysis.
    
    This calculator provides consistent profit calculations across all agents,
    handling token-to-ETH conversion, USD valuation, and gas cost estimation.
    """
    
    # Default ETH price in USD (fallback when dynamic pricing unavailable)
    DEFAULT_ETH_PRICE_USD = 3000.0
    
    def __init__(
        self,
        eth_price_usd: float | None = None,
        price_cache: dict[str, float] | None = None,
    ) -> None:
        """Initialize profit calculator.
        
        Args:
            eth_price_usd: Current ETH price in USD (uses default if None)
            price_cache: Optional cache of token prices by symbol (lowercase)
        """
        self.eth_price_usd = eth_price_usd or self.DEFAULT_ETH_PRICE_USD
        self.price_cache = price_cache or {}
    
    def normalize_token_amount(self, amount: float, decimals: int) -> float:
        """Normalize raw token amount to human-readable value.
        
        Args:
            amount: Raw token amount (e.g., 1_000_000 for 1 USDC with 6 decimals)
            decimals: Number of decimal places
            
        Returns:
            Normalized amount (e.g., 1.0 for 1 USDC)
        """
        if decimals < 0:
            return amount
        return amount / (10 ** decimals)
    
    def get_token_price(self, token_spec: TokenSpec) -> float:
        """Get token price in USD.
        
        Args:
            token_spec: Token specification
            
        Returns:
            Token price in USD (0.0 if unavailable)
        """
        # Check cache first
        symbol_lower = token_spec.symbol.lower()
        if symbol_lower in self.price_cache:
            return self.price_cache[symbol_lower]
        
        # Fall back to token spec price
        return token_spec.price_usd or 0.0
    
    def compute_eth_equiv(
        self,
        amount: float,
        token_spec: TokenSpec,
    ) -> float:
        """Convert token amount to ETH equivalent.
        
        Args:
            amount: Normalized token amount
            token_spec: Token specification
            
        Returns:
            ETH equivalent value
        """
        if token_spec.eth_equiv_multiplier:
            numerator = token_spec.eth_equiv_multiplier.get("numerator", 1)
            denominator = token_spec.eth_equiv_multiplier.get("denominator", 1) or 1
            return (amount * numerator) / denominator
        
        # Fall back to price-based conversion
        token_price = self.get_token_price(token_spec)
        if token_price > 0 and self.eth_price_usd > 0:
            return (amount * token_price) / self.eth_price_usd
        
        return 0.0
    
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
            
            symbol_lower = symbol.lower()
            if symbol_lower not in token_lookup:
                continue
            
            token_spec = token_lookup[symbol_lower]
            
            # Normalize amount
            normalized = self.normalize_token_amount(amount, token_spec.decimals)
            
            # Compute ETH equivalent
            eth_equiv = self.compute_eth_equiv(normalized, token_spec)
            eth_equiv_total += eth_equiv
            
            # Compute USD value
            usd_value = self.compute_usd_value(normalized, token_spec)
            total_usd += usd_value
            
            # Store breakdown by address or symbol
            key = token_spec.address or symbol
            breakdown_usd[key] = usd_value
        
        return (eth_equiv_total, breakdown_usd, total_usd)
    
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

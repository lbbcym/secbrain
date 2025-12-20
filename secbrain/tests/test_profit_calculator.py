"""Tests for unified profit calculator."""

import pytest

from secbrain.core.profit_calculator import ProfitCalculator, TokenSpec


class TestTokenSpec:
    """Test TokenSpec dataclass validation."""
    
    def test_valid_token_spec(self):
        """Test creating valid TokenSpec."""
        spec = TokenSpec(
            symbol="USDC",
            address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            decimals=6,
            price_usd=1.0,
        )
        assert spec.symbol == "USDC"
        assert spec.decimals == 6
        assert spec.price_usd == 1.0
    
    def test_token_spec_empty_symbol_raises(self):
        """Test that empty symbol raises ValueError."""
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            TokenSpec(symbol="", address="0xabc", decimals=18)
    
    def test_token_spec_empty_address_raises(self):
        """Test that empty address raises ValueError."""
        with pytest.raises(ValueError, match="address cannot be empty"):
            TokenSpec(symbol="TEST", address="", decimals=18)
    
    def test_token_spec_negative_decimals_raises(self):
        """Test that negative decimals raises ValueError."""
        with pytest.raises(ValueError, match="decimals must be non-negative"):
            TokenSpec(symbol="TEST", address="0xabc", decimals=-1)
    
    def test_token_spec_negative_price_raises(self):
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="price_usd must be non-negative"):
            TokenSpec(symbol="TEST", address="0xabc", decimals=18, price_usd=-10.0)
    
    def test_token_spec_from_dict(self):
        """Test creating TokenSpec from dictionary."""
        data = {
            "symbol": "WETH",
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "decimals": 18,
            "price_usd": 3000.0,
        }
        spec = TokenSpec.from_dict(data)
        assert spec.symbol == "WETH"
        assert spec.decimals == 18
        assert spec.price_usd == 3000.0


class TestProfitCalculator:
    """Test ProfitCalculator class."""
    
    def test_normalize_token_amount(self):
        """Test token amount normalization."""
        calc = ProfitCalculator()
        
        # USDC with 6 decimals
        assert calc.normalize_token_amount(1_000_000, 6) == 1.0
        
        # WETH with 18 decimals
        assert calc.normalize_token_amount(1e18, 18) == 1.0
        
        # Negative decimals should return amount as-is
        assert calc.normalize_token_amount(100, -1) == 100
    
    def test_get_token_price_from_cache(self):
        """Test getting token price from cache."""
        price_cache = {"usdc": 1.0, "weth": 3000.0}
        calc = ProfitCalculator(price_cache=price_cache)
        
        usdc_spec = TokenSpec("USDC", "0xabc", 6, price_usd=0.99)
        
        # Should use cache value, not spec price
        assert calc.get_token_price(usdc_spec) == 1.0
    
    def test_get_token_price_from_spec(self):
        """Test getting token price from spec when not in cache."""
        calc = ProfitCalculator()
        
        usdc_spec = TokenSpec("USDC", "0xabc", 6, price_usd=1.0)
        assert calc.get_token_price(usdc_spec) == 1.0
    
    def test_get_token_price_returns_zero_when_unavailable(self):
        """Test that price returns 0.0 when unavailable."""
        calc = ProfitCalculator()
        
        spec = TokenSpec("UNKNOWN", "0xabc", 18)
        assert calc.get_token_price(spec) == 0.0
    
    def test_compute_eth_equiv_with_multiplier(self):
        """Test ETH equivalent calculation with multiplier."""
        calc = ProfitCalculator()
        
        spec = TokenSpec(
            "USDC",
            "0xabc",
            6,
            eth_equiv_multiplier={"numerator": 1, "denominator": 3000},
        )
        
        # 3000 USDC should equal 1 ETH
        eth_equiv = calc.compute_eth_equiv(3000.0, spec)
        assert eth_equiv == pytest.approx(1.0)
    
    def test_compute_eth_equiv_with_price(self):
        """Test ETH equivalent calculation using prices."""
        calc = ProfitCalculator(eth_price_usd=3000.0)
        
        spec = TokenSpec("USDC", "0xabc", 6, price_usd=1.0)
        
        # 3000 USDC at $1 each = 1 ETH at $3000
        eth_equiv = calc.compute_eth_equiv(3000.0, spec)
        assert eth_equiv == pytest.approx(1.0)
    
    def test_compute_usd_value(self):
        """Test USD value calculation."""
        calc = ProfitCalculator()
        
        spec = TokenSpec("USDC", "0xabc", 6, price_usd=1.0)
        usd_value = calc.compute_usd_value(100.0, spec)
        assert usd_value == 100.0
    
    def test_calculate_profit_from_tokens(self):
        """Test profit calculation from token dictionary."""
        calc = ProfitCalculator(eth_price_usd=3000.0)
        
        profit_tokens = {
            "USDC": 1_000_000,  # 1 USDC with 6 decimals
            "WETH": 10 * 10**18,  # 10 WETH
        }
        
        token_specs = [
            TokenSpec("USDC", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6, price_usd=1.0),
            TokenSpec("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18, price_usd=3000.0),
        ]
        
        eth_equiv, breakdown, total_usd = calc.calculate_profit_from_tokens(
            profit_tokens, token_specs
        )
        
        # 1 USDC = ~0.00033 ETH, 10 WETH = 10 ETH
        assert eth_equiv == pytest.approx(10.00033, rel=1e-3)
        
        # Total USD: 1 + 30000 = 30001
        assert total_usd == pytest.approx(30001.0)
        
        # Breakdown should have entries for both tokens
        assert len(breakdown) == 2
    
    def test_calculate_profit_from_tokens_handles_missing_tokens(self):
        """Test that missing tokens are ignored."""
        calc = ProfitCalculator()
        
        profit_tokens = {"UNKNOWN": 123}
        token_specs = []
        
        eth_equiv, breakdown, total_usd = calc.calculate_profit_from_tokens(
            profit_tokens, token_specs
        )
        
        assert eth_equiv == 0.0
        assert breakdown == {}
        assert total_usd == 0.0
    
    def test_calculate_profit_from_tokens_handles_invalid_input(self):
        """Test that invalid input returns zeros."""
        calc = ProfitCalculator()
        
        # Not a dict
        eth_equiv, breakdown, total_usd = calc.calculate_profit_from_tokens(
            "invalid", []  # type: ignore
        )
        
        assert eth_equiv == 0.0
        assert breakdown == {}
        assert total_usd == 0.0
    
    def test_calculate_profit_usd_from_list(self):
        """Test profit calculation from list format."""
        calc = ProfitCalculator()
        
        profit_tokens = [
            {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "amount": 1_000_000}
        ]
        
        token_specs = [
            TokenSpec("USDC", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6, price_usd=1.0)
        ]
        
        result = calc.calculate_profit_usd_from_list(profit_tokens, token_specs)
        
        assert result is not None
        assert result["total_usd"] == pytest.approx(1.0)
        assert len(result["breakdown"]) == 1
    
    def test_calculate_profit_usd_from_list_empty_returns_none(self):
        """Test that empty list returns None."""
        calc = ProfitCalculator()
        
        result = calc.calculate_profit_usd_from_list([], [])
        assert result is None
    
    def test_estimate_gas_cost(self):
        """Test gas cost estimation."""
        calc = ProfitCalculator(eth_price_usd=3000.0)
        
        # 100k gas at 50 gwei
        gas_cost_eth, gas_cost_usd = calc.estimate_gas_cost(100_000, 50e9)
        
        # 100k * 50e9 / 1e18 = 0.005 ETH
        assert gas_cost_eth == pytest.approx(0.005)
        
        # 0.005 ETH * 3000 = 15 USD
        assert gas_cost_usd == pytest.approx(15.0)
    
    def test_estimate_gas_cost_with_no_gas_used(self):
        """Test gas cost estimation with no gas used."""
        calc = ProfitCalculator()
        
        gas_cost_eth, gas_cost_usd = calc.estimate_gas_cost(None)
        assert gas_cost_eth == 0.0
        assert gas_cost_usd == 0.0
    
    def test_make_economic_decision_pursue(self):
        """Test economic decision to pursue."""
        calc = ProfitCalculator()
        
        decision = calc.make_economic_decision(
            max_profit_usd=500.0,
            gas_cost_usd=50.0,
            min_profit_threshold=300.0,
        )
        
        assert decision["decision"] == "PURSUE"
        assert decision["net_usd"] == 450.0
    
    def test_make_economic_decision_skip_high_gas(self):
        """Test economic decision to skip due to high gas."""
        calc = ProfitCalculator()
        
        decision = calc.make_economic_decision(
            max_profit_usd=100.0,
            gas_cost_usd=60.0,  # > 50% of profit
        )
        
        assert decision["decision"] == "SKIP"
        assert "Gas cost too high" in decision["reason"]
    
    def test_make_economic_decision_skip_negative(self):
        """Test economic decision to skip due to negative profit."""
        calc = ProfitCalculator()
        
        decision = calc.make_economic_decision(
            max_profit_usd=100.0,
            gas_cost_usd=150.0,
        )
        
        assert decision["decision"] == "SKIP"
        # Gas ratio > 0.5 triggers first, so reason is about gas cost
        assert "Gas cost too high" in decision["reason"] or "Negative or zero profit" in decision["reason"]
    
    def test_make_economic_decision_consider(self):
        """Test economic decision to consider marginal profit."""
        calc = ProfitCalculator()
        
        decision = calc.make_economic_decision(
            max_profit_usd=250.0,
            gas_cost_usd=50.0,
            min_profit_threshold=300.0,
        )
        
        assert decision["decision"] == "CONSIDER"
        assert "Marginal profit" in decision["reason"]


class TestProfitCalculatorIntegration:
    """Integration tests matching original test cases."""
    
    def test_compute_profit_eth_equiv_with_tokens(self):
        """Test matching original test_profit_equiv.py::test_compute_profit_eth_equiv_with_tokens."""
        calc = ProfitCalculator(eth_price_usd=3000.0)
        
        attempt = {
            "profit_tokens": {
                "USDC": 1_000_000,  # 1 USDC with 6 decimals
            }
        }
        
        token_specs = [
            TokenSpec(
                "USDC",
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                6,
                price_usd=1.0,
                eth_equiv_multiplier={"numerator": 1, "denominator": 1},
            )
        ]
        
        eth_equiv, breakdown, profit_usd = calc.calculate_profit_from_tokens(
            attempt.get("profit_tokens", {}), token_specs
        )
        
        assert eth_equiv == pytest.approx(1.0)
        assert breakdown == {"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": pytest.approx(1.0)}
        assert profit_usd == pytest.approx(1.0)
    
    def test_compute_profit_eth_equiv_handles_missing_tokens(self):
        """Test matching original test_profit_equiv.py::test_compute_profit_eth_equiv_handles_missing_tokens."""
        calc = ProfitCalculator()
        
        attempt = {"profit_tokens": {"UNKNOWN": 123}}
        
        eth_equiv, breakdown, profit_usd = calc.calculate_profit_from_tokens(
            attempt.get("profit_tokens", {}), []
        )
        
        assert eth_equiv == 0.0
        assert breakdown == {}
        assert profit_usd == 0.0
    
    def test_compute_profit_eth_equiv_uses_price_cache(self):
        """Test matching original test_profit_equiv.py::test_compute_profit_eth_equiv_uses_price_cache."""
        price_cache = {"weth": 2000.0}
        calc = ProfitCalculator(eth_price_usd=3000.0, price_cache=price_cache)
        
        attempt = {"profit_tokens": {"WETH": 10 * 10**18}}  # 10 WETH
        
        token_specs = [
            TokenSpec(
                "WETH",
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                18,
                eth_equiv_multiplier={"numerator": 1, "denominator": 1},
            )
        ]
        
        eth_equiv, breakdown, profit_usd = calc.calculate_profit_from_tokens(
            attempt.get("profit_tokens", {}), token_specs, 
        )
        
        assert eth_equiv == pytest.approx(10.0)
        assert profit_usd == pytest.approx(20000.0)  # 10 WETH * $2000 from cache

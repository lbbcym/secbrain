---
description: End-to-end implementation of claudereview.txt recommendations
---

# Workflow: Implement claudereview recommendations

1. Review summary
   - Read claudereview.txt and note critical blockers: missing asyncio import, oracle exploitation gaps, MEV/precision verification, token pricing/coverage, profit plumbing.

2. Fix runtime blockers first
   - [ ] Ensure vuln_hypothesis_agent.py imports asyncio.
   - [ ] Run pytest -q (or project test subset) to confirm no import errors.

3. Profit plumbing validation
   - [ ] Inspect secbrain/tools/foundry_runner.py to ensure profit_tokens, profit_breakdown, execution_trace/state propagate into FoundryRunResult.
   - [ ] If missing, add extraction of token logs/decoded logs and map into result.
   - [ ] Add/adjust parsing so zero-profit runs still return tokens when present.

4. Token coverage and pricing
   - [ ] Expand TOKEN_ADDRESSES_BY_CHAIN in exploit_agent.py with common tokens per chain (ETH: WETH, WBTC, UNI, LINK, etc.; BSC: BUSD, CAKE; Polygon: USDC, WMATIC, WETH).
   - [ ] Replace hardcoded ETH price with price feed helper (e.g., CoinGecko) with timeout + fallback to static prices.
   - [ ] Wire fetched prices into _compute_profit_eth_equiv; keep static fallback when API fails.

5. Oracle manipulation exploitation
   - [ ] Implement pool resolution helper in oracle_manipulation_detector.py (registry/factory lookup or config-driven mapping).
   - [ ] Extend generate_manipulation_exploit to produce executable flash-swap harness with callback, price check, and repayment using resolved pool/token.
   - [ ] Integrate exploitation path into exploit_agent: when oracle hypothesis present, ensure harness uses resolved pool/token and runs via FoundryRunner.

6. MEV/sandwich and precision verification
   - [ ] In vuln_hypothesis_agent._heuristic_enrich_hypotheses, add verification steps:
       - MEV: estimate slippage/price impact from ABI/pool hints; only emit hypothesis if slippage window exists; adjust confidence accordingly.
       - Precision: basic share math check (small/large amounts) or static detection of rounding branches; raise confidence when detected, lower/skip otherwise.
   - [ ] Add fuzz/boundary harness generator for precision exploits (deposit/withdraw) and integrate with FoundryRunner.

7. Tests and smoke
   - [ ] Add/adjust unit tests for price fetch fallback, profit parsing, heuristic gating.
   - [ ] Run pytest -q (or targeted suites) and a small SecBrain smoke run if available.

8. Documentation
   - [ ] Update docs/architecture*.md or ops.md with oracle exploitation flow, MEV/precision verification changes, pricing source/fallback, and new token coverage.

## Notes

- Use pwsh for commands. Avoid destructive operations. Keep changes minimal and incremental.

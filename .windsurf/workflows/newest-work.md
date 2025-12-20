---
description: Implement all claudereview.txt recommendations to completion
---

# Workflow: newest-work (Claude review completion)

## Prereqs

- Shell: pwsh. No destructive commands.
- Ensure tests can run (pytest, any Foundry harness). No `cd` in commands.
- Owners suggested: Python/agents (A), Foundry harness (B), Pricing/config (C).

## 1) Blockers first

1. Add `import asyncio` to `secbrain/agents/vuln_hypothesis_agent.py` if missing.
2. Ensure `exploit_agent.py` still has `_run_contract_hypothesis` helper (restore if absent).
3. Quick check: run targeted tests covering hypothesis/exploit phases (e.g., `pytest -q` subset).

## 2) Profit plumbing completion

1. Foundry runner:
   - Ensure `foundry_runner.py` returns `profit_tokens`, `profit_eth`, `execution_trace`, `state_changes`.
   - Parse token transfers/logs; normalize by decimals; keep zero-profit token data.
2. Exploit agent:
   - In `_compute_profit_eth_equiv`, normalize amounts by decimals; fill `profit_breakdown` and `profit_usd_estimate`.
   - Findings should include `profit_tokens`, `profit_breakdown`, `profit_usd_estimate`; triage uses these fields.
3. Token registry & pricing:
   - Expand `TOKEN_ADDRESSES_BY_CHAIN` (ETH: WETH, WBTC, UNI, LINK, stETH, wstETH, USDC/USDT/DAI; BSC: BUSD, CAKE, USDT/USDC; Polygon: USDC, WMATIC, WETH, etc.).
   - Replace hardcoded ETH price with pricing helper:
     - Option A: config-based static map.
     - Option B: external API (e.g., CoinGecko) with timeout/backoff and offline fallback.
   - Wire prices into profit computation; fallback to static when API fails.
4. Tests: add/adjust unit tests for `_match_token_price` and `_compute_profit_eth_equiv` with decimals/USD.

## 3) Oracle manipulation exploitation

1. Pool resolution: implement `_resolve_pool_address` (registry/config or factory lookup) in `oracle_manipulation_detector.py`.
2. Flashswap harness: make `generate_manipulation_exploit` emit executable code (no commented stubs) with callback, price check, repayment.
3. Price-dependent call: detect price-using function(s) and inject call into harness.
4. Integration: wire oracle hypotheses in `exploit_agent` to run this harness via FoundryRunner and capture profit tokens/USD.
5. Tests: unit test harness shape; optional mock/dry-run to ensure compilation succeeds.

## 4) MEV/sandwich + precision verification (reduce false positives)

1. MEV: add minimal verification (slippage/price impact estimation or simple sandwich sim) before emitting/raising confidence.
2. Precision: add PrecisionErrorDetector fuzz/boundary harness (deposit/withdraw small/large) and wire into exploit phase; raise confidence on detected rounding profit.
3. Integrate harnesses with FoundryRunner; record `profit_tokens` when profit observed.
4. Tests: unit tests for detector outputs; integration smoke on AMM-like/vault contract to ensure runs complete.

## 5) Data flow + parallelization sanity

1. Trace fields from foundry_runner → exploit_agent findings → triage_agent decisions; ensure no KeyError/None paths.
2. Reconfirm triage uses USD/token breakdown thresholds consistently.
3. Smoke run recon/hypothesis/exploit to confirm semaphores still improve timing (~1.7m target) and no deadlocks.

## 6) QA & regression

1. Unit tests: price fetch fallback, profit parsing, heuristic gating, oracle/precision harness outputs.
2. Integration: end-to-end smoke on sample targets (oracle, AMM, vault); verify findings include profit fields and no crashes.
3. RPC retry: simulate transient failure to ensure backoff path works.

## 7) Docs & config

1. Update docs/ops or architecture docs with: oracle exploitation flow, MEV/precision verification, pricing source/fallback, token coverage.
2. Document new config options (pricing source, API keys if any) and defaults; note offline fallback.

## 8) Rollout

1. Lint/format; ensure tests green.
2. Final SecBrain run; capture artifacts/logs showing profit tokens & USD.
3. Merge with notes on new configs and how to disable external pricing.

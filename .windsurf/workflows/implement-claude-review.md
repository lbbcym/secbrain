---
description: Implement all recommendations from claudereview.txt across hypothesis, exploit, recon, triage, and architecture
---

# Implement Claude Review Recommendations

## Prereqs

1. Ensure Python deps installable; add any new libs to `secbrain/pyproject.toml` (e.g., `jsonschema`, `eth_utils`, `tenacity`, `slither` if used).
2. Ensure Foundry toolchain available for harness changes.
3. Set shell to `pwsh` for commands.

## 1) Quick Wins (do first, ≤90 min)

1. **Hypothesis confidence filter:** In `secbrain/agents/vuln_hypothesis_agent.py`, add `CONFIDENCE_THRESHOLD=0.4`, filter ranked hypotheses before top-N, and log counts.
2. **JSON parse logging:** Log parse failures with contract, error, and response preview before correction prompt.
3. **Oracle detection logging:** After ABI extraction, log detected oracle functions and annotate classification.
4. **Recon timeout handling:** In `secbrain/agents/recon_agent.py`, add assets for `compilation_timeout` and `compilation_error` cases with metadata.
5. **Profit log surfacing:** In `secbrain/agents/exploit_agent.py`, append `profit_logs` and `token_transfers` derived from logs.

## 2) Hypothesis Agent Hardening

1. **JSON schema validation:** Add `HYPOTHESIS_SCHEMA` and validate parsed arrays (use `jsonschema`). Fail gracefully with logged errors.
2. **Checksum validation:** Normalize/validate `contract_address` via `eth_utils.is_address/to_checksum_address`; reject invalid.
3. **Retry bounds:** Keep single retry but ensure specific exception scopes (JSON vs validation).
4. **Parallel LLM calls:** Gate with semaphore (default 5) for contract hypotheses generation.

## 3) Exploit Profit Measurement (CRITICAL)

1. **Harness ERC20 tracking:** Extend Foundry harness (likely `foundry_runner.py` templates) to:
   - Accept `profitTokens` from scope.
   - Record initial and final balances for each token; log per-token profit.
2. **Attempt data model:** Ensure runner returns `profit_breakdown` `{token: amount}` plus ETH.
3. **Exploit agent aggregation:** In `_run_contract_hypothesis`, compute USD total via token symbol/price resolver; store `profit_breakdown` and `profit_usd_estimate/total`. Use USD-based threshold (ETH price fallback).
4. **Use `profit_tokens`:** Wire scope’s `profit_tokens` through to harness and exploit attempts.

## 4) Vulnerability Coverage Expansions

1. **Oracle manipulation:** Add detector (new module) to spot oracle ABI patterns and generate tailored exploit template; seed hypotheses with oracle-specific rationale.
2. **Flash loans:** Replace placeholder with actual flash loan/swap flow in harness templates when needed.
3. **MEV/Sandwich & precision bugs:** Add detectors/templates for sandwiching and rounding/precision checks; include in hypothesis patterns.
4. **Severity weights:** Update ranking severity map to DeFi-centric types (oracle, mev, rounding, access control, reentrancy).

## 5) Parallelization & Performance

1. **Recon parallel builds:** Semaphore-based parallel forge builds (default 5).
2. **Exploit parallelism:** Revisit `max_parallel` default (≥5) with semaphore; ensure backpressure is safe.
3. **LLM parallelism:** (From §2) already applied; confirm bounded.

## 6) Failure Handling & Resilience

1. **RPC retries/backoff:** Add `_run_exploit_with_retry` with timeout and exponential backoff; categorize failures.
2. **Circuit breaker/alternate RPCs:** Optional but recommended; manage multiple RPC URLs and open/close logic.
3. **Supervisor abort policy:** Decide whether phase failure should abort; if not, ensure downstream aware of missing data.

## 7) Findings & Data Flow Enrichment

1. **Findings structure:** Add `profit_breakdown`, `profit_usd_estimate`, `execution_trace`, `state_changes`, `root_cause`, `confidence_components`.
2. **Ranking filters:** Apply confidence threshold before ranking; adjust penalties/bonuses for missing contract/function.
3. **Triage alignment:** Ensure triage consumes new fields; keep hypothesis_id correlation.

## 8) Architectural Refactors

1. **Hypothesis dataclass:** Create `hypothesis.py` dataclass with validation/converters; migrate exploit agent to consume typed objects.
2. **Template registry:** Extract exploit templates into dedicated module; map `vuln_type` → template (incl. oracle/mev/precision).
3. **Modularize run() methods:** Split agent `run()` into testable substeps (parse, split, execute, aggregate, store).

## 9) Research-Level Enhancements (optional after above)

1. **Call graph analysis:** Integrate Slither call graph to detect cross-function issues; feed into hypotheses.
2. **Type-aware mutator:** Generate ABI-driven parameter mutations (boundary/extremes) and limit combinations.
3. **Iterative refinement loop:** Add supervisor method to iterate recon → hypothesis → exploit with failure feedback until success or max iterations.

## 10) Verification

1. Add/extend unit tests for:
   - Hypothesis schema/validation, checksum, filtering.
   - Recon timeout/exception asset creation.
   - Profit aggregation and threshold logic.
   - RPC retry/backoff behavior.
2. Add integration test (or dry-run) covering multi-token harness logging and oracle detection.
3. Run linters/formatters/tests; ensure new deps installed.

## 11) Rollout

1. Document changes in `docs/` (profit tracking, new vuln types, retry policy).
2. Update configs (`config/models.yaml`, `config/tools.yaml`) if new tools/models referenced.
3. Re-run SecBrain end-to-end on a known scope to validate reduced gaps.

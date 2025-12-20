---
description: Expand SecBrain exploit coverage to state-of-the-art across dynamic, static, evidence, and safety
---

# State-of-the-art vulnerability coverage rollout (Path A)

Goal: align SecBrain with the 2025 bug bounty meta (business logic + complex access control + blind SSRF) while raising overall coverage under SecBrain’s existing evidence-first and safety-first guarantees.

Single track: no shortcuts. Each phase includes design, implementation, tests, and docs; do not move forward until the phase’s quality bar is met.

## Non-negotiable quality bar

- Every new capability must emit verifiable, replayable evidence (EvidenceBundle + trace_id) and a deterministic repro artifact.
- False positives must be actively minimized with negative controls, baseline diffs, and per-class consensus thresholds.
- All high-risk/outbound tooling stays approval-gated via tool ACLs and is logged to `audit.jsonl`.
- Each phase must add tests (unit + integration harness) and docs updates before moving on.

## Phase 0 — Baseline + engineering guardrails

- Create feature branch `feat/sota-coverage`.
- Run the full test suite and capture a baseline: existing specialists/verifiers, current FP rate, and missing meta coverage.
- Confirm CI for tests/lint is enforced (add if missing).
- Freeze and document the current tool ACL surface (which tools are approval-required and why).

## Phase 1 — Meta-first foundations (required for 2025 classes)

- Add first-class identity/session abstractions (attacker vs victim contexts, cookie jar, auth headers, token storage, replay helpers).
- Add a stateful workflow runner for multi-step HTTP sequences and optional Playwright flows (with artifact capture).
- Add reusable response diff primitives (status/body/header/JSON semantic diff, size/entropy, keyword deltas) to support authz + logic verification.
- Add a controlled concurrency harness for race testing (bounded parallelism, idempotency checks, rate-limit aware execution).

## Phase 2 — Business Logic specialist (P0, highest ROI)

- Implement `BusinessLogicSpecialist` for workflow bypass, price/quantity manipulation, state forcing, and race conditions.
- Extend hypothesis generation to label likely logic endpoints (money, quantity, state transitions, coupons, transfers).
- Implement logic verifiers that confirm state changes via before/after evidence and invariant violations (not just error/keyword checks).
- Add deterministic repro exports (recorded request sequences) and triage severity heuristics.

## Phase 3 — Blind SSRF specialist + production-grade OOB (P1, “WAF killer”)

- Implement a real OOB client integration (interactsh/Burp collaborator/webhook-style) plus a dry-run simulator.
- Implement `BlindSSRFSpecialist` payload families: DNS exfil, redirects, IP obfuscations, auth-bypass URL forms, IPv6, and URL parser differentials.
- Implement OOB verification (canary creation, polling, correlation to trace_id) and capture hit metadata as evidence.
- Enforce ACL + scope rules for OOB and ensure all OOB actions remain approval-gated.

## Phase 4 — Auth & AuthZ bypass specialist (P2, OWASP #1)

- Implement multi-identity access-control testing (same endpoint with multiple sessions) and detect privilege escalation via robust diffing.
- Implement IDOR and object-level authz checks (identifier mutation, predictable IDs, object-type confusion) with evidence-backed verification.
- Implement safe JWT/header-based bypass probes with strict guardrails and verification (403→200 transitions, new sensitive fields, ownership markers).
- Add fixtures/mocks to validate verifier accuracy across allow/deny boundaries.

## Phase 5 — Expand technical vuln coverage to “SOTA breadth”

- Add/upgrade specialists + verifiers for: SSTI (multi-engine), XXE, RCE/command injection, deserialization, file upload, path traversal, NoSQLi, GraphQL abuse, and in-band SSRF.
- For each class, define: payload catalog, adaptation strategy, verifiers, consensus thresholds, and regression tests.

## Phase 6 — Static + hybrid intelligence

- Build semgrep rule packs per language focusing on SSRF/XXE/SSTI/RCE/IDOR; map static sinks/sources into dynamic hypotheses.
- Optionally add SBOM/dependency scanning to seed CVE-driven hypotheses under strict in-scope constraints.

## Phase 7 — Evidence, triage, reporting excellence

- Extend evidence to cover: browser artifacts (console/network/screenshot), OOB metadata, multi-step traces, and sanitized sensitive fields.
- Upgrade triage to correlate recon → hypothesis → exploit → static → evidence; dedupe and severity-rank with advisor only at checkpoints.
- Auto-generate submission-ready reports: CWE mapping, impact narrative, exact repro steps, minimal PoC scripts.

## Phase 8 — Rollout, evaluation, and hardening

- Run end-to-end dry runs against fixtures and test workspaces; measure FP/FN per class and iterate until thresholds are met.
- Run gated live runs with conservative rate limits and `--approval-mode ask`; validate audit trail completeness.
- Merge only after: all tests pass, docs updated, safety review complete, and new ACL defaults are conservative.

---
title: Phase 0 baseline and tool ACL freeze (sota-coverage rollout)
---

## Repository state

- Git branch creation blocked: workspace is **not a git repository** (`git checkout -b feat/sota-coverage` fails). Initialize git before branch creation to satisfy Phase 0.

## Test baseline

- `python -m pytest` (repo root) **fails** because `secbrain/examples/tools_smoke_test.py` lacks the `run_context` fixture expected by the tests (see pytest error for missing fixture).
- `cd secbrain && python -m pytest tests -q --disable-warnings --maxfail=1` **passes** (12 passed, 7 warnings). This is the current reliable automated test signal.

## Current tool ACL surface (from `config/tools.yaml`)

Approval audit log path: defaults to `<workspace>/audit.jsonl` via `ApprovalManager`.

| Tool          | Allowed | Allowed phases        | Require approval | Max calls/phase | Max calls/run |
| ------------- | ------- | --------------------- | ---------------- | --------------- | ------------- |
| http_client   | true    | all                   | false            | 50              | 200           |
| oob_client    | true    | exploit               | **true**         | 5               | 10            |
| playwright    | true    | recon, exploit, triage| **true**         | 3               | 6             |
| subfinder     | true    | recon                 | false            | 5               | 10            |
| amass         | true    | recon                 | false            | 3               | 5             |
| httpx         | true    | recon                 | false            | 5               | 10            |
| ffuf          | true    | recon, exploit        | **true**         | 2               | 4             |
| nmap          | true    | recon                 | false            | 2               | 4             |
| nuclei        | true    | exploit, triage       | **true**         | 2               | 4             |

Rate limits:

- `http_client`: 20 rpm, burst 5
- `subfinder`: 1 rpm, burst 1
- `amass`: 0.5 rpm, burst 1
- `oob_client`: 2 rpm, burst 1
- `playwright`: 2 rpm, burst 1
- `nuclei`: 1 rpm, burst 1
- Global: 60 rpm, burst 10 (defaults in `ToolsConfig`)

## Next required actions to close Phase 0

1. Initialize git and create `feat/sota-coverage` branch.
2. Decide how to handle `examples/tools_smoke_test.py` (add fixture or exclude from CI) so root `python -m pytest` is green.
3. Keep CI enforcing tests/lint (current GitHub workflow runs `secbrain/tests` only; adjust if you want root pytest).

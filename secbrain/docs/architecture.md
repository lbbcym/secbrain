# SecBrain Architecture

## Overview

SecBrain is a multi-agent security bounty system designed to automate vulnerability research while maintaining strict safety controls and evidence-based findings. It combines:

- **Multi-agent orchestration** for specialized tasks (recon, hypothesis, exploit, triage, reporting)
- **Verification-first evidence collection** via multi-method exploit verification
- **Human-in-the-loop approvals** with explicit audit trails
- **Advisor model** (Gemini) for critical decision checkpoints
- **Guarded tooling** with ACLs, rate limits, and kill-switch
- **Research integration** (Perplexity) for context and learning

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│                    (secbrain_cli.py)                            │
│              Flags: --approval-mode, --dry-run, etc.            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                          │
│                   (bug_bounty_run.py)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Supervisor Agent                       │   │
│  │  - Phase orchestration (Recon → Hypothesis → Exploit)     │   │
│  │  - ACL/rate limit enforcement                            │   │
│  │  - Kill-switch monitoring                                │   │
│  │  - Human approval checkpoints                            │   │
│  │  - Audit trail logging (audit.jsonl)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Agent Layer                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Program   │ │  Planner   │ │   Recon    │ │   Vuln     │   │
│  │  Ingest    │ │   Agent    │ │   Agent    │ │ Hypothesis │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Exploit   │ │  Static    │ │  Triage    │ │ Reporting  │   │
│  │   Agent    │ │  Analysis  │ │   Agent    │ │   Agent    │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐                                                 │
│  │   Meta     │                                                 │
│  │ Learning   │                                                 │
│  └────────────┘                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Verification & Evidence Layer                   │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ VerificationResult │  │  EvidenceBundle    │                │
│  │ (verified, conf)   │  │ (fingerprint, hash │                │
│  └────────────────────┘  │  baseline vs test) │                │
│  ┌────────────────────┐  └────────────────────┘                │
│  │    Verifiers       │  (ReflectedXSS, SQLError, Naive)        │
│  └────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Models & Approval Layer                            │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │   Worker Models    │  │ ApprovalManager    │                │
│  │  (Qwen/DeepSeek)   │  │  (ask/auto/deny)   │                │
│  └────────────────────┘  └────────────────────┘                │
│  ┌────────────────────┐                                        │
│  │   Advisor Model    │  (Gemini, critical checkpoints)         │
│  │   (Gemini)         │                                        │
│  └────────────────────┘                                        │
│  ┌────────────────────┐                                        │
│  │ Research (Perplex) │                                        │
│  └────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Tools Layer                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │    HTTP    │ │   Recon    │ │  Scanners  │ │  Storage   │   │
│  │   Client   │ │   CLIs     │ │ (nuclei)   │ │  (SQLite)  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│              All subject to ACLs, rate limits                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Core Layer                                │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │    RunContext      │  │     Logging        │                │
│  │    (Session)       │  │     (JSONL)        │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

## Current Implementation Status

### Already Implemented

#### Verification-First Evidence System

- `secbrain/core/verification.py`: Defines response fingerprinting and structured evidence (`EvidenceBundle`, `VerificationResult`)
- `secbrain/agents/verifiers.py`: Multi-method verifiers (e.g., reflected XSS, SQLi error)
- `secbrain/agents/exploit_agent.py`: Collects baseline response, executes test requests, calls verifiers, and emits findings with `verified`, `confidence_score`, and evidence

#### Human-in-the-Loop Approvals + Audit Trail

- `secbrain/core/approval.py`: `ApprovalManager` with modes `deny` (safe default), `ask` (interactive), `auto` (trusted)
- CLI flag: `--approval-mode deny|ask|auto`
- Audit log: `<workspace>/audit.jsonl`
- Enforcement:
  - `secbrain/tools/http_client.py`
  - `secbrain/tools/recon_cli_wrappers.py`

#### Specialist Routing (completed)
- `secbrain/agents/exploit_specialists.py`: router + XSS/SQLi/IDOR/Generic specialists
- `ExploitAgent` delegates to specialists for payload generation and verification

#### ReAct Reasoning Chains (completed)
- `BaseAgent` now records `reasoning_chain` and emits it in `AgentResult`
- Hooks available for agents to append THINK/JUSTIFY/ACT/REFLECT steps

#### Payload Adaptation (completed)
- `secbrain/core/payload_adaptation.py`: WAF/encoding/timing-aware mutation of payloads with retries in specialists

#### Consensus Verification (completed)
- `secbrain/core/consensus_engine.py`: aggregates verifier outputs into a single confidence/verified decision

### Remaining Work

- None for the 9/10 target; next improvements are opportunistic.

## Roadmap

All items for the 9/10 milestone are completed. Future enhancements (optional):
- Broader specialist coverage (RCE/SSRF/XXE/logic)
- Richer reasoning-chain storage (persist to DB with trace IDs)
- Adaptive rate-limit tuning and sandboxed executors
## Agents

### Supervisor Agent

- Orchestrates the overall workflow
- Enforces scope, ACLs, rate limits
- Monitors kill-switch
- Gates human approval for sensitive actions

### Program Ingest Agent

- Parses scope.yaml and program.json
- Normalizes rules and constraints
- Calls Perplexity for related writeups

### Planner Agent

- Creates phased execution plan
- Uses worker model + Perplexity research
- Gets Gemini advisor review

### Recon Agent

- Runs recon tools (subfinder, amass, httpx)
- Builds endpoint/asset map
- Research substep for stack/vuln class info

### Vuln Hypothesis Agent

- Generates vulnerability hypotheses per asset
- Research substep + advisor review

### Exploit Agent

- Designs and executes payloads
- Uses HTTP client and scanners
- High-risk actions require human approval
- Delegates to specialists (router) with payload adaptation, consensus verification, and reasoning-chain hooks

### Static Analysis Agent

- Integrates semgrep/scanners
- Analyzes source code when available

### Triage Agent

- Clusters anomalies
- Correlates dynamic + static findings
- Uses advisor for severity classification

### Reporting Agent

- Drafts PoCs and reports
- Attaches CWEs/CVEs via research
- Advisor review for submission readiness

### Browser & OOB Harnesses

- Playwright harness (headless by default) for DOM/flow verification, screenshots, console logs
- OOB client stub (interactsh-style) to generate canary URLs/DNS for SSRF and blind classes; dry-run simulates interactions

### Meta-Learning Agent

- Reviews logs post-run
- Learns from public writeups
- Suggests improvements (never auto-applies)

## Models

| Role | Model | Purpose |
|------|-------|---------|
| Worker | Qwen/DeepSeek | Bulk reasoning, cheap calls |
| Advisor | Gemini | Critical checkpoints, plan review |
| Research | Perplexity | External knowledge, writeups |

## Tools & Safety Controls

All tTools & Safety Controls

- **ACLs**: Scope-based access control
- **Rate limits**: Per-phase and global caps
- **Kill-switch**: Immediate halt capability
- **Logging**: Every action recorded

In addition, tools can be configured as **approval-required** via `config/tools.yaml`.

Safety controls:

1. **Scope Enforcement**: All actions validated against scope.yaml
2. **Rate Limits**: Configurable per tool and phase
3. **Human-in-the-Loop Approvals**: Approval gating via `RunContext.approval_manager`
4. **Kill-Switch**: External file or internal flag
5. **Dry-Run Mode**: Test without real network calls

Approval behavior is controlled by the CLI:

```text
--approval-mode deny|ask|auto
```

- **deny**: block approval-required actions (safe default)
- **ask**: prompt the operator in the terminal
- **auto**: automatically approve approval-required actions

All approval requests/responses are appended to:

```text
<workspace>/audit.jsonl
```

Verification-first exploit confirmation:

- `secbrain/core/verification.py`: evidence types (`EvidenceBundle`, `VerificationResult`, response fingerprinting)
- `secbrain/agents/verifiers.py`: exploit verifiers (e.g., reflected XSS, SQLi error)
- `secbrain/tools/oob_client.py`: OOB canary stub
- `secbrain/tools/playwright_client.py`: browser harness stub for DOM/flows

## Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| False Positive Rate | ~10-20% | <5% (with consensus) |
| Success Rate (real targets) | Baseline | +30-40% (specialists + adaptation) |
| Exploitability Proof | Evidence-backed | Evidence + reasoning chains |
| Enterprise Audit Trail | audit.jsonl | audit.jsonl + reasoning chains in DB |

## Key Files

- Orchestration: `secbrain/workflows/bug_bounty_run.py`, `secbrain/cli/secbrain_cli.py`
- Verification: `secbrain/core/verification.py`, `secbrain/agents/verifiers.py`
- Approvals: `secbrain/core/approval.py`
- Exploit: `secbrain/agents/exploit_agent.py`
- Tools: `secbrain/tools/http_client.py`, `secbrain/tools/recon_cli_wrappers.py`
- Core: `secbrain/core/context.py`, `secbrain/core/logging.py`
- Tests: `tests/test_verifiers.py`, `tests/test_approval_flow.py`

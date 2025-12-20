# SecBrain Workflows

## Overview

SecBrain supports multiple run modes depending on the task at hand. Each mode orchestrates a subset of agents through specific phases.

## Full Bounty Run

The default workflow for a complete bug bounty engagement.

```
secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo
```

### Phases

1. **Ingest** - Parse program and scope, normalize rules
2. **Plan** - Generate phased attack plan with advisor review
3. **Recon** - Asset discovery, endpoint mapping
4. **Hypothesis** - Generate vulnerability hypotheses
5. **Exploit** - Test hypotheses with payloads
6. **Triage** - Cluster and prioritize findings
7. **Report** - Draft PoCs and submission-ready reports

### Flow Diagram

```
Ingest → Plan → Recon → Hypothesis → Exploit → Triage → Report
                  ↑                      │
                  └──────────────────────┘
                    (iterate on findings)
```

### Forked exploit parameters (optional)

- `--rpc-url` RPC for mainnet/testnet fork
- `--block-number` Fork block for reproducibility
- `--chain-id` Chain ID for forked execution
- `--exploit-iterations` Attempts per hypothesis (default 3)
- `--profit-threshold` Early-stop profit target in ETH (default 0.1)

Behavioral notes:
- Recon extracts ABI and function signatures from Foundry build artifacts and attaches to contract assets for hypothesis generation.
- Exploit injects LLM-generated attack bodies into a templated `Exploit.t.sol` and runs iterative forge tests; stops once `profit_threshold` is hit.
- Triage applies economic gating; findings are marked `ready_for_report` only when the decision is `PURSUE`.
- Meta metrics (hypotheses_count, attempts_with_profit, economic decisions) append to `workspace/meta_metrics.jsonl`.

Validation notes:
- Contract-only scopes are supported: contract assets from Recon will produce hypotheses and drive the exploit loop.
- Phase artifacts are written to `workspace/phases/{recon,hypothesis,exploit,triage}.json` for inspection.

## Recon-Only Mode

Quick asset discovery without exploitation.

```
secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo --phases recon
```

### Output
- Asset inventory
- Endpoint map
- Technology stack analysis
- Initial vulnerability surface assessment

## Triage-Only Mode

Analyze existing findings without new testing.

```
secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo --phases triage,report
```

### Prerequisites
- Previous run data in workspace
- Findings to analyze

### Output
- Prioritized findings
- Severity classifications
- Draft reports

## Dry-Run Mode

Simulate the full workflow without real network calls.

```
secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo --dry-run
```

### Use Cases
- Validate configuration
- Test agent orchestration
- Verify logging setup
- Training and demos

## Custom Phase Selection

Run specific phases only.

```
secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo --phases recon,hypothesis
```

### Available Phases
- `ingest`
- `plan`
- `recon`
- `hypothesis`
- `exploit`
- `static`
- `triage`
- `report`

## Kill-Switch Integration

Enable external stop signal monitoring.

```
secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo --kill-switch-file ./stop.flag
```

When the kill-switch file is created, the run halts immediately after completing the current atomic operation.

## Human Approval Checkpoints

Certain actions require explicit human approval:

1. **Exploit execution** - Any payload that modifies target state
2. **Authentication attempts** - Login/credential testing
3. **Scope edge cases** - Actions near scope boundaries
4. **High-risk tools** - Nuclei templates marked as dangerous

The CLI will prompt for approval at these checkpoints. In automated environments, pre-approve via configuration or skip with `--auto-approve` (use with caution).

## Post-Run Analysis

After any run, the meta-learning agent can analyze outcomes:

```
secbrain analyze --workspace ./targets/foo
```

This generates:
- Run statistics
- Success/failure patterns
- Suggested improvements
- Learning from public writeups

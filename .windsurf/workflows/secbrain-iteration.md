# Goal

Drive `/secbrain-build` in a controlled, phased way with explicit checkpoints for each step of the build workflow:

1. Bootstrap Project Skeleton  
2. Core Context & Logging  
3. Model & Research Abstraction Layer  
4. Tooling Layer (Recon / HTTP / Storage)  
5. Agent Layer (Core Agents)  
6. Orchestration / Workflow Logic  
7. CLI Interface  
8. Logging, Threat Model & Ops Docs  
9. Dummy Target & Sanity Check  
10. Summarize & TODOs

Each phase has clear entry → work → checkpoint → exit criteria.

---

## Phase 1 – Bootstrap Project Skeleton  (aligns with build Step 1)

### Goal

Have a basic `secbrain/` project skeleton with `pyproject.toml`, `cli/`, `docs/`, and a minimal `README.md`.

### Steps

1. Ensure git working tree is clean.  
2. In Cascade, run `/secbrain-build` but instruct:

   > “Only execute Step 1 (Bootstrap Project Skeleton). Do not touch core, models, tools, agents, or workflows yet.”

3. Let Windsurf:
   - Create `secbrain/` directory (if needed).
   - Add `pyproject.toml` (using `uv` or `poetry`, with reasoning).
   - Create `secbrain/__init__.py`.
   - Create `cli/secbrain_cli.py` (can be stub).
   - Create `docs/architecture.md`, `docs/workflows.md`, `docs/threat_model.md`, `docs/ops.md`.
   - Create a minimal `README.md` with:
     - Purpose.
     - Multi-agent / research-first / guarded features.
     - High-level architecture.
     - Very basic install & run instructions.

### Checkpoint

- Confirm the structure matches build Step 1 exactly.
- README + docs exist and roughly describe the intended system.

### Exit Criteria

- Skeleton is present, no extra logic yet.
- Commit:

  ```bash
  git commit -am "secbrain: bootstrap project skeleton"
  ```

---

## Phase 2 – Core Context & Logging  (aligns with build Step 2)

### Goal

Define `RunContext` / `Session` and structured logging under `secbrain/core/`.

### Steps

1. In Cascade, run `/secbrain-build` and instruct:

   > “Only execute Step 2 (Core Context & Logging). Do not modify models, tools, agents, or workflows.”

2. Let Windsurf add/modify:

   - `secbrain/core/context.py`:
     - `RunContext` / `Session` including:
       - Program scope info.
       - Workspace paths.
       - Model clients (worker + advisor).
       - Tool registry / ACLs / rate limits.
       - Kill-switch flag + helpers.
   - `secbrain/core/logging.py`:
     - Structured logging (e.g. JSONL).
     - Helpers to log `run_id, agent, phase, action, models, tools, result`.
   - Logging location: `workspace/logs/run-<timestamp>.jsonl`.

### Checkpoint

- `RunContext` has all fields required by later steps (models, tools, ACLs, kill-switch).  
- Logging writes to workspace logs in a structured way.

### Exit Criteria

- Context + logging match build Step 2.
- Commit:

  ```bash
  git commit -am "secbrain: core RunContext and logging"
  ```

---

## Phase 3 – Model & Research Abstraction Layer  (aligns with build Step 3)

### Goal

Abstract worker models, Gemini advisor, and Perplexity research behind clean interfaces.

### Steps

1. In Cascade, run `/secbrain-build` and instruct:

   > “Only execute Step 3 (Model & Research Abstraction Layer). Do not modify tools, agents, orchestrator, or CLI.”

2. Let Windsurf create/modify:

   - `secbrain/models/base.py` – common interfaces for model calls.
   - `secbrain/models/open_workers.py` – wraps cheap/open models (Qwen/DeepSeek/Mixtral etc., stubs OK).
   - `secbrain/models/gemini_advisor.py` – Gemini Pro wrapper.
   - `secbrain/tools/perplexity_research.py`:
     - Env/config-based API key.
     - `ask_research(question, context, run_context)` with:
       - per-run caching.
       - phase-level usage/cost caps.
   - `secbrain/config/models.yaml` – which models are workers/advisors/etc.

### Checkpoint

- Interfaces exist and are simple, e.g.:

  - `call_worker_model(prompt, context, **kwargs)`  
  - `call_advisor_model(prompt, context, **kwargs)`

- `ask_research(...)`:
  - Implements caching and caps.
  - Logs queries and truncated answers.

- Quick import/smoke test from terminal.

### Exit Criteria

- Build Step 3 is fully implemented and stable.
- Commit:

  ```bash
  git commit -am "secbrain: model layer and Perplexity research abstraction"
  ```

---

## Phase 4 – Tooling Layer (Recon / HTTP / Storage)  (aligns with build Step 4)

### Goal

Safe-by-default wrappers for HTTP, recon tools, scanners, and storage with ACL + kill-switch.

### Steps

1. In Cascade, run `/secbrain-build` and instruct:

   > “Only execute Step 4 (Tooling Layer) and update `config/tools.yaml`. Do not touch agents or workflows yet.”

2. Ensure Windsurf implements under `secbrain/tools/`:

   - `http_client.py`:
     - Uses `RunContext` for host allowlists, method restrictions, rate limits, kill-switch.
     - Logs request/response metadata (no full bodies by default).

   - `recon_cli_wrappers.py`:
     - Subprocess wrappers for `subfinder`, `amass`, `httpx`, `ffuf`, etc.
     - Config-driven paths/args.
     - Respect ACLs / rate limits / kill-switch.

   - `scanners.py`:
     - Abstractions for `nuclei`, `semgrep` etc.

   - `storage.py`:
     - Workspace store (JSON/SQLite) for recon results, hypotheses, findings.

   - `secbrain/config/tools.yaml`:
     - Allowed tools per program.
     - Rate limits and safety thresholds.

3. Add `examples/tools_smoke_test.py` that:
   - Builds a dummy `RunContext`.
   - Calls HTTP + recon wrappers in “dry mode” (localhost/echo/print-only).

4. Run smoke test from Windsurf terminal and fix issues.

### Exit Criteria

- Tools match build Step 4, safe-neutral by default.
- Commit:

  ```bash
  git commit -am "secbrain: tooling layer with ACLs and kill-switch"
  ```

---

## Phase 5 – Agent Layer (Core Agents)  (aligns with build Step 5)

### Goal

Implement all core agents as thin orchestrators using models, tools, and research.

### Steps

1. In Cascade, call `/secbrain-build` with:

   > “Execute Step 5 (Agent Layer) but only scaffold the files; then we’ll refine agents one-by-one.”

   This should create skeletons for:

   - `secbrain/agents/supervisor.py`
   - `program_ingest_agent.py`
   - `planner_agent.py`
   - `recon_agent.py`
   - `vuln_hypothesis_agent.py`
   - `exploit_agent.py`
   - `static_analysis_agent.py`
   - `triage_agent.py`
   - `reporting_agent.py`
   - `meta_learning_agent.py`

2. Then, refine **one agent at a time** (using `/secbrain-agents` or similar) in this order:

   1. `supervisor.py`  
   2. `program_ingest_agent.py`  
   3. `planner_agent.py`  
   4. `recon_agent.py`  
   5. `vuln_hypothesis_agent.py`  
   6. `exploit_agent.py`  
   7. `triage_agent.py`  
   8. `reporting_agent.py`  
   9. `static_analysis_agent.py`  
   10. `meta_learning_agent.py`

   For each agent:

   - Ensure `run(run_context: RunContext, ...)` entry point.  
   - Use worker models by default.  
   - Call `perplexity_research` at defined substeps.  
   - Call Gemini advisor only at key checkpoints.  
   - Update `docs/architecture.md` with responsibilities, tools, research/advisor usage.

### Checkpoint

- Each agent:
  - Uses only abstractions (no raw HTTP/subprocess).
  - Has clear responsibilities aligned with build Step 5 descriptions.
- You commit after every 1–2 agents.

### Exit Criteria

- All agents from Step 5 are implemented at least to a functional skeleton with correct interfaces and docs.
- Multiple small commits, no giant refactors.

---

## Phase 6 – Orchestration / Workflow Logic  (aligns with build Step 6)

### Goal

Implement `bug_bounty_run` orchestration that wires phases and agents together.

### Steps

1. In Cascade, run `/secbrain-build` and instruct:

   > “Execute Step 6 (Orchestration / Workflow Logic) only.”

2. Implement `secbrain/workflows/bug_bounty_run.py` to:

   - Accept:
     - `scope` file path.
     - `program` file path.
     - `workspace` path.
   - Initialize `RunContext` (scope, config, models, tools).  
   - Build the phase graph:
     - `program_ingest` → `planner` → `recon` → `vuln_hypothesis` → `exploit` → `triage` → `reporting` → `meta_learning`.  
   - Add support for:
     - Branching when certain conditions are met (e.g., promising vuln).
     - Human approval prompts before “sensitive actions”.
   - Kill-switch check before external calls.
   - Log each transition and outcome.

### Checkpoint

- Code compiles; orchestrator calls each agent via `run(...)`.  
- Branching/approval/kill-switch hooks exist even if some logic is stubbed.

### Exit Criteria

- Build Step 6 is implemented and reachable from code.
- Commit:

  ```bash
  git commit -am "secbrain: bug_bounty_run orchestrator"
  ```

---

## Phase 7 – CLI Interface  (aligns with build Step 7)

### Goal

User-facing `secbrain run` CLI that drives `bug_bounty_run`.

### Steps

1. In Cascade, run `/secbrain-build` and instruct:

   > “Execute Step 7 (CLI Interface) only.”

2. Implement `cli/secbrain_cli.py` (using `typer` or `argparse`) with:

   - Command:

     ```bash
     secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo
     ```

   - Options:
     - `--dry-run` (no real HTTP/tools; log-only/mocks).
     - `--phases` (e.g. `recon,exploit,report`).
     - `--kill-switch-file` path (optional external stop signal).

   - Behavior:
     - Creates workspace directory if needed.
     - Writes `run_id` and logs under workspace.
     - Calls `bug_bounty_run.run(...)`.

**Checkpoint**:

- From terminal:

  ```bash
  python cli/secbrain_cli.py --help
  ```

  (or installed entrypoint) shows correct options.

**Exit Criteria**:

- CLI behavior matches build Step 7.
- Commit:

  ```bash
  git commit -am "secbrain: CLI interface for bug bounty run"
  ```

---

## Phase 8 – Logging, Threat Model & Ops Docs  (aligns with build Step 8)

**Goal**:
Docs reflect reality; threat model and ops guidance are in place.

**Steps**:

1. In Cascade, run a docs-focused workflow:

   > “Open `docs/architecture.md`, `docs/threat_model.md`, `docs/workflows.md`, `docs/ops.md` and update them to match the current code and build Steps 1–7.”

2. Ensure:

   - `architecture.md`:
     - Describes agents, models, tools, and their interactions.
   - `threat_model.md`:
     - Lists prompt-injection, tool misuse, data leakage between programs.
     - Documents controls: ACLs, rate limits, manual approvals, kill-switch, program isolation.
   - `workflows.md`:
     - Documents recon-only, full run, triage-only, etc.
   - `ops.md`:
     - Setup instructions, configs, env vars.
     - How to run tests and dry-runs.
     - How to safely add new tools.

3. Run a small logging smoke test (see Phase 9 dry-run) and verify logs are written as per Step 2.

**Checkpoint**:

- Docs are updated to reflect the current state of the project.

**Exit Criteria**:

- Build Step 8 is fully covered in docs and behavior.
- Commit:

  ```bash
  git commit -am "secbrain: logging, threat model, and ops docs"
  ```

---

## Phase 9 – Dummy Target & Sanity Check  (aligns with build Step 9)

**Goal**:
One full, safe end-to-end run using dummy target.

**Steps**:

1. Ensure `examples/dummy_target/` contains:

   - `scope.yaml`
   - `program.json`

   as described in build Step 9.

2. From Windsurf terminal, run:

   ```bash
   secbrain run \
     --scope examples/dummy_target/scope.yaml \
     --program examples/dummy_target/program.json \
     --workspace ./targets/dummy \
     --dry-run
   ```

3. Check:

   - Agents invoked in expected order.
   - No real network calls were made (dry-run honored).
   - Logs created under `./targets/dummy/logs/`.

4. (Optional) Small live test on a safe lab target under strict ACLs and manual approvals.

**Exit Criteria**:

- Build Step 9 passes in dry-run.
- Commit:

  ```bash
  git commit -am "secbrain: first end-to-end dry-run"
  ```

---

## Phase 10 – Summarize & TODOs  (aligns with build Step 10)

**Goal**:
Close the loop with explicit summary and roadmap.

**Steps**:

1. Update `README.md` or `docs/ops.md` with a **TODO / roadmap** section covering build Step 10:

   - Deeper LangGraph/AutoGen integration.
   - Additional tools (Burp extensions, browser automation).
   - Prompt/model tuning based on real usage.

2. Add a short summary of current capabilities and limitations.

**Exit Criteria**:

- Build Step 10 is reflected in docs.
- Final commit for this iteration:

  ```bash
  git commit -am "secbrain: summarize build status and TODOs"
  ```

---

## Usage

- Use `/secbrain-build` to do the **implementation** steps.  
- Use `/secbrain-iteration` (this workflow) to control **which build steps to run when**, and to enforce checkpoints and commits after each phase.

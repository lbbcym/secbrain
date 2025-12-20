# /secbrain-build

## Goal

Design and implement the “secbrain” bounty/security agent system as a CLI-first Python project, with:

- multi-agent architecture,
- research integration via Perplexity,
- advisor model via Gemini,
- tool ACLs + rate limits + kill-switch,
- strong logging and threat modeling.

## Steps

1. **Bootstrap Project Skeleton**
   - Create a new directory `secbrain/` (if it doesn’t exist).
   - Set up a modern Python project:
     - Add `pyproject.toml` using `uv` or `poetry` (summarize the choice).
     - Create the `secbrain/` package with `__init__.py`.
     - Add `cli/` folder with `secbrain_cli.py`.
     - Add `docs/` with initial `architecture.md`, `workflows.md`, `threat_model.md`, `ops.md`.
   - Add a minimal `README.md` summarizing:
     - Purpose and key features (multi-agent, research-first, guarded).
     - High-level architecture (agents + tools + models).
     - Basic install & run instructions.

2. **Core Context & Logging**
   - Under `secbrain/core/`:
     - Implement `context.py` defining `RunContext` / `Session`:
       - Program scope info.
       - Workspace paths.
       - Model clients (worker + advisor).
       - Tool registry / ACLs / rate limits.
       - Kill-switch flag and helpers.
     - Implement `logging.py`:
       - Configure structured logging (e.g., JSONL).
       - Helper functions to log events with: run_id, agent, phase, action, models, tools, result.
   - Ensure logs are written under `workspace/logs/run-<timestamp>.jsonl`.

3. **Model & Research Abstraction Layer**
   - Under `secbrain/models/`:
     - Implement `base.py` with common interfaces for model calls.
     - Implement `open_workers.py` to wrap cheap/open models (e.g., Qwen/DeepSeek/etc., even if stubbed at first).
     - Implement `gemini_advisor.py` wrapping Gemini calls.
   - Under `secbrain/tools/`:
     - Implement `perplexity_research.py` with:
       - Configurable API key via env/config.
       - `ask_research(question, context, run_context)` with:
         - caching per run.
         - a simple usage/cost cap mechanism (max calls per phase).
   - Add `config/models.yaml` to define which models are used for:
     - worker,
     - advisor,
     - any special modes (later).

4. **Tooling Layer (Recon / HTTP / Storage)**
   - Under `secbrain/tools/` implement:
     - `http_client.py` (requests/httpx wrapper):
       - Uses RunContext for:
         - scope enforcement (hosts, methods).
         - rate limits.
         - kill-switch check.
       - Logs every request/response metadata (not full bodies by default).
     - `recon_cli_wrappers.py`:
       - Functions to call `subfinder`, `amass`, `httpx`, `ffuf`, etc. via subprocess.
       - Use config-driven paths and arguments.
       - Respect ACL / rate limits / kill-switch.
     - `scanners.py`:
       - Abstractions for `nuclei`, `semgrep`, or other scanners.
     - `storage.py`:
       - Simple workspace store (JSON/SQLite) for:
         - recon results.
         - hypotheses.
         - findings.
   - Add `config/tools.yaml` describing:
     - Allowed tools and arguments per program.
     - Rate limits and safety thresholds.

5. **Agent Layer (Core Agents)**
   - Under `secbrain/agents/`, create and implement skeletons for:
     - `supervisor.py`:
       - Orchestrates phases.
       - Enforces scope, ACLs, rate limits, kill-switch, and human approval checkpoints.
     - `program_ingest_agent.py`:
       - Reads program/scope config.
       - Normalizes rules.
       - Calls research to fetch related writeups and constraints.
     - `planner_agent.py`:
       - Proposes a phased plan (recon → mapping → hypotheses → tests → triage → reporting).
       - Uses worker model + Perplexity.
       - Gets advisor (Gemini) review for the plan.
     - `recon_agent.py`:
       - Orchestrates recon tools, builds endpoint/asset map.
       - Research substep: given recon results, asks Perplexity about stack/vuln classes.
     - `vuln_hypothesis_agent.py`:
       - Generates vulnerability hypotheses per asset/endpoint.
       - Research substep and advisor review at the end.
     - `exploit_agent.py`:
       - Designs and executes payloads via HTTP/scanners.
       - Periodically uses research to discover new payload patterns.
       - Marks high-risk actions for human approval.
     - `static_analysis_agent.py` (optional at first but scaffold it):
       - Integrates scanners/semgrep or source when available.
     - `triage_agent.py`:
       - Clusters anomalies, correlates dynamic + static findings.
       - Uses advisor for high/medium/low classification.
     - `reporting_agent.py`:
       - Drafts PoCs and reports.
       - Research substep to attach CWEs/CVEs/best-practice references.
       - Advisor review for “ready to submit”.
     - `meta_learning_agent.py`:
       - Reviews logs and outcomes after runs.
       - Uses research to learn from public writeups.
       - Produces suggested changes (never applies them automatically).

   - Each agent should:
     - Expose `run(run_context, ...)`.
     - Use worker models by default.
     - Call advisor only at key checkpoints.
     - Call research via `perplexity_research` at defined sub-steps.

6. **Orchestration / Workflow Logic**
   - Implement `secbrain/workflows/bug_bounty_run.py`:
     - Accepts scope/program files and workspace path.
     - Initializes RunContext (scope, config, models, tools).
     - Builds the phase graph (sequence + possible branches).
     - Calls agents in order, with:
       - branching when certain conditions met (e.g., promising vuln).
       - human-approval checkpoints for sensitive actions.
       - kill-switch check before any external call.
     - Logs each transition and outcome.

7. **CLI Interface**
   - Implement `cli/secbrain_cli.py` using `typer` or `argparse` with commands:
     - `secbrain run --scope scope.yaml --program program.json --workspace ./targets/foo`
     - Options:
       - `--dry-run` (no real HTTP/tools).
       - `--phases recon,exploit,report` to restrict phases.
       - `--kill-switch-file path` to watch for an external stop signal.
   - Ensure the CLI:
     - Creates the workspace directory if needed.
     - Writes run_id and logs there.
     - Calls `bug_bounty_run.run(...)`.

8. **Logging, Threat Model & Ops Docs**
   - Flesh out `docs/architecture.md`:
     - Agent list, responsibilities, interactions.
     - Models and tools abstraction.
   - Fill `docs/threat_model.md`:
     - Prompt-injection risks (from target and tools).
     - Tool misuse / overreach risks.
     - Controls: ACLs, rate limits, manual approvals, kill-switch, program isolation.
   - Fill `docs/workflows.md`:
     - Common run modes (recon-only, full bounty run, triage-only).
   - Fill `docs/ops.md`:
     - How to set up configs.
     - How to run tests and dry-runs.
     - How to safely add new tools.

9. **Dummy Target & Sanity Check**
   - Add `examples/dummy_target/` with:
     - `scope.yaml` (simple fake target).
     - `program.json` (fake bounty description).
   - Implement a minimal “mock” HTTP target or local service for testing (could be a stub server or just log-only mode).
   - Run:
     - `secbrain run --scope examples/dummy_target/scope.yaml --program examples/dummy_target/program.json --workspace ./targets/dummy --dry-run`
   - Verify:
     - Logs created.
     - Agents invoked in order.
     - No real network calls in dry-run.

10. **Summarize & TODOs**

    - Summarize what was implemented and where stubs remain.
    - Add a TODO section to `README.md` or `docs/ops.md`:
      - Deeper integration with LangGraph/AutoGen.
      - Additional tools (Burp extensions, browser automation).
      - Fine-tuning prompts and model selection once real usage data exists.

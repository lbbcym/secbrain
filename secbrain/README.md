# SecBrain

**Multi-agent security bounty system with research integration, advisor models, and guarded tooling.**

## Overview

SecBrain is a CLI-first Python project that automates bug bounty workflows using a coordinated team of AI agents. It combines:

- **Multi-agent architecture**: Specialized agents for each phase (recon, hypothesis, exploit, triage, reporting)
- **Research-first approach**: Perplexity integration for external knowledge and learning
- **Advisor oversight**: Gemini model reviews critical decisions
- **Guarded execution**: ACLs, rate limits, kill-switch, and human approval checkpoints

## Key Features

- 🔍 **Automated recon** with subfinder, amass, httpx integration
- 🧠 **Vulnerability hypothesis generation** using AI reasoning
- 🔬 **Research-backed testing** with Perplexity for context
- ✅ **Advisor review** at critical checkpoints
- 🛡️ **Safety controls**: Scope enforcement, rate limits, kill-switch
- 📊 **Structured logging** in JSONL format
- 📝 **Report generation** with CWE/CVE references

## Architecture

```
CLI → Orchestrator → Agents → Models/Tools → Core Context
         ↓             ↓           ↓
    Supervisor    [Ingest,      [Worker,
                   Planner,      Advisor,
                   Recon,        Research]
                   Exploit,        +
                   Triage,      [HTTP,
                   Report]       Recon,
                                 Scanners]
```

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd secbrain

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

1. **Set up API keys**:
```bash
export PERPLEXITY_API_KEY=pplx-xxxx
export GOOGLE_API_KEY=AIza-xxxx
```

2. **Run a dry-run test**:
```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/test \
  --dry-run
```

3. **Run a real bounty workflow**:
```bash
secbrain run \
  --scope path/to/scope.yaml \
  --program path/to/program.json \
  --workspace ./targets/my-target \
  --rpc-url https://mainnet.infura.io/v3/<key> \
  --block-number 12345678 \
  --chain-id 1 \
  --exploit-iterations 3 \
  --profit-threshold 0.1
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `secbrain run` | Execute bounty workflow |
| `secbrain validate` | Validate configuration files |
| `secbrain version` | Show version |

### Run Options

| Option | Description |
|--------|-------------|
| `--scope` | Path to scope.yaml |
| `--program` | Path to program.json |
| `--workspace` | Output directory |
| `--dry-run` | Simulate without real calls |
| `--phases` | Comma-separated phase list |
| `--kill-switch-file` | External stop signal file |
| `--rpc-url` | RPC URL for forked exploit execution |
| `--block-number` | Block number to pin the fork |
| `--chain-id` | Chain ID for forked execution |
| `--exploit-iterations` | Attempts per hypothesis (default 3) |
| `--profit-threshold` | Stop iterating after profit (ETH) meets threshold (default 0.1) |

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [Workflows](docs/workflows.md) - Run modes and phases
- [Threat Model](docs/threat_model.md) - Security considerations
- [Operations](docs/ops.md) - Setup and usage guide

## Project Structure

```
secbrain/
├── secbrain/
│   ├── agents/        # Agent implementations
│   ├── cli/           # CLI interface
│   ├── core/          # Context, logging, types
│   ├── models/        # Model abstractions
│   ├── tools/         # Tool wrappers
│   └── workflows/     # Orchestration logic
├── config/            # Configuration files
├── docs/              # Documentation
├── examples/          # Example targets
└── tests/             # Test suite
```

## Instascope bundles (Immunefi)

- Layout per protocol: `targets/<protocol>/instascope/` (Instascope sources: `src/`, `foundry.toml`, `build.sh`, generated `out/`/`cache/`); `targets/<protocol>/workspace/` (SecBrain artifacts: `logs/`, `findings/`, `reports/`, `audit.jsonl`, scope/program files).
- Fetch/unpack: `python secbrain/scripts/fetch_instascope.py --protocol <name> --source <zip_or_tar>`; add `--build` to run `build.sh` after unpack; add `--force` to overwrite existing.
- Build: run `forge build` (or `./build.sh`) with cwd `targets/<protocol>/instascope/`. Requires Foundry/forge on PATH and a shell (bash/WSL on Windows).
- Gitignore: `out/`, `cache/`, `lib/` under `targets/**/instascope` are ignored by default.

## Safety Controls

1. **Scope Enforcement**: All actions validated against scope.yaml
2. **Rate Limits**: Configurable per-tool and global caps
3. **Kill-Switch**: External file or API signal for immediate halt
4. **Human Approval**: Required for high-risk actions
5. **Dry-Run Mode**: Full simulation without network calls

## Implementation Status

### Completed ✅

- **Core Layer**: RunContext, Session, structured JSONL logging
- **Model Layer**: Worker models (OpenAI-compatible, Ollama), Gemini advisor, Perplexity research
- **Tool Layer**: HTTP client, recon CLI wrappers (subfinder, amass, httpx, ffuf, nmap), scanners (nuclei, semgrep), SQLite storage
- **Agent Layer**: All 10 agents (supervisor, ingest, planner, recon, hypothesis, exploit, static, triage, reporting, meta-learning)
- **Orchestration**: Phase graph workflow with supervisor checks
- **CLI**: Typer-based interface with async support
- **Safety Controls**: ACLs, rate limits, kill-switch, scope enforcement
- **Documentation**: Architecture, workflows, threat model, operations guide
- **Examples**: Scope/program configs, dry-run and smoke tests

### Stubs / Needs Enhancement 🔧

- Worker model clients need real API integration testing
- Recon CLI wrappers assume tools are installed on PATH
- Scanner integrations need template configuration
- Research caching uses simple in-memory dict (consider Redis)
- Approval flow is auto-approve in dry-run only

## TODO

### High Priority

- [ ] Add unit tests for all agents and tools
- [ ] Implement real API key validation on startup
- [ ] Add retry logic with exponential backoff for API calls
- [ ] Create Docker container with pre-installed tools

### Medium Priority

- [ ] Deeper integration with LangGraph/AutoGen
- [ ] Browser automation tools (Playwright/Selenium)
- [ ] Burp Suite extension integration
- [ ] Fine-tuned prompts based on real usage data
- [ ] Multi-target orchestration
- [ ] Webhook notifications for findings

### Low Priority / Future

- [ ] Cloud deployment options (AWS Lambda, GCP Cloud Run)
- [ ] Web dashboard for monitoring runs
- [ ] Integration with bug bounty platforms (HackerOne, Bugcrowd APIs)
- [ ] Custom vulnerability template authoring
- [ ] Team collaboration features

## License

MIT

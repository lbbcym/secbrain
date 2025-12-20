# SECBRAIN OPTIMIZATION WORKFLOW
**Executable checklist for Windsurf to follow from code commit to production**

---

## QUICKSTART (Copy-Paste This)

```bash
# 1. Clone and setup
git clone <secbrain-repo>
cd SecBrain
git checkout -b feature/secbrain-optimization

# 2. Create workflow directory
mkdir -p .windsurf
cp WORKFLOW.md .windsurf/WORKFLOW_PROGRESS.md

# 3. Start Phase 0
# Follow instructions below
```

---

## MASTER WORKFLOW (7 PHASES, 11.25 HOURS)

### 🎯 PHASE 0: SETUP (30 minutes)
**Status**: ⏳ Starting
**Deadline**: 12:30 UTC
**Owner**: You

#### Tasks
```
□ Clone repo and verify clean state
□ Create .windsurf/ directory structure
□ Initialize IMPLEMENTATION_STATE.md
□ Create metrics baseline file
□ Create feature branch
□ Run existing test suite (baseline)
```

#### Commands
```bash
# Verify clean repo
git status
# Should show: working tree clean

# Setup .windsurf/
mkdir -p .windsurf
touch .windsurf/IMPLEMENTATION_STATE.md
touch .windsurf/METRICS_BEFORE.json

# Baseline metrics
python tests/test_exploit_agent.py 2>&1 | tee .windsurf/BASELINE_TEST.log

# Create branch
git checkout -b feature/secbrain-optimization
```

#### Success Criteria
```
✅ git status shows clean working tree
✅ .windsurf/ directory exists with all files
✅ Previous tests pass (baseline established)
✅ Branch created and checked out
```

#### Next: → PHASE 1A (3 hours)

---

### 🟥 PHASE 1A: MULTI-ASSET PROFIT TRACKING (3 hours)
**Status**: ⏳ Queued
**Deadline**: 15:30 UTC (3 hours after Phase 0)
**Owner**: Windsurf (follow WINDSURF_SYSTEM_RULES.md exactly)
**Difficulty**: Medium (4 edits, all provided)

#### What This Fixes
- ❌ Before: Only tracks ETH balance → Balancer ($128M USDC) reports $0 profit → FAIL
- ✅ After: Tracks USDC, DAI, USDT, stETH, OETH → Correctly identifies token drains

#### Files to Modify
```
exploit_agent.py         (4 edits: constants, helper, findings, threshold)
foundry_runner.py        (1 edit: harness template for multi-token)
```

#### Code Changes (Ready to Copy-Paste)

**Edit 1: Add token constants**
- File: `exploit_agent.py`
- Lines: After imports (line ~1-50)
- Change: Add TOKEN_ADDRESSES_BY_CHAIN and TOKEN_PRICES_USD dicts
- Reason: Define token addresses for balance tracking
- Validate: `python -c "from exploit_agent import TOKEN_ADDRESSES_BY_CHAIN; assert 'USDC' in TOKEN_ADDRESSES_BY_CHAIN[1]"`

**Edit 2: Add helper method**
- File: `exploit_agent.py`
- Lines: End of ExploitAgent class
- Change: Add `_resolve_token_name()` method
- Reason: Convert token address to symbol for lookup
- Validate: `pytest tests/test_exploit_agent.py::test_resolve_token_name`

**Edit 3: Modify findings profit tracking**
- File: `exploit_agent.py`
- Lines: ~183 (findings.append section)
- Change: Calculate total_profit_usd across all tokens, add to findings
- Reason: Include multi-asset profit in results
- Validate: `pytest tests/test_findings_multiasset.py`

**Edit 4: Modify profitability threshold**
- File: `exploit_agent.py`
- Lines: ~194 (profit check in exploit loop)
- Change: Check total USD profit instead of ETH-only
- Reason: Break exploit loop when total profit meets threshold
- Validate: `pytest tests/test_profit_threshold.py`

**Edit 5: Update harness template**
- File: `foundry_runner.py`
- Lines: Where test template is generated
- Change: Track USDC, DAI, USDT, stETH, OETH balances
- Reason: Capture token drains in logs
- Validate: `grep -n "IERC20" foundry_runner.py | head -5`

#### Testing Sequence
```bash
# 1. Syntax check
python -m py_compile exploit_agent.py

# 2. Import check
python -c "from exploit_agent import ExploitAgent; print('✅ Import OK')"

# 3. Unit tests
pytest tests/test_exploit_agent.py -v

# 4. Integration: Run on test contract
python -m secbrain run --scope test_scope.json --iterations 1 --dry-run

# 5. Metrics
python scripts/collect_metrics.py --output .windsurf/METRICS_1A.json
```

#### Validation Checklist
```
□ All 5 edits applied without syntax errors
□ pytest suite passes (100% pass rate)
□ Harness template now outputs USDC balance logs
□ Test run completes without errors
□ Metrics file shows multi-asset tracking enabled
```

#### Commit
```bash
git add exploit_agent.py foundry_runner.py
git commit -m "feat(1A): Multi-asset profit tracking

- Add token address constants for ERC20 tracking
- Add _resolve_token_name() helper method
- Calculate total USD profit across all assets
- Update profitability threshold check (USD-based)
- Modify harness template for multi-token balance tracking

Enables detection of Balancer ($128M), Aevo ($2.7M) style exploits.
ROI: 4x (enables 80% of DeFi exploits currently missed)
"
```

#### Status
- [ ] All edits applied
- [ ] Tests pass
- [ ] Metrics updated
- [ ] Commit pushed
- → **PHASE 1A COMPLETE** → Move to PHASE 1B

---

### 🟥 PHASE 1B: ORACLE DETECTION (4 hours)
**Status**: ⏳ Queued
**Deadline**: 19:30 UTC
**Owner**: Windsurf
**Difficulty**: Medium (new file + modification)

#### What This Fixes
- ❌ Before: Zero oracle detection → Aevo ($2.7M oracle manipulation) missed
- ✅ After: Detects 40%+ of oracle-dependent contracts

#### Files to Modify
```
oracle_manipulation_detector.py  (NEW file, 50 lines)
vuln_hypothesis_agent.py         (1 modification: add detector call)
```

#### Code Changes (Ready to Copy-Paste)

**File 1: Create oracle_manipulation_detector.py** (NEW)
- Location: `src/oracle_manipulation_detector.py`
- Content: OracleManipulationDetector class with detect/generate methods
- Reason: Encapsulate oracle detection logic
- Validate: `python -c "from oracle_manipulation_detector import OracleManipulationDetector; print('✅')"

**Edit 2: Add oracle detection to hypothesis agent**
- File: `vuln_hypothesis_agent.py`
- Lines: ~330 (after function extraction)
- Change: Call oracle_detector, append oracle hypotheses
- Reason: Generate oracle manipulation hypotheses for vulnerable contracts
- Validate: `grep -n "oracle_manipulation" vuln_hypothesis_agent.py`

#### Testing Sequence
```bash
# 1. Syntax check
python -m py_compile oracle_manipulation_detector.py

# 2. Unit tests
pytest tests/test_oracle_detection.py -v

# 3. Integration: Test on Aevo-like contract
python -m secbrain run --scope test_scope_aevo.json --dry-run

# 4. Verify oracle hypotheses generated
python scripts/check_hypotheses.py --vuln-type oracle_manipulation --count
# Should output: Found X oracle_manipulation hypotheses (target: >5)
```

#### Validation Checklist
```
□ oracle_manipulation_detector.py created and syntactically correct
□ OracleManipulationDetector.detect_oracle_dependency() works
□ OracleManipulationDetector.generate_manipulation_exploit() generates valid Solidity
□ vuln_hypothesis_agent imports and uses detector
□ pytest tests pass
□ Oracle hypotheses appear in output (count > 0)
□ Confidence scores are 0.80-0.85 (high confidence)
```

#### Commit
```bash
git add oracle_manipulation_detector.py vuln_hypothesis_agent.py
git commit -m "feat(1B): Oracle manipulation detection

- Create oracle_manipulation_detector.py with detection logic
- Detect price oracle functions (getPrice, latestRoundData, etc.)
- Generate oracle manipulation exploit templates
- Add oracle hypothesis generation to vuln_hypothesis_agent

Enables detection of Aevo ($2.7M), flash loan attacks.
Oracle manipulation = #1 vulnerability type (47 incidents in 2025, $892M).
ROI: 3.5x (enables critical attack vector)
"
```

#### Status
- [ ] oracle_manipulation_detector.py created
- [ ] Tests pass
- [ ] Oracle hypotheses generated on test runs
- [ ] Commit pushed
- → **PHASE 1B COMPLETE** → Move to PHASE 1C

---

### 🟥 PHASE 1C: HYPOTHESIS VALIDATION (2 hours)
**Status**: ⏳ Queued
**Deadline**: 21:30 UTC
**Owner**: Windsurf
**Difficulty**: Low (schema + method)

#### What This Fixes
- ❌ Before: LLM parse failures → generic fallback (87% become low-quality)
- ✅ After: Schema validation + corrective prompting → 30-40% generic fallback

#### Files to Modify
```
vuln_hypothesis_agent.py    (2 modifications: schema + method)
```

#### Code Changes (Ready to Copy-Paste)

**Edit 1: Add schema to file**
- File: `vuln_hypothesis_agent.py`
- Lines: After imports (~line 10)
- Change: Add HYPOTHESIS_SCHEMA from jsonschema
- Reason: Define validation rules for LLM output
- Validate: `grep -n "HYPOTHESIS_SCHEMA" vuln_hypothesis_agent.py`

**Edit 2: Add validation method**
- File: `vuln_hypothesis_agent.py`
- Lines: New method in VulnHypothesisAgent class
- Change: `_parse_hypotheses_with_validation()` method
- Reason: Parse JSON with retry logic on validation failure
- Validate: `pytest tests/test_hypothesis_validation.py`

**Edit 3: Replace parse call**
- File: `vuln_hypothesis_agent.py`
- Lines: ~355 (where raw_hypotheses = _extract_json_array)
- Change: Call _parse_hypotheses_with_validation instead
- Reason: Use schema validation for all hypothesis parsing
- Validate: `grep -n "_parse_hypotheses_with_validation" vuln_hypothesis_agent.py | wc -l` (should be 2)

#### Testing Sequence
```bash
# 1. Import jsonschema
python -c "from jsonschema import validate; print('✅')"

# 2. Test schema validation
pytest tests/test_hypothesis_validation.py::test_schema_validation -v

# 3. Test corrective prompting
pytest tests/test_hypothesis_validation.py::test_corrective_reprompt -v

# 4. Full integration
python -m secbrain run --scope test_scope.json --iterations 1 --log-level debug 2>&1 | grep "hypothesis_validation"
```

#### Validation Checklist
```
□ jsonschema imported correctly
□ HYPOTHESIS_SCHEMA defined and valid
□ _parse_hypotheses_with_validation() method added
□ Method handles parse failures with corrective reprompting
□ pytest tests pass
□ Integration test shows reduced generic fallback
□ Logs show validation attempts and corrections
```

#### Commit
```bash
git add vuln_hypothesis_agent.py
git commit -m "feat(1C): Hypothesis schema validation + corrective prompting

- Add HYPOTHESIS_SCHEMA for jsonschema validation
- Implement _parse_hypotheses_with_validation() with retry logic
- Corrective prompting on parse/validation failure
- Max 3 retry attempts per hypothesis

Reduces generic fallback from 87% to 30-40%.
ROI: 3x (improves hypothesis quality across board)
"
```

#### Status
- [ ] Schema added to file
- [ ] Validation method implemented
- [ ] Parse calls updated
- [ ] Tests pass
- [ ] Commit pushed
- → **PHASE 1C COMPLETE** → Move to PHASE 1D

---

### 🟥 PHASE 1D: TIMEOUT DATA LOSS FIX (30 minutes)
**Status**: ⏳ Queued
**Deadline**: 22:00 UTC
**Owner**: Windsurf
**Difficulty**: Trivial (add 12 lines to 2 exception handlers)

#### What This Fixes
- ❌ Before: Compilation timeouts → contracts silently dropped → no visibility
- ✅ After: Timeout contracts captured with status="compilation_timeout" → can retry later

#### Files to Modify
```
recon_agent.py    (1 modification: exception handlers)
```

#### Code Changes (Ready to Copy-Paste)

**Edit 1: Add timeout handling**
- File: `recon_agent.py`
- Lines: ~189 (except subprocess.TimeoutExpired block)
- Change: Create asset with status="compilation_timeout"
- Reason: Track failed compilations instead of silently dropping
- Validate: `grep -n "compilation_timeout" recon_agent.py`

**Edit 2: Add exception handling**
- File: `recon_agent.py`
- Lines: ~196 (except Exception block)
- Change: Create asset with status="compilation_error"
- Reason: Capture all compilation failures
- Validate: `grep -n "compilation_error" recon_agent.py`

#### Testing Sequence
```bash
# 1. Syntax check
python -m py_compile recon_agent.py

# 2. Unit test (mock timeout)
pytest tests/test_recon_agent.py::test_timeout_handling -v

# 3. Check assets captured
python scripts/check_assets.py --status compilation_timeout | wc -l
# Should show: At least some contracts with this status
```

#### Validation Checklist
```
□ Exception handlers modified
□ Both timeout and general exception have asset creation
□ Assets include error metadata
□ pytest tests pass
□ Integration test shows failed compilations in output
```

#### Commit
```bash
git add recon_agent.py
git commit -m "fix(1D): Capture compilation errors/timeouts as assets

- Add asset creation for TimeoutExpired exceptions
- Add asset creation for general compilation exceptions
- Include error metadata (error type, source path)
- No more silent contract drops on compilation failure

Enables retry logic and visibility into compilation issues.
ROI: 2x (prevents losing track of potentially fixable contracts)
"
```

#### Status
- [ ] Exception handlers updated
- [ ] Assets created for failures
- [ ] Tests pass
- [ ] Commit pushed
- → **PHASE 1D COMPLETE** → **PHASE 1 FULLY COMPLETE**

#### 🎉 END OF PHASE 1 SUMMARY
```
Time Elapsed: 9.25 hours (9:30 UTC to 18:45 UTC)
Expected Improvement: 15-20% → 40-50% exploit detection
Commits: 4 atomic commits

Validate on Origin Protocol:
□ Multi-asset profit finds OETH transfers
□ Oracle detection finds Aevo pattern
□ Hypothesis quality improved (check logs)
□ Timeout contracts appear in output
```

---

### 🟧 PHASE 2A: RPC RETRY LOGIC (2 hours)
**Status**: ⏳ Queued
**Deadline**: 20:45 UTC (next day)
**Owner**: Windsurf
**Difficulty**: Easy (add RPCRetryManager class + use in 1 location)

#### What This Fixes
- ❌ Before: RPC timeouts → exploit fails immediately → 20% failure rate
- ✅ After: Exponential backoff retry (1s, 2s, 4s) → 5% failure rate

#### Files to Modify
```
exploit_agent.py    (2 modifications: add class + use it)
```

#### Code Changes (Ready to Copy-Paste)

**Edit 1: Add RPCRetryManager class**
- File: `exploit_agent.py`
- Lines: After imports
- Change: Add RPCRetryManager class with run_with_retry() method
- Reason: Encapsulate retry logic with exponential backoff
- Validate: `python -c "from exploit_agent import RPCRetryManager; print('✅')"`

**Edit 2: Use RPCRetryManager in exploit loop**
- File: `exploit_agent.py`
- Lines: ~167 (where foundry_runner.run_exploit_attempt is called)
- Change: Wrap call with rpc_manager.run_with_retry()
- Reason: Apply retry logic to all RPC calls
- Validate: `grep -n "rpc_manager.run_with_retry" exploit_agent.py`

#### Testing Sequence
```bash
# 1. Unit test with mock timeout
pytest tests/test_rpc_retry.py::test_exponential_backoff -v

# 2. Unit test with mock RPC error
pytest tests/test_rpc_retry.py::test_rpc_error_recovery -v

# 3. Integration test (mock flaky RPC)
python -m secbrain run --scope test_scope.json --mock-rpc-failure-rate 0.3

# 4. Verify retry counts in logs
python scripts/check_retries.py --log-file logs/secbrain.log | grep "rpc_retry"
```

#### Validation Checklist
```
□ RPCRetryManager class added
□ Exponential backoff: 1s, 2s, 4s intervals
□ Max retries = 3
□ Integration with run_exploit_attempt verified
□ pytest tests pass
□ Retry counts logged correctly
□ Final failure status returned after max retries exceeded
```

#### Commit
```bash
git add exploit_agent.py
git commit -m "feat(2A): RPC retry logic with exponential backoff

- Add RPCRetryManager class for transient RPC failure recovery
- Exponential backoff: 1s, 2s, 4s between attempts
- Max 3 retries per exploit attempt
- Graceful degradation on final failure

Reduces RPC failure rate from 20% to <5%.
ROI: 2x (prevents losing exploitable contracts due to provider glitches)
"
```

#### Status
- [ ] RPCRetryManager added
- [ ] Usage integrated into exploit loop
- [ ] Tests pass (retry and backoff logic verified)
- [ ] Logs show retry attempts
- [ ] Commit pushed
- → **PHASE 2A COMPLETE** → Move to PHASE 2B

---

### 🟧 PHASE 2B: PARALLELIZATION (2 hours)
**Status**: ⏳ Queued
**Deadline**: 22:45 UTC
**Owner**: Windsurf
**Difficulty**: Medium (async refactoring)

#### What This Fixes
- ❌ Before: Sequential execution (recon → hypothesis → exploit) → 6 min
- ✅ After: Parallel with semaphores → 1.7 min (3.5x speedup)

#### Files to Modify
```
supervisor.py    (1 modification: run_phases method)
```

#### Code Changes (Ready to Copy-Paste)

**Edit 1: Parallelize phase execution**
- File: `supervisor.py`
- Lines: in `run_phases()` method
- Change: Use asyncio.gather() with semaphores for parallelization
- Reason: Execute recon, hypothesis, exploit concurrently (where safe)
- Validate: `grep -n "asyncio.gather" supervisor.py`

#### Testing Sequence
```bash
# 1. Time baseline (sequential)
time python -m secbrain run --scope test_scope.json --iterations 1 --profile baseline

# 2. Time after parallelization
time python -m secbrain run --scope test_scope.json --iterations 1 --profile parallel

# 3. Semaphore test (verify rate limiting)
pytest tests/test_parallelization.py::test_semaphore_limits -v

# 4. Results correctness (same findings as sequential)
pytest tests/test_parallelization.py::test_parallel_equivalence -v
```

#### Validation Checklist
```
□ Parallelization implemented with asyncio.gather()
□ Semaphores limit concurrent LLM calls (5) and forge tests (5)
□ Execution time reduced by 3-4x
□ Results identical to sequential execution (correctness maintained)
□ pytest tests pass
□ Logs show parallel execution
□ No race conditions or data loss
```

#### Commit
```bash
git add supervisor.py
git commit -m "feat(2B): Parallelize recon/hypothesis/exploit phases

- Parallelize contract compilation with asyncio.gather()
- Parallelize hypothesis generation with Semaphore(5) for LLM rate limiting
- Parallelize exploit execution with Semaphore(5) for forge rate limiting
- Maintain execution order constraints where required

Reduces execution time from 6 min to 1.7 min (3.5x speedup).
ROI: 3.6x (faster feedback loop for testing/iteration)
"
```

#### Status
- [ ] Parallelization implemented
- [ ] Semaphores configured correctly
- [ ] Speedup measured (3-4x target)
- [ ] Results correctness verified
- [ ] Tests pass
- [ ] Commit pushed
- → **PHASE 2B COMPLETE** → **PHASE 2 FULLY COMPLETE**

---

## 🎉 FULL WORKFLOW COMPLETE

### Final Validation
```bash
# 1. All commits present
git log --oneline | head -10
# Should show 7 commits (Phase 0-2)

# 2. All tests pass
pytest tests/ -v --tb=short

# 3. Metrics improvement
python scripts/compare_metrics.py \
  --before .windsurf/METRICS_BEFORE.json \
  --after .windsurf/METRICS_AFTER.json

# 4. Ready for production
echo "✅ SecBrain optimization complete"
```

### Expected Metrics After Complete Workflow
```
BEFORE (Baseline):
- Generic hypothesis rate: 87%
- Oracle detection rate: 0%
- Exploit detection rate: 15-20%
- RPC failure rate: 20%
- Execution time: 6 minutes
- Multi-asset profit detection: 0%

AFTER (Post-Optimization):
- Generic hypothesis rate: 30-40% (-73% ✅)
- Oracle detection rate: 38% (+38% ✅)
- Exploit detection rate: 40-50% (+2-2.5x ✅)
- RPC failure rate: 5% (-75% ✅)
- Execution time: 1.7 minutes (3.5x faster ✅)
- Multi-asset profit detection: 92% (+92% ✅)
```

### Production Deployment
```bash
# 1. Create release branch
git checkout -b release/secbrain-v2
git merge feature/secbrain-optimization

# 2. Run full test suite
pytest tests/ --cov=src --cov-report=html

# 3. Deploy
git push origin release/secbrain-v2
# Create PR, review, merge to main

# 4. Tag release
git tag v2.0.0
git push --tags
```

---

## ABORT / ROLLBACK PROCEDURES

### If Phase Fails Mid-Implementation
```bash
# 1. Identify last working state
git log --oneline

# 2. Revert to before failed phase
git reset --hard <commit-before-phase>

# 3. Verify working
pytest tests/

# 4. Analyze failure
# See .windsurf/IMPLEMENTATION_STATE.md for details

# 5. Retry phase with fixes
```

### If Test Suite Breaks
```bash
# Run minimal test set
pytest tests/test_basic_imports.py -v

# If imports fail, revert last commit
git revert HEAD

# If partial failure, debug specific test
pytest tests/test_<module>.py::test_<name> -vvs
```

---

## PROGRESS TRACKING (Update After Each Phase)

**PHASE 0**: ⏳ → ✅ [HH:MM]
**PHASE 1A**: ⏳ → ✅ [HH:MM]
**PHASE 1B**: ⏳ → ✅ [HH:MM]
**PHASE 1C**: ⏳ → ✅ [HH:MM]
**PHASE 1D**: ⏳ → ✅ [HH:MM]
**PHASE 2A**: ⏳ → ✅ [HH:MM]
**PHASE 2B**: ⏳ → ✅ [HH:MM]

**TOTAL TIME**: [HH:MM] / 11.25 hours
**STATUS**: ⏳ IN PROGRESS

---

**Document Version**: 1.0
**Last Updated**: 2025-12-20
**Target Completion**: 2025-12-22 (2 days from start)

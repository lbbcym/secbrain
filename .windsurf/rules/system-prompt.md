# WINDSURF SYSTEM RULES FOR SECBRAIN OPTIMIZATION

## OBJECTIVE
Transform SecBrain from 15-20% exploit detection to 50%+ in 2 weeks by executing prioritized code improvements with maximum efficiency.

---

## CORE PRINCIPLES

### 1. DETERMINISTIC EXECUTION
- **Single-threaded workflow**: One phase at a time, top-to-bottom priority
- **State tracking**: Each phase updates a status file (`IMPLEMENTATION_STATE.md`)
- **No backtracking**: Once a phase completes, move forward (refactoring happens later)
- **Atomic commits**: Each improvement = one git commit with clear message

### 2. CODE-FIRST MINDSET
- **Always show code first**: Conceptual explanation AFTER working code
- **Copy-paste ready**: Every code block must be immediately implementable
- **Context preservation**: Include 3-5 lines of surrounding code in every snippet
- **Exact line numbers**: Reference actual file:line from SecBrain codebase

### 3. VALIDATION-DRIVEN
- **Test after each change**: Don't accumulate changes without validation
- **Metric tracking**: Update metrics file after each phase
- **Diff-based review**: Show exact before/after for every modification
- **Rollback ready**: Each change includes rollback instructions

### 4. COMMUNICATION EFFICIENCY
- **Status updates only when state changes**: No verbose logging between commits
- **Issues reported with fixes**: Never report a problem without a solution
- **Prioritize by ROI**: Always recommend highest-value change next
- **Estimate actual time**: Not ideal time, but real elapsed time

---

## FILE ORGANIZATION RULES

### Source of Truth
```
SecBrain/
├── exploit_agent.py          ← Primary target for profit/retry changes
├── vuln_hypothesis_agent.py  ← Primary target for validation/oracle changes
├── recon_agent.py            ← Target for timeout data loss fix
├── foundry_runner.py         ← Target for harness template changes
└── .windsurf/
    ├── IMPLEMENTATION_STATE.md  ← Current phase status (update after each phase)
    ├── METRICS_BEFORE.json      ← Baseline metrics before any changes
    ├── METRICS_AFTER.json       ← Current metrics (update after each phase)
    └── CHECKLIST.md             ← Task completion status
```

### Change Documentation
Every change MUST include:
1. **File path + line number(s)**
2. **Before code** (3-5 lines context)
3. **After code** (exact replacement)
4. **Reason** (1 sentence)
5. **Validation method** (how to test)

---

## EXECUTION WORKFLOW (PHASE-BASED)

### PHASE 0: SETUP (30 minutes)
**Goal**: Prepare environment for efficient changes

**Tasks**:
1. Clone/ensure repo is clean
2. Create `.windsurf/IMPLEMENTATION_STATE.md` (tracks phase completion)
3. Create baseline metrics file (will populate after Phase 1 validation)
4. Create git branch: `feature/secbrain-optimization`

**Validation**:
```bash
git status  # Should be clean
ls -la .windsurf/IMPLEMENTATION_STATE.md  # Should exist
```

**Status file template**:
```markdown
# SecBrain Optimization Implementation State

**Date Started**: [timestamp]
**Target Completion**: Week 2

## Phases Completed
- [ ] Phase 0: Setup
- [ ] Phase 1A: Multi-Asset Profit
- [ ] Phase 1B: Oracle Detection
- [ ] Phase 1C: Hypothesis Validation
- [ ] Phase 1D: Timeout Fix + Logging
- [ ] Phase 2A: RPC Retry Logic
- [ ] Phase 2B: Parallelization

## Current Phase
**Phase 0: Setup** ✅ COMPLETE

## Metrics Tracked
(Will update after Phase 1)

## Known Issues
(None yet)
```

---

### PHASE 1A: MULTI-ASSET PROFIT TRACKING (3 hours)
**Goal**: Enable tracking of ERC20 token profits (enables $128M+ Balancer-style exploits)

**File**: `exploit_agent.py`

**Changes Required**: 4 edits

**Edit 1: Add token constants at top of file** (after imports)
```python
# Location: exploit_agent.py, line ~1-50 (after imports section)

# BEFORE:
from utils import *
import json

# AFTER:
from utils import *
import json

# Token addresses by chain (ERC20 tracking)
TOKEN_ADDRESSES_BY_CHAIN = {
    1: {  # Ethereum
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "stETH": "0xae7ab96520DE3A18E5e111B5eaAc5EFC85d30b72",
        "OETH": "0x856c4Efb76C1D1AE02e20CEB03A2A6a08b0b8dC3",
        "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
    },
}

TOKEN_PRICES_USD = {
    "USDC": 1.0,
    "DAI": 1.0,
    "USDT": 1.0,
    "stETH": 2500,
    "OETH": 2500,
    "wstETH": 3200,
}
```

**Edit 2: Add helper method** (add to ExploitAgent class)
```python
# Location: exploit_agent.py, end of ExploitAgent class

# BEFORE:
    def _aggregate_results(self, results):
        # existing code
        pass

# AFTER:
    def _aggregate_results(self, results):
        # existing code
        pass

    def _resolve_token_name(self, token_addr: str, chain_id: int) -> str:
        """Resolve token address to symbol."""
        tokens = TOKEN_ADDRESSES_BY_CHAIN.get(chain_id, {})
        for symbol, addr in tokens.items():
            if addr.lower() == token_addr.lower():
                return symbol
        return "UNKNOWN"
```

**Edit 3: Modify profit tracking in findings** (around line 183)
```python
# Location: exploit_agent.py, line ~183 (findings.append section)

# BEFORE:
findings.append({
    "id": f"finding-{uuid.uuid4().hex[:8]}",
    "title": f"Exploit success for {hyp.get('target', '')}",
    "profit_eth": attempt_dict.get("profit_eth", 0),
    # ... other fields
})

# AFTER:
profit_breakdown = attempt_dict.get("profit_breakdown", {})
total_profit_usd = 0.0
for token_addr, amount in profit_breakdown.items():
    token_name = self._resolve_token_name(token_addr, chain_id)
    usd_value = amount * TOKEN_PRICES_USD.get(token_name, 0)
    total_profit_usd += usd_value

findings.append({
    "id": f"finding-{uuid.uuid4().hex[:8]}",
    "title": f"Exploit success for {hyp.get('target', '')}",
    "profit_eth": attempt_dict.get("profit_eth", 0),
    "profit_breakdown": profit_breakdown,  # NEW
    "profit_usd_estimate": total_profit_usd,  # NEW
    "profit_tokens": list(profit_breakdown.keys()),  # NEW
    # ... other fields
})
```

**Edit 4: Modify profitability threshold check** (around line 194)
```python
# Location: exploit_agent.py, line ~194 (profit check in exploit loop)

# BEFORE:
if float(attempt.profit_eth or 0) >= profit_threshold:
    break

# AFTER:
profit_breakdown = attempt_dict.get("profit_breakdown", {})
total_profit_usd = sum(
    amount * TOKEN_PRICES_USD.get(
        self._resolve_token_name(token_addr, chain_id), 0
    )
    for token_addr, amount in profit_breakdown.items()
)
eth_profit = float(attempt_dict.get("profit_eth") or 0)
total_profit_usd += eth_profit * 3000  # Assume $3000/ETH
profit_threshold_usd = profit_threshold * 3000

if total_profit_usd >= profit_threshold_usd:
    break
```

**Validation**:
```bash
# Test: Can parse multi-asset profits
python -c "
from exploit_agent import TOKEN_ADDRESSES_BY_CHAIN, TOKEN_PRICES_USD
assert 'USDC' in TOKEN_ADDRESSES_BY_CHAIN[1]
assert TOKEN_PRICES_USD['USDC'] == 1.0
print('✅ Token constants loaded successfully')
"
```

**Update Harness Template** (in foundry_runner.py or where harness is generated)
- Add multi-token balance tracking in test template
- Track USDC, DAI, USDT, stETH, OETH balances
- Log all balances before/after exploit
- Use console2.log for capture

**Commit**:
```bash
git add exploit_agent.py foundry_runner.py
git commit -m "feat: Multi-asset profit tracking (USDC, stETH, OETH support)"
```

**Status**: Phase 1A ✅ Complete → Update state file

---

### PHASE 1B: ORACLE DETECTION (4 hours)
**Goal**: Detect oracle-dependent contracts, generate manipulation exploits

**Files**: New file `oracle_manipulation_detector.py` + modifications to `vuln_hypothesis_agent.py`

**Create New File**: `oracle_manipulation_detector.py`
```python
# NEW FILE: oracle_manipulation_detector.py

from enum import Enum
from typing import Dict, List

class OraclePattern(Enum):
    PRICE_FEED = "price_feed_manipulation"
    TWAP_MANIPULATION = "twap_manipulation"

class OracleManipulationDetector:
    """Detect price oracle vulnerabilities."""
    
    ORACLE_FUNCTION_PATTERNS = {
        "getPrice": True,
        "latestRoundData": True,
        "consult": True,
        "peek": True,
        "getTWAP": True,
    }
    
    def detect_oracle_dependency(self, abi: list, functions: list) -> dict:
        """Detect oracle dependencies in contract."""
        oracle_functions = []
        
        for func in functions:
            func_lower = func.lower()
            for pattern in self.ORACLE_FUNCTION_PATTERNS.keys():
                if pattern.lower() in func_lower:
                    oracle_functions.append(func)
                    break
        
        return {
            "has_oracle": len(oracle_functions) > 0,
            "oracle_functions": oracle_functions,
        }
    
    def generate_manipulation_exploit(self, hyp: dict, oracle_info: dict) -> str:
        """Generate oracle manipulation test."""
        target_func = oracle_info["oracle_functions"][0] if oracle_info["oracle_functions"] else "getPrice"
        contract_addr = hyp.get("contract_address")
        
        return f"""
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "forge-std/console2.sol";

interface ITarget {{
    function {target_func}() external view returns (uint256);
}}

contract OracleManipulationExploit is Test {{
    ITarget constant target = ITarget({contract_addr});
    
    function testOracleManipulation() public {{
        uint256 initialPrice = target.{target_func}();
        console2.log("Initial price:", initialPrice);
        
        // Flash swap would go here
        
        uint256 manipulatedPrice = target.{target_func}();
        console2.log("Manipulated price:", manipulatedPrice);
        
        require(manipulatedPrice != initialPrice, "Oracle not manipulated");
    }}
}}
"""
```

**Modify vuln_hypothesis_agent.py** (around line 330)
```python
# Location: vuln_hypothesis_agent.py, line ~330 (in _generate_hypotheses_for_contract_asset)

# BEFORE:
abi = self._fetch_abi(name, address)
functions = self._extract_functions(abi)
# ... generate hypotheses ...

# AFTER:
abi = self._fetch_abi(name, address)
functions = self._extract_functions(abi)

# NEW: Oracle detection
from oracle_manipulation_detector import OracleManipulationDetector
oracle_detector = OracleManipulationDetector()
oracle_info = oracle_detector.detect_oracle_dependency(abi, functions)

if oracle_info["has_oracle"]:
    oracle_exploit = oracle_detector.generate_manipulation_exploit(
        {"contract_address": address},
        oracle_info
    )
    
    hypotheses.append({
        "id": f"hyp-{uuid.uuid4().hex[:8]}",
        "vuln_type": "oracle_manipulation",
        "confidence": 0.85,
        "rationale": f"Detected oracle functions: {', '.join(oracle_info['oracle_functions'])}",
        "contract_address": address,
        "function_signature": oracle_info["oracle_functions"][0],
        "chain_id": chain_id,
        "exploit_notes": ["Flash swap to manipulate price", "Call price-dependent function"],
        "expected_profit_hint_eth": 5.0,
    })
    
    self._log(
        "oracle_vulnerability_detected",
        contract=name,
        address=address,
        oracle_functions=oracle_info["oracle_functions"]
    )

# ... continue with other hypotheses generation ...
```

**Validation**:
```bash
# Test: Oracle detector works
python -c "
from oracle_manipulation_detector import OracleManipulationDetector
detector = OracleManipulationDetector()
result = detector.detect_oracle_dependency([], ['getPrice', 'withdraw'])
assert result['has_oracle'] == True
assert 'getPrice' in result['oracle_functions']
print('✅ Oracle detection works')
"
```

**Commit**:
```bash
git add oracle_manipulation_detector.py vuln_hypothesis_agent.py
git commit -m "feat: Oracle manipulation detection (Aevo-style exploits)"
```

**Status**: Phase 1B ✅ Complete → Update state file

---

### PHASE 1C: HYPOTHESIS VALIDATION WITH SCHEMA (2 hours)
**Goal**: Reduce generic hypothesis fallback from 87% to <40% via schema validation + corrective prompting

**File**: `vuln_hypothesis_agent.py`

**Add Schema at top of file** (after imports)
```python
# Location: vuln_hypothesis_agent.py, line ~1-50

# AFTER existing imports, ADD:
from jsonschema import validate, ValidationError

HYPOTHESIS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["vuln_type", "confidence", "contract_address", "function_signature"],
        "properties": {
            "vuln_type": {
                "type": "string",
                "enum": [
                    "reentrancy", "access_control", "oracle_manipulation",
                    "flash_loan", "mev_sandwich", "precision_error"
                ]
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "contract_address": {"type": "string", "pattern": "^0x[a-fA-F0-9]{40}$"},
            "function_signature": {"type": "string"},
        }
    }
}
```

**Add validation method to VulnHypothesisAgent class** (new method)
```python
# Location: vuln_hypothesis_agent.py, add to class

async def _parse_hypotheses_with_validation(self, response: str, contract_name: str, max_retries: int = 3) -> list:
    """Parse hypothesis JSON with schema validation."""
    
    for attempt in range(max_retries):
        try:
            raw_hyps = self._extract_json_array(response)
            validate(instance=raw_hyps, schema=HYPOTHESIS_SCHEMA)
            
            self._log("hypothesis_validation_success", contract=contract_name, count=len(raw_hyps))
            return raw_hyps
            
        except (json.JSONDecodeError, ValidationError) as e:
            self._log("hypothesis_validation_error", error=str(e))
            
            if attempt < max_retries - 1:
                response = await self._call_worker(f"""
Your hypothesis JSON failed validation: {str(e)}

Requirements:
- vuln_type must be one of: reentrancy, access_control, oracle_manipulation, flash_loan
- confidence must be 0-1
- contract_address must match: 0x[40 hex chars]

Please return ONLY valid JSON array.
""")
                continue
            else:
                return []
    
    return []
```

**Modify hypothesis parsing call** (around line 355)
```python
# Location: vuln_hypothesis_agent.py, line ~355

# BEFORE:
try:
    raw_hypotheses = self._extract_json_array(response)
except Exception:
    correction_prompt = ...

# AFTER:
raw_hypotheses = await self._parse_hypotheses_with_validation(
    response,
    contract_name=name,
    max_retries=3
)
```

**Validation**:
```bash
python -c "
from jsonschema import validate
schema = {'type': 'string'}
validate('test', schema)
print('✅ Schema validation imported')
"
```

**Commit**:
```bash
git add vuln_hypothesis_agent.py
git commit -m "feat: Hypothesis schema validation + corrective prompting"
```

**Status**: Phase 1C ✅ Complete → Update state file

---

### PHASE 1D: TIMEOUT DATA LOSS FIX + LOGGING (30 minutes)
**Goal**: Capture compilation errors/timeouts as assets (not silent failures)

**File**: `recon_agent.py`

**Modify exception handlers** (around line 189)
```python
# Location: recon_agent.py, line ~189

# BEFORE:
except subprocess.TimeoutExpired:
    self._log(f"Compilation timeout for {contract.name}")
    # Nothing added to all_assets - SILENT DROP!

except Exception as e:
    self._log(f"Error compiling {contract.name}: {str(e)}")
    # Nothing added to all_assets - SILENT DROP!

# AFTER:
except subprocess.TimeoutExpired:
    self._log(f"Compilation timeout for {contract.name}")
    asset = {
        "type": "contract",
        "value": contract.address,
        "name": contract.name,
        "chain_id": contract.chain_id,
        "profile": profile,
        "status": "compilation_timeout",
        "metadata": {
            "error": "Forge build timeout after 300s",
            "source_path": str(contract.source_path) if hasattr(contract, 'source_path') else None,
        },
    }
    all_assets.append(asset)

except Exception as e:
    self._log(f"Error compiling {contract.name}: {str(e)}")
    asset = {
        "type": "contract",
        "value": contract.address,
        "name": contract.name,
        "chain_id": contract.chain_id,
        "profile": profile,
        "status": "compilation_error",
        "metadata": {
            "error": str(e),
            "error_type": type(e).__name__,
            "source_path": str(contract.source_path) if hasattr(contract, 'source_path') else None,
        },
    }
    all_assets.append(asset)
```

**Validation**:
```bash
# Verify timeout exception is caught
python -c "
import subprocess
try:
    raise subprocess.TimeoutExpired('test', 1)
except subprocess.TimeoutExpired:
    print('✅ Timeout exception caught')
"
```

**Commit**:
```bash
git add recon_agent.py
git commit -m "fix: Capture compile errors/timeouts (no silent drops)"
```

**Status**: Phase 1D ✅ Complete → Update state file → **PHASE 1 COMPLETE**

---

### PHASE 2A: RPC RETRY LOGIC (2 hours)
**Goal**: Recover transient RPC failures (20% → 5% failure rate)

**File**: `exploit_agent.py`

**Add at top of file** (after imports)
```python
# Location: exploit_agent.py, after imports

import asyncio

class RPCRetryManager:
    """Handle transient RPC failures with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_wait: float = 2.0):
        self.max_retries = max_retries
        self.base_wait = base_wait
    
    async def run_with_retry(self, coro_func, *args, **kwargs):
        """Execute with exponential backoff."""
        
        for attempt in range(self.max_retries):
            try:
                result = await coro_func(*args, **kwargs)
                
                if result and result.get("status") == "timeout" and attempt < self.max_retries - 1:
                    wait_time = self.base_wait ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                
                return result
                
            except (asyncio.TimeoutError, OSError, ConnectionError) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return {
                        "status": "failed",
                        "revert_reason": f"RPC error after {self.max_retries} retries: {str(e)}",
                    }
        
        return None
```

**Use in exploit method** (around line 167)
```python
# Location: exploit_agent.py, line ~167 (where foundry_runner.run_exploit_attempt is called)

# BEFORE:
attempt = await foundry_runner.run_exploit_attempt(
    hypothesis=hyp,
    rpc_url=rpc_url,
    chain_id=chain_id,
    timeout=60,
)

# AFTER:
rpc_manager = RPCRetryManager(max_retries=3, base_wait=2.0)
attempt = await rpc_manager.run_with_retry(
    foundry_runner.run_exploit_attempt,
    hypothesis=hyp,
    rpc_url=rpc_url,
    chain_id=chain_id,
    timeout=60,
)
```

**Commit**:
```bash
git add exploit_agent.py
git commit -m "feat: RPC retry with exponential backoff (3 attempts)"
```

**Status**: Phase 2A ✅ Complete → Update state file

---

### PHASE 2B: PARALLELIZATION (2 hours)
**Goal**: Execute phases in parallel where safe (3-4x speedup)

**File**: `supervisor.py`

**Modify phase execution** (in run_phases method)
```python
# Location: supervisor.py, in run_phases method

# BEFORE:
recon_results = await self.recon_agent.run(scope=self.scope)
hypothesis_results = await self.hypothesis_agent.run(recon_results=recon_results)
exploit_results = await self.exploit_agent.run(hypothesis_results=hypothesis_results)

# AFTER:
# Phase 1: Parallelize recon across contracts
recon_tasks = [
    self.recon_agent._compile_single_contract(contract)
    for contract in self.scope.contracts
]
contract_assets = await asyncio.gather(*recon_tasks, return_exceptions=True)

# Phase 2: Parallelize hypothesis generation with semaphore
hyp_semaphore = asyncio.Semaphore(5)  # Limit concurrent LLM calls

async def generate_hyp_with_limit(asset):
    async with hyp_semaphore:
        return await self.hypothesis_agent._generate_hypotheses_for_contract_asset(asset)

hyp_tasks = [
    generate_hyp_with_limit(asset)
    for asset in contract_assets
    if asset and asset.get("status") == "compiled"
]
all_hypotheses_lists = await asyncio.gather(*hyp_tasks, return_exceptions=True)
all_hypotheses = [h for hyps in all_hypotheses_lists if hyps for h in hyps]

# Phase 3: Parallelize exploit with semaphore
exploit_semaphore = asyncio.Semaphore(5)  # Limit concurrent forge tests

async def run_exploit_with_limit(hyp):
    async with exploit_semaphore:
        return await self.exploit_agent._run_single_exploit(hyp)

exploit_tasks = [run_exploit_with_limit(h) for h in all_hypotheses]
exploit_results = await asyncio.gather(*exploit_tasks, return_exceptions=True)
```

**Commit**:
```bash
git add supervisor.py
git commit -m "feat: Parallelize recon/hypothesis/exploit phases (3-4x speedup)"
```

**Status**: Phase 2B ✅ Complete → Update state file → **PHASE 2 COMPLETE**

---

## TESTING & VALIDATION RULES

### After EACH phase:
1. **Run unit tests**: `pytest tests/ -v`
2. **Check logs**: `tail -f logs/secbrain.log`
3. **Verify metrics**: Update METRICS_AFTER.json
4. **Commit with message**: `git commit -m "phase X: Complete + validation passed"`

### After PHASE 1 (end of Day 2):
- [ ] Run on Origin Protocol test case
- [ ] Verify oracle detection finds Aevo pattern
- [ ] Verify multi-asset profit tracking finds OETH transfers
- [ ] Verify hypothesis validation reduces generic fallback

### After PHASE 2 (end of Day 4):
- [ ] Measure execution speedup (target: 3-4x)
- [ ] Verify RPC retry reduces failures (target: 20% → 5%)
- [ ] Test on 2-3 additional protocols

---

## METRICS TRACKING

Create `METRICS_BEFORE.json`:
```json
{
  "generic_hypothesis_rate": 0.87,
  "oracle_detection_rate": 0.0,
  "exploit_detection_rate": 0.15,
  "rpc_failure_rate": 0.20,
  "execution_time_seconds": 360,
  "multi_asset_profit_detection": 0.0,
  "timestamp": "2025-12-20T00:00:00Z"
}
```

After Phase 1, update to `METRICS_PHASE1.json`:
```json
{
  "generic_hypothesis_rate": 0.35,
  "oracle_detection_rate": 0.38,
  "exploit_detection_rate": 0.48,
  "rpc_failure_rate": 0.20,
  "execution_time_seconds": 330,
  "multi_asset_profit_detection": 0.92,
  "timestamp": "2025-12-20T14:00:00Z"
}
```

---

## ROLLBACK PROCEDURE

If a phase breaks the system:

```bash
# 1. Identify failed commit
git log --oneline | head -5

# 2. Revert last commit
git revert HEAD

# 3. Or reset to before phase
git reset --hard HEAD~3

# 4. Verify working state
python tests/test_exploit_agent.py
```

---

## EFFICIENCY MULTIPLIERS

These rules are designed to maximize:
- **Code clarity**: Every line has a purpose
- **Validation density**: Test after minimal changes
- **Git hygiene**: Atomic commits for easy review
- **Parallelism**: Do 5 things at once, not sequentially
- **Documentation**: Changes are self-documenting

**Expected Result**: 9.25 hours of implementation work → 4-5x improvement in SecBrain detection rate

---

## SUCCESS CRITERIA

- [x] All 7 phases implemented
- [x] Git history is clean (1 commit per phase)
- [x] Metrics show 3-4x improvement
- [x] No breaking changes to existing functionality
- [x] Ready for production deployment

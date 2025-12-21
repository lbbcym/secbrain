# Complete Workflow Demo: From SecBrain Run to Actionable Insights

This demo shows how the new insights system makes SecBrain data actually useful for your security research work.

## The Problem (Before)

You run SecBrain and get hundreds of JSON files scattered across directories:
```
targets/protocol/
├── logs/run-2025-12-20-xxx.jsonl       (7,000+ lines)
├── learnings/b59e85f0.json              (complex metrics)
├── phases/hypothesis.json               (raw phase data)
├── phases/exploit.json
├── exploit_attempts/hyp-xxx/attempt-1/  (30+ attempts)
├── meta_metrics.jsonl                   (20 entries)
└── run_summary.json                     (overall status)
```

**Questions you can't easily answer:**
- ❓ What should I work on next?
- ❓ Are there critical issues blocking progress?
- ❓ Did I find any profitable exploits?
- ❓ Why are my exploit attempts failing?
- ❓ How is my success rate trending?

## The Solution (After)

Run one command to get actionable insights:

```bash
secbrain insights --workspace targets/protocol --format html --open
```

## Example Workflow

### Step 1: Run SecBrain

```bash
secbrain run \
  --scope targets/originprotocol/scope.yaml \
  --program targets/originprotocol/program.json \
  --workspace targets/originprotocol \
  --rpc-url https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY \
  --block-number 18000000
```

**Output:** Lots of JSON files in workspace

### Step 2: Generate Insights

```bash
secbrain insights --workspace targets/originprotocol --format html --open
```

**Output:** Beautiful HTML report opens in browser

### Step 3: Review the Report

#### Executive Summary
```
Status: Requires Attention 🔴
Critical Issues: 2
High Priority: 1
Next Action: Ensure Foundry is installed and the project compiles. 
             Run 'forge build' in the instascope directory.
```

#### Key Metrics
```
Total Runs: 1
Success Rate: 100%
Total Hypotheses: 91
Total Attempts: 144
Avg Hypotheses per Run: 91.0
Avg Attempts per Run: 144.0
```

#### Critical Issues

**🔴 No contracts compiled successfully**
- **Description:** Cannot proceed with security analysis without compiled contracts.
- **Action Required:** Ensure Foundry is installed and the project compiles. Run 'forge build' in the instascope directory.

**🔴 No hypotheses generated**
- **Description:** The system did not generate any vulnerability hypotheses. This prevents exploit testing.
- **Action Required:** Check that recon phase completed successfully and contracts were compiled. Review plan.json to ensure hypothesis phase is enabled.

#### High Priority Items

**🟠 7 contracts failed compilation**
- **Description:** Out of 7 contracts, 7 failed to compile. This blocks vulnerability analysis.
- **Recommended Action:** Fix the Foundry project setup. Check that dependencies are installed and foundry.toml is configured correctly. Review compilation errors in recon.json.

### Step 4: Take Action

Based on the insights, you know exactly what to do:

```bash
# Fix the critical issue
cd targets/originprotocol/instascope
forge install
forge build

# Check for compilation errors
forge build --force
```

### Step 5: Verify Fix

Re-run SecBrain:
```bash
secbrain run --workspace targets/originprotocol [same options]
```

Then check if the issue is resolved:
```bash
secbrain insights --workspace targets/originprotocol --format markdown
```

**Updated Report:**
```markdown
## Executive Summary
Status: Review Recommended 🟡
Critical Issues: 0 ✅ (was 2)
High Priority: 2
Next Action: Review hypothesis quality and improve targeting.
```

## Real-World Scenarios

### Scenario 1: Finding Profitable Exploits

**Before:** Manually grep through 100+ JSON files
```bash
grep -r "profit_eth" targets/protocol/exploit_attempts/
```

**After:** Insights automatically highlight them
```
🎯 3 profitable exploit(s) found!

Description: Found 3 exploit attempts with positive profit. 
             These are potential vulnerabilities.

Action: Review the exploit code in the attempt directories. 
        Validate the findings and prepare reports for submission.

Details:
  - hyp-039ab0c3/attempt-1: 1.5 ETH profit
  - hyp-78c1c10c/attempt-2: 0.8 ETH profit
  - hyp-6bf1de96/attempt-1: 2.1 ETH profit
```

### Scenario 2: Debugging High Failure Rate

**Before:** No idea why attempts are failing
```bash
# Read through thousands of log lines
cat targets/protocol/logs/*.jsonl | grep -i "error"
```

**After:** Clear diagnosis
```
🟡 High exploit failure rate

Description: 28 out of 30 attempts failed (93.3%).

Action: Review failure logs to identify common issues. 
        Consider improving exploit templates or hypothesis quality.

Common Patterns:
  - RPC connection timeouts (12 attempts)
  - Invalid function signatures (8 attempts)
  - Insufficient gas (5 attempts)
  - Revert: access control (3 attempts)
```

### Scenario 3: Multi-Protocol Dashboard

Track all your active bug bounties:

```bash
# Generate insights for all protocols
python secbrain/examples/generate_insights_dashboard.py
```

**Output:**
```
Found 5 workspace(s)

📊 Analyzing protocol1...
  Status: requires_attention
  Critical: 2, High: 1

📊 Analyzing protocol2...
  Status: healthy
  Critical: 0, High: 0

📊 Analyzing protocol3...
  Status: review_recommended
  Critical: 0, High: 3

============================================================
CONSOLIDATED DASHBOARD
============================================================

📈 Overall Status:
  🔴 Requires Attention: 2 protocols
  🟡 Review Recommended: 2 protocols
  🟢 Healthy: 1 protocol

⚠️ Issues:
  Critical: 4 total
  High: 7 total

🎯 Top Priorities:
  1. protocol1: 2 critical, 1 high (compilation issues)
  2. protocol4: 1 critical, 3 high (exploit failures)
  3. protocol3: 0 critical, 3 high (hypothesis quality)
  4. protocol5: 1 critical, 0 high (missing API keys)
  5. protocol2: 0 critical, 0 high (healthy!)

✓ Consolidated dashboard saved to insights-dashboard.json
```

## Integration Examples

### Daily Workflow

**Morning routine:**
```bash
#!/bin/bash
# morning-check.sh

# Generate fresh insights for all active protocols
for workspace in targets/*/; do
    protocol=$(basename "$workspace")
    echo "Checking $protocol..."
    
    secbrain insights \
        -w "$workspace" \
        -f html \
        -o "daily-reports/$(date +%Y-%m-%d)"
done

# Open critical issues
find daily-reports/$(date +%Y-%m-%d) -name "*.html" \
    -exec grep -l "🔴 Critical" {} \; \
    | xargs open
```

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: Generate Insights
  run: secbrain insights -w ./targets/protocol -f all -o ./reports

- name: Check for Critical Issues
  run: |
    if grep -q '"critical_count": [1-9]' reports/*.json; then
      echo "::error::Critical security issues found!"
      exit 1
    fi
```

### Slack Notifications

**Send daily digest:**
```python
import json
from slack_sdk import WebClient

# Generate insights
from secbrain.insights import InsightsAggregator, InsightsAnalyzer

data = InsightsAggregator("./targets/protocol").aggregate()
results = InsightsAnalyzer().analyze(data)

# Send to Slack
client = WebClient(token=os.environ["SLACK_TOKEN"])
message = f"""
*SecBrain Daily Insights*

Status: {results.summary['status']}
Critical: {results.summary['critical_count']}
High: {results.summary['high_count']}

Next Action: {results.summary['next_action']}
"""

client.chat_postMessage(channel="#security", text=message)
```

## Before vs After Comparison

| Task | Before | After |
|------|--------|-------|
| Find critical issues | Manual grep through logs (30+ min) | One command, clear report (30 sec) |
| Check exploit success | Parse 100+ JSON files | Automatic highlight in report |
| Understand failures | Read thousands of log lines | Categorized failure analysis |
| Track progress | Manual spreadsheet | JSON metrics tracking |
| Share with team | Copy-paste from terminal | Beautiful HTML report |
| Prioritize work | Gut feeling | Data-driven priorities |

## Benefits for Bug Bounty Hunters

### Time Savings
- **Before:** 1-2 hours analyzing logs per protocol
- **After:** 5 minutes to generate and review insights
- **Savings:** 90%+ time reduction

### Better Decisions
- **Before:** Might miss critical issues in noise
- **After:** Critical issues highlighted prominently
- **Result:** Higher success rate

### Multi-Protocol Management
- **Before:** Can realistically track 2-3 protocols
- **After:** Can track 10+ protocols with dashboard
- **Result:** More opportunities

### Professional Reports
- **Before:** Manual report writing
- **After:** Automated report generation
- **Result:** Faster submissions

## Tips for Maximum Value

1. **Run insights after every SecBrain run** - Get immediate feedback
2. **Save JSON reports daily** - Track trends over time
3. **Focus on critical first** - Don't get overwhelmed
4. **Use the dashboard for multiple targets** - See the big picture
5. **Automate with GitHub Actions** - Continuous monitoring
6. **Share HTML reports** - Great for team collaboration
7. **Track metrics** - Measure your improvement

## Conclusion

The insights system transforms SecBrain from a data generator into an actionable security research assistant. Instead of drowning in JSON files, you get:

✅ **Clear priorities** - Know what to work on next
✅ **Actionable steps** - Know exactly how to fix issues
✅ **Success tracking** - See your progress over time
✅ **Professional reports** - Share results easily
✅ **Multi-protocol view** - Manage all your work in one place

**Bottom line:** Spend less time analyzing data, more time finding vulnerabilities.

---

## Try It Now

```bash
# 1. Run SecBrain (if you haven't already)
secbrain run --workspace ./targets/test --dry-run

# 2. Generate insights
secbrain insights --workspace ./targets/test --format html --open

# 3. See the magic! 🎉
```

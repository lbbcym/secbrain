# Using SecBrain Insights for Actionable Security Research

## Overview

The SecBrain Insights system transforms raw workflow data into actionable reports that help you prioritize your security research work. Instead of digging through JSON logs, you get clear recommendations on what to do next.

## Quick Start

### Generate an insights report

```bash
# Basic usage - generates markdown report
secbrain insights --workspace ./targets/originprotocol

# Generate HTML report and open in browser
secbrain insights --workspace ./targets/originprotocol --format html --open

# Generate all formats
secbrain insights --workspace ./targets/originprotocol --format all --output ./reports
```

## What You Get

### 1. Executive Summary
- **Overall Status**: Requires Attention / Review Recommended / Healthy
- **Critical Issues Count**: Number of issues that need immediate action
- **High Priority Count**: Items to address soon
- **Next Action**: Clear recommendation for what to do next

### 2. Key Metrics
- Total runs and success rate
- Hypotheses generated
- Exploitation attempts made
- Performance metrics

### 3. Categorized Insights

Insights are organized by category:
- **Reconnaissance**: Issues with contract compilation, asset discovery
- **Hypothesis Generation**: Problems generating vulnerability hypotheses
- **Exploitation**: Exploit attempt results, failures, and successes
- **Performance**: Slow runs, bottlenecks
- **Security**: Learnings and patterns from previous runs

Each insight includes:
- **Priority**: Critical, High, Medium, or Low
- **Title**: Clear problem statement
- **Description**: Context and details
- **Action**: Specific next steps

### 4. Top Recommendations

Prioritized list of actions to take, ordered by criticality.

## Example Workflow

### 1. Run SecBrain on a target

```bash
secbrain run \
  --scope ./targets/myprotocol/scope.yaml \
  --program ./targets/myprotocol/program.json \
  --workspace ./targets/myprotocol \
  --rpc-url https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY \
  --block-number 18000000
```

### 2. Generate insights

```bash
secbrain insights \
  --workspace ./targets/myprotocol \
  --format html \
  --output ./reports \
  --open
```

### 3. Review the report

The HTML report will open in your browser, showing:

**Example Critical Issue:**
```
🔴 No contracts compiled successfully

Description: Cannot proceed with security analysis without compiled contracts.

Action Required: Ensure Foundry is installed and the project compiles. 
Run 'forge build' in the instascope directory.
```

### 4. Take action

Based on the insights:

```bash
# If contracts didn't compile
cd targets/myprotocol/instascope
forge install
forge build

# Re-run SecBrain
cd ../../..
secbrain run --workspace ./targets/myprotocol [same options as before]
```

### 5. Check progress

```bash
# Generate new insights to see if issues are resolved
secbrain insights --workspace ./targets/myprotocol --format html --open
```

## Common Insights and Solutions

### "No contracts compiled successfully"
**Priority:** Critical  
**Solution:**
1. Navigate to the instascope directory
2. Run `forge install` to install dependencies
3. Run `forge build` to compile contracts
4. Check for compilation errors in `foundry.toml`

### "No hypotheses generated"
**Priority:** Critical  
**Solution:**
1. Ensure recon phase completed successfully
2. Check that contracts compiled
3. Verify API keys are set (PERPLEXITY_API_KEY, GOOGLE_API_KEY)
4. Review logs for errors in hypothesis generation

### "N hypotheses missing concrete targets"
**Priority:** Medium  
**Solution:**
1. Review the generated hypotheses in `phases/hypothesis.json`
2. Improve the scope configuration with more specific targets
3. Add more detailed contract information to the scope

### "High exploit failure rate"
**Priority:** Medium  
**Solution:**
1. Review failure logs in `logs/` directory
2. Check RPC connection and block number
3. Verify exploit templates are correct
4. Consider adjusting exploit parameters

### "🎯 N profitable exploit(s) found!"
**Priority:** Critical (Good news!)  
**Action:**
1. Review exploit code in `exploit_attempts/*/` directories
2. Verify the exploits are valid
3. Document the vulnerabilities
4. Prepare reports for bug bounty submission
5. Use the reporting agent to generate professional reports

## Using Insights for Bug Bounty Work

### Daily Workflow

1. **Morning**: Generate insights for all active targets
   ```bash
   for target in targets/*/; do
     secbrain insights --workspace "$target" --format html --output ./daily-reports
   done
   ```

2. **Review**: Open HTML reports and prioritize based on:
   - Critical issues first (show-stoppers)
   - Profitable exploits (potential bounties!)
   - High priority items (optimization opportunities)

3. **Work**: Address top 3-5 recommendations

4. **Evening**: Re-run workflows after fixes, generate new insights

### Weekly Review

```bash
# Generate comprehensive reports for all targets
secbrain insights --workspace ./targets/protocol1 --format all --output ./weekly-review
secbrain insights --workspace ./targets/protocol2 --format all --output ./weekly-review
secbrain insights --workspace ./targets/protocol3 --format all --output ./weekly-review

# Compare metrics over time using JSON exports
# Track: success rate, hypothesis quality, exploit success rate
```

## Output Formats

### Markdown (.md)
- Best for: Documentation, GitHub, version control
- Use when: Sharing with team, tracking in git
- Command: `--format markdown`

### HTML (.html)
- Best for: Reading, presenting, screenshots
- Use when: Daily review, sharing with stakeholders
- Command: `--format html --open`

### JSON (.json)
- Best for: Automation, metrics tracking, dashboards
- Use when: Building custom tools, tracking trends
- Command: `--format json`

### CSV (.csv)
- Best for: Spreadsheet analysis, filtering, sorting
- Use when: Tracking multiple targets, creating reports
- Command: `--format csv`

## Integration with CI/CD

Add insights generation to your GitHub Actions workflow:

```yaml
- name: Generate Insights Report
  if: always()
  run: |
    secbrain insights \
      --workspace ./targets/${{ matrix.protocol }} \
      --format all \
      --output ./insights-reports

- name: Upload Insights
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: insights-reports
    path: ./insights-reports/*.html
```

## Advanced Usage

### Analyzing Multiple Workspaces

```python
from secbrain.insights import InsightsAggregator, InsightsAnalyzer, InsightsReporter

workspaces = [
    "./targets/protocol1",
    "./targets/protocol2",
    "./targets/protocol3",
]

for workspace in workspaces:
    aggregator = InsightsAggregator(workspace)
    data = aggregator.aggregate()
    
    analyzer = InsightsAnalyzer()
    results = analyzer.analyze(data)
    
    reporter = InsightsReporter("./reports")
    reporter.save_report(results, format="html")
```

### Custom Analysis

```python
from secbrain.insights import InsightsAggregator, InsightsAnalyzer

aggregator = InsightsAggregator("./targets/myprotocol")
data = aggregator.aggregate()

# Access raw data
print(f"Total runs: {data.total_runs}")
print(f"Successful: {data.successful_runs}")
print(f"Hypotheses: {data.total_hypotheses}")

# Custom analysis
analyzer = InsightsAnalyzer()
results = analyzer.analyze(data)

# Filter insights
critical = results.get_critical_insights()
recon_insights = results.get_by_category("reconnaissance")

# Access metrics
print(f"Success rate: {results.metrics['success_rate']:.1f}%")
```

## Tips and Tricks

### 1. Automate with Shell Scripts

Create `generate-insights.sh`:
```bash
#!/bin/bash
for workspace in targets/*/; do
    protocol=$(basename "$workspace")
    echo "Generating insights for $protocol..."
    secbrain insights \
        --workspace "$workspace" \
        --format all \
        --output "./reports/$protocol"
done
```

### 2. Track Trends

Save JSON reports with timestamps and compare:
```bash
secbrain insights --workspace ./targets/protocol1 \
    --format json \
    --output ./metrics/$(date +%Y-%m-%d)
```

### 3. Focus on Exploits

Filter the HTML report to show only exploitation insights:
```python
from secbrain.insights import InsightsAggregator, InsightsAnalyzer

data = InsightsAggregator("./targets/protocol").aggregate()
results = InsightsAnalyzer().analyze(data)

# Get only exploitation insights
exploit_insights = results.get_by_category("exploitation")
for insight in exploit_insights:
    print(f"{insight.priority}: {insight.title}")
    print(f"  → {insight.action}")
```

### 4. Email Daily Digest

```bash
# Cron job: Generate and email insights daily
#!/bin/bash
secbrain insights --workspace ./targets/protocol1 --format html > /tmp/report.html
mail -s "SecBrain Daily Insights" -a /tmp/report.html you@example.com < /dev/null
```

## Troubleshooting

### "Workspace path does not exist"
- Ensure you're pointing to a valid SecBrain workspace
- Workspace should contain files like `run_summary.json`, `learnings/`, `phases/`

### "No data found"
- Run SecBrain at least once to generate data
- Check that the run completed (even if with errors)

### "No insights generated"
- This means your workspace is healthy! 
- You'll still get a report with metrics and summary

## Next Steps

1. **Generate your first report**: `secbrain insights --workspace ./targets/test --format html --open`
2. **Review the recommendations**: Focus on critical and high priority items
3. **Take action**: Address the top issues
4. **Re-run and compare**: See how your changes improved the metrics
5. **Automate**: Add insights generation to your daily workflow

## Support

For issues or questions:
- Check the main SecBrain documentation
- Review example workspaces in `targets/`
- Open an issue on GitHub with the `insights` label

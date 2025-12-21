# SecBrain Insights - Quick Reference

## One-Line Commands

```bash
# Generate HTML report and view it
secbrain insights -w ./targets/protocol1 -f html --open

# Generate all formats for multiple protocols
for dir in targets/*/; do secbrain insights -w "$dir" -f all -o ./reports; done

# Quick markdown check
secbrain insights -w ./targets/protocol1
```

## Priority Levels

| Icon | Level | Meaning | Action Timeline |
|------|-------|---------|----------------|
| 🔴 | Critical | Blocking issues | Fix immediately |
| 🟠 | High | Important problems | Fix within 1 day |
| 🟡 | Medium | Optimization opportunities | Fix within 1 week |
| ⚪ | Low | Nice to have | Fix when convenient |

## Common Insights

| Insight | Category | Typical Fix |
|---------|----------|-------------|
| No contracts compiled | Recon | Run `forge build` in instascope/ |
| No hypotheses generated | Hypothesis | Fix compilation, check API keys |
| High exploit failure rate | Exploitation | Review logs, check RPC connection |
| Missing concrete targets | Hypothesis | Improve scope configuration |
| Profitable exploits found | Exploitation | 🎉 Validate and report! |

## Output Formats

| Format | Best For | Extension |
|--------|----------|-----------|
| Markdown | Documentation, Git | `.md` |
| HTML | Daily review, Screenshots | `.html` |
| JSON | Automation, Dashboards | `.json` |
| CSV | Spreadsheets, Analysis | `.csv` |

## Integration Examples

### Daily Check Script

```bash
#!/bin/bash
# daily-insights.sh
TODAY=$(date +%Y-%m-%d)

for workspace in targets/*/; do
    protocol=$(basename "$workspace")
    secbrain insights \
        -w "$workspace" \
        -f html \
        -o "reports/$TODAY/$protocol"
done

# Open summary
open "reports/$TODAY/*/insights_report_*.html"
```

### Pre-Commit Hook

```bash
# .git/hooks/pre-push
#!/bin/bash
secbrain insights -w ./targets/active-protocol -f markdown > /tmp/insights.md
if grep -q "🔴 CRITICAL" /tmp/insights.md; then
    echo "Critical issues found! Review insights before pushing."
    cat /tmp/insights.md
    exit 1
fi
```

### GitHub Actions

```yaml
- name: Generate Insights
  run: |
    secbrain insights -w ./targets/protocol -f all -o ./reports
    
- name: Upload Reports
  uses: actions/upload-artifact@v4
  with:
    name: insights-reports
    path: reports/*.html
```

## Programmatic Usage

```python
from secbrain.insights import InsightsAggregator, InsightsAnalyzer, InsightsReporter

# Load and analyze
aggregator = InsightsAggregator("./targets/protocol1")
data = aggregator.aggregate()

analyzer = InsightsAnalyzer()
results = analyzer.analyze(data)

# Check status
if results.summary["status"] == "requires_attention":
    print("⚠️  Critical issues found!")
    for insight in results.get_critical_insights():
        print(f"  - {insight.title}")
        print(f"    Action: {insight.action}")

# Generate reports
reporter = InsightsReporter("./output")
reporter.save_all_formats(results)
```

## Metrics Tracking

Track trends over time:

```bash
# Save daily metrics
DATE=$(date +%Y-%m-%d)
secbrain insights -w ./targets/protocol -f json -o ./metrics/$DATE

# Compare trends (with jq)
jq '.metrics.success_rate' ./metrics/*/insights_report_*.json
```

## Tips

1. **Run after every workflow**: Get immediate feedback
2. **Focus on critical first**: Don't get overwhelmed
3. **Track trends**: Save JSON reports to see progress
4. **Automate**: Add to CI/CD for continuous monitoring
5. **Share**: HTML reports are great for stakeholders

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Workspace path does not exist" | Point to SecBrain workspace with run_summary.json |
| "No insights generated" | Good news! Workspace is healthy |
| Reports are empty | Run SecBrain at least once to generate data |
| Missing dependencies | `cd secbrain && pip install -e .` |

## See Also

- [Full Insights Guide](../docs/INSIGHTS-GUIDE.md)
- [SecBrain README](../README.md)
- [Example Dashboard Script](generate_insights_dashboard.py)

# Workflow Integration Guide

This document explains how to integrate AI insights from the Copilot Space into your development workflow.

## Quick Start

### 1. Enable Copilot Space

The Copilot Space is automatically active for this repository. No additional setup is required.

### 2. View AI Insights

After each workflow run:

1. Navigate to the Actions tab
2. Click on a completed workflow run
3. Look for the "AI Insights" section in the summary
4. Review recommendations and metrics

### 3. Act on Recommendations

Priority levels:
- 🔴 **Critical**: Address immediately (security, high failure rate)
- 🟡 **High**: Address within 1 week (performance, coverage gaps)
- 🟢 **Medium**: Address when convenient (optimizations)
- ⚪ **Low**: Nice to have (minor improvements)

## Integration Points

### Pre-Commit Checks

Run local validations before committing:

```bash
# Run linting
cd secbrain && ruff check .

# Run type checking
cd secbrain && mypy secbrain

# Run tests with coverage
cd secbrain && pytest tests/ -v --cov=secbrain --cov-report=term-missing
```

### Pull Request Reviews

The Copilot Space automatically comments on PRs with:

- Coverage analysis for changed files
- Performance impact estimates
- Potential failure risks
- Optimization suggestions

### Issue Creation

The following issues are automatically created:

- **Coverage Gaps**: When coverage drops below threshold
- **Performance Degradation**: When execution time increases >20%
- **High Failure Rate**: When failures exceed 5%
- **Artifact Bloat**: When artifact size grows significantly

## AI-Powered Commands

### In Pull Requests

Comment with these commands to trigger specific analyses:

```
/copilot analyze coverage
/copilot analyze performance
/copilot suggest optimizations
/copilot compare to baseline
```

### In GitHub Copilot Chat

Use these prompts for insights:

```
@workspace What are the current test coverage gaps?
@workspace Why is the workflow running slow?
@workspace How can I optimize artifact storage?
@workspace What are the common failure patterns?
```

## Interpreting AI Insights

### Test Coverage Analysis

**Example Output**:
```
## Test Coverage Analysis

Overall Coverage: 65%
Change from previous: +2%
Status: ✅ Above threshold (60%)

Areas Needing Attention:
- secbrain/agents/contract_agent.py: 45% (target: 60%)
- secbrain/tools/foundry.py: 52% (target: 60%)

Recommendations:
1. Add tests for error handling in contract_agent.py
2. Test edge cases in foundry.py tool initialization
3. Add integration tests for agent-tool interaction
```

**Action Items**:
- Prioritize files below threshold
- Focus on untested error paths
- Add integration tests as suggested

### Execution Time Analysis

**Example Output**:
```
## Execution Time Analysis

Latest run: 45s
Average (last 30): 38s
Trend: ⚠️ Increasing

Bottlenecks:
1. Install dependencies: 18s (40%)
2. Run tests: 12s (27%)
3. Type checking: 8s (18%)

Optimization Opportunities:
- Enable pip caching (save ~10s)
- Parallelize type checking and linting (save ~5s)
```

**Action Items**:
- Implement suggested caching
- Consider job parallelization
- Monitor trend for further degradation

### Failure Trend Analysis

**Example Output**:
```
## Failure Trend Analysis

Failure Rate: 8% (⚠️ Above target of 5%)
Trend: Increasing

Top Failure Causes:
1. Import errors (40%)
2. Type checking failures (30%)
3. Test failures (20%)
4. Configuration errors (10%)

Root Causes:
- Missing dependencies in requirements.lock
- Recent refactoring broke type hints
- Flaky test: test_contract_recon_async

Preventive Measures:
1. Add dependency validation in pre-commit
2. Enable mypy in IDE
3. Fix or mark flaky test
```

**Action Items**:
- Address import errors immediately
- Update type hints
- Stabilize or skip flaky test

### Artifact Optimization

**Example Output**:
```
## Artifact Optimization

Total Storage: 2.3 GB
Unused Artifacts: 65%
Estimated Savings: 1.5 GB (65%)

High Priority Optimizations:
1. Compress log files before upload (save 800 MB)
2. Upload artifacts only on failure (save 600 MB)
3. Reduce retention from 90 to 30 days (save 100 MB)

Quick Win:
Add compression step:
- name: Compress logs
  run: tar -czf logs.tar.gz test_workspace/logs
```

**Action Items**:
- Implement compression for logs
- Add conditional artifact upload
- Adjust retention policies

## Best Practices

### Responding to AI Insights

1. **Review critically**: AI suggestions are helpful but not infallible
2. **Understand context**: Consider your specific use case
3. **Test changes**: Validate optimizations in a branch first
4. **Track impact**: Measure before and after metrics
5. **Share learnings**: Update knowledge bases with findings

### Maintaining Accuracy

1. **Keep knowledge bases current**: Update when workflows change
2. **Provide feedback**: Report inaccurate suggestions
3. **Refine prompts**: Improve task definitions based on results
4. **Monitor trends**: Ensure AI insights align with reality

### Optimizing for AI

1. **Write descriptive commit messages**: Helps AI understand changes
2. **Document workflow changes**: Update knowledge bases
3. **Use consistent naming**: Makes pattern detection easier
4. **Tag appropriately**: Use labels for better categorization

## Customization

### Adjusting Thresholds

Edit task files to change thresholds:

**Coverage threshold** (`.github/copilot/tasks/analyze-test-coverage.yml`):
```yaml
inputs:
  coverage_threshold:
    default: 70  # Increase from 60
```

**Performance alert** (`.github/copilot/tasks/analyze-execution-time.yml`):
```yaml
inputs:
  alert_threshold_minutes:
    default: 3  # Decrease from 5
```

### Custom Analysis

Add custom analysis by creating new task files:

```yaml
name: Custom Analysis
description: Your custom analysis

trigger:
  on_workflow_completion:
    - your-workflow

task:
  steps:
    - name: Your analysis step
      action: ai_analysis
      prompt: |
        Your custom prompt here

outputs:
  your_output:
    description: Your output description
```

## Troubleshooting

### AI Insights Not Appearing

1. Check that the workflow completed successfully
2. Verify the workflow name matches task configuration
3. Review GitHub Actions logs for errors
4. Ensure Copilot is enabled for the repository

### Inaccurate Suggestions

1. Check if knowledge bases are up to date
2. Review AI prompts for clarity
3. Provide feedback to help improve suggestions
4. Consider adjusting task configurations

### Performance Issues

1. Reduce analysis window (fewer runs to analyze)
2. Disable non-critical tasks temporarily
3. Optimize task prompts for efficiency
4. Review GitHub Actions quota

## Getting Help

1. **Documentation**: Review knowledge base files
2. **Examples**: Check existing workflow runs
3. **Community**: Open a discussion
4. **Support**: Create an issue with `copilot-space` label

## Examples

### Implementing a Coverage Improvement

**AI Suggestion**:
```
Add tests for error handling in contract_agent.py
Coverage: 45% → 65% (target: 60%)
```

**Implementation**:
```python
# tests/test_contract_agent.py

def test_contract_agent_handles_missing_config():
    """Test that agent handles missing configuration gracefully."""
    with pytest.raises(ConfigurationError):
        ContractAgent(config=None)

def test_contract_agent_handles_invalid_scope():
    """Test that agent validates scope format."""
    with pytest.raises(ValueError):
        agent = ContractAgent()
        agent.load_scope("invalid.yaml")
```

### Implementing a Performance Optimization

**AI Suggestion**:
```
Enable pip caching to save ~10 seconds
```

**Implementation**:
```yaml
# .github/workflows/contract-audit-ci.yml

- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    cache: 'pip'  # Add this line
    cache-dependency-path: |
      secbrain/pyproject.toml
      secbrain/requirements.lock
```

### Implementing an Artifact Optimization

**AI Suggestion**:
```
Upload logs only on failure to reduce storage
```

**Implementation**:
```yaml
# .github/workflows/contract-audit-ci.yml

- name: Upload logs on failure
  if: failure()  # Add condition
  uses: actions/upload-artifact@v4
  with:
    name: failure-logs
    path: test_workspace/logs/
    retention-days: 7  # Reduce retention
```

## Feedback

Your feedback helps improve AI insights. Please report:

- ✅ Helpful suggestions that worked well
- ❌ Inaccurate or unhelpful suggestions
- 💡 Ideas for new types of analysis
- 🐛 Bugs or issues with the Copilot Space

Create a feedback issue with the `copilot-feedback` label.

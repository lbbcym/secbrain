# SecBrain Copilot Space

## Overview

This Copilot Space is designed to optimize the SecBrain audit workflows using AI-powered insights. It provides automated analysis of test coverage, execution time, failure trends, and artifact management for the contract audit and SOTA coverage CI/CD pipelines.

## Features

### 🎯 Automated Workflow Analysis

The Copilot Space continuously monitors and analyzes workflow runs to provide:

- **Test Coverage Analysis**: Identifies gaps in test coverage and suggests specific tests to add
- **Execution Time Tracking**: Monitors workflow performance and identifies bottlenecks
- **Failure Trend Analysis**: Detects patterns in failures and recommends preventive measures
- **Artifact Optimization**: Analyzes artifact usage and suggests storage optimizations

### 📊 Key Capabilities

1. **Real-time Insights**: Get immediate feedback on workflow performance
2. **Trend Detection**: Identify patterns and trends over time
3. **Actionable Recommendations**: Receive specific, implementable suggestions
4. **Automated Alerts**: Get notified of issues before they become problems

## Structure

```
.github/copilot/
├── space.yml                           # Main Copilot Space configuration
├── README.md                           # This file
├── contract-audit-knowledge.md         # Contract audit workflow knowledge base
├── sota-coverage-knowledge.md          # SOTA coverage workflow knowledge base
└── tasks/
    ├── analyze-test-coverage.yml       # Test coverage analysis task
    ├── analyze-execution-time.yml      # Execution time analysis task
    ├── analyze-failure-trends.yml      # Failure trend analysis task
    └── optimize-artifacts.yml          # Artifact optimization task
```

## Monitored Workflows

### Contract Audit CI
- **File**: `.github/workflows/contract-audit-ci.yml`
- **Purpose**: Main contract audit workflow with linting, type checking, and security tests
- **Key Metrics**:
  - Test coverage (target: >60%)
  - Execution time (target: <40 seconds)
  - Failure rate (target: <5%)

### SOTA Coverage CI
- **File**: `.github/workflows/sota-coverage-ci.yml`
- **Purpose**: State-of-the-art vulnerability coverage testing
- **Key Metrics**:
  - Integration test success rate
  - Security vulnerability count (target: 0 high/critical)
  - Coverage upload success rate

## Using the Copilot Space

### Manual Task Invocation

You can manually invoke any of the analysis tasks through GitHub Copilot:

1. Open GitHub Copilot Chat
2. Reference the task: `@workspace /task analyze-test-coverage`
3. Provide any required inputs
4. Review the generated insights

### Automatic Analysis

Tasks are automatically triggered:

- **After every workflow run**: Test coverage and execution time analysis
- **Weekly (Monday)**: Comprehensive failure trend analysis
- **Weekly (Sunday)**: Artifact optimization review

### Viewing Results

Analysis results are provided through:

- **GitHub Issues**: For actionable items requiring attention
- **PR Comments**: For coverage gaps or optimization suggestions
- **Workflow Summaries**: Embedded in the workflow run page

## Configuration

### Customizing Thresholds

Edit `space.yml` to adjust analysis thresholds:

```yaml
capabilities:
  - id: analyze-test-coverage
    inputs:
      coverage_threshold: 70  # Increase from 60% to 70%
```

### Adding Custom Tasks

Create new task files in the `tasks/` directory following the existing pattern. Tasks should include:

- Clear description and purpose
- Input parameters with defaults
- Analysis steps
- Output definitions
- Success criteria
- Notification rules

## Best Practices

### For Developers

1. **Review AI suggestions** before implementing them blindly
2. **Keep knowledge bases updated** as workflows evolve
3. **Monitor trend reports** to catch issues early
4. **Address high-priority recommendations** promptly

### For Maintainers

1. **Update task definitions** when adding new workflows
2. **Refine prompts** based on the quality of AI responses
3. **Adjust thresholds** based on team goals and capacity
4. **Document workflow changes** in knowledge bases

## Metrics Dashboard

### Coverage Metrics
- Current coverage: Tracked per workflow run
- Coverage trend: 30-day rolling average
- Gap analysis: Files below threshold

### Performance Metrics
- Average execution time: By workflow and step
- Bottleneck identification: Top 5 slowest steps
- Performance trend: Week-over-week comparison

### Quality Metrics
- Failure rate: Overall and by workflow
- Mean time to recovery: Average time to fix failures
- Flaky test detection: Tests with inconsistent results

### Efficiency Metrics
- Artifact storage: Total size and growth rate
- Unused artifacts: Percentage never downloaded
- Cost optimization: Estimated monthly savings

## Troubleshooting

### Task Not Running

**Possible causes**:
- Workflow name mismatch in task configuration
- Missing required inputs
- Trigger conditions not met

**Solutions**:
- Verify workflow names in `space.yml`
- Check task logs for error messages
- Review trigger configuration in task files

### Inaccurate Analysis

**Possible causes**:
- Stale knowledge base information
- AI prompt needs refinement
- Insufficient historical data

**Solutions**:
- Update knowledge base documents
- Refine AI prompts in task files
- Wait for more workflow runs to accumulate

### Missing Notifications

**Possible causes**:
- Notification thresholds not met
- GitHub permissions issues
- Notification configuration errors

**Solutions**:
- Check threshold values in task files
- Verify GitHub App permissions
- Review notification rules

## Contributing

### Updating Knowledge Bases

When making significant changes to workflows:

1. Update the relevant knowledge base file
2. Document new patterns or best practices
3. Add common issues and solutions
4. Update metrics and targets

### Improving AI Tasks

To enhance AI analysis quality:

1. Review generated insights for accuracy
2. Refine prompts to be more specific
3. Add context from knowledge bases
4. Test changes with recent workflow runs

### Adding New Analysis

To add new types of analysis:

1. Create a new task file in `tasks/`
2. Define clear inputs and outputs
3. Write specific AI prompts
4. Add success criteria
5. Configure notifications
6. Update `space.yml` to reference the new task

## Resources

### Documentation
- [GitHub Copilot Spaces Documentation](https://docs.github.com/copilot)
- [GitHub Actions Workflow Syntax](https://docs.github.com/actions/reference/workflow-syntax-for-github-actions)
- [SecBrain Project Documentation](../../../secbrain/README.md)

### Related Files
- Contract Audit Workflow: `.github/workflows/contract-audit-ci.yml`
- SOTA Coverage Workflow: `.github/workflows/sota-coverage-ci.yml`
- Project Configuration: `secbrain/pyproject.toml`

## Support

For issues or questions about the Copilot Space:

1. Check this README and knowledge bases
2. Review task definitions for expected behavior
3. Open a GitHub issue with the `copilot-space` label
4. Tag the repository maintainers

## License

This Copilot Space configuration is part of the SecBrain project and follows the same MIT license.

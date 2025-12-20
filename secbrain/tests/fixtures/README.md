# SOTA Vulnerability Coverage Test Fixtures

This directory contains test fixtures and configurations for the SOTA (State-of-the-Art) Vulnerability Coverage feature.

## Files

- `sota_scope.yaml`: Defines the target scope, authentication, rate limiting, and test configuration.
- `sota_program.json`: Defines the testing workflow, including phases, tools, and safety controls.

## Usage

1. **Running Tests**

   ```bash
   # Run the SOTA coverage tests
   python -m secbrain.cli.secbrain_cli run \
     --scope tests/fixtures/sota_scope.yaml \
     --program tests/fixtures/sota_program.json \
     --workspace sota_workspace
   ```

2. **Dry Run**

   ```bash
   # Perform a dry run to validate the configuration
   python -m secbrain.cli.secbrain_cli run \
     --scope tests/fixtures/sota_scope.yaml \
     --program tests/fixtures/sota_program.json \
     --workspace sota_workspace \
     --dry-run
   ```

## Configuration

### sota_scope.yaml

- `targets`: Define the API endpoints and authentication details.
- `test_config`: Configure test behavior, timeouts, and evidence collection.
- `vulnerability_classes`: List of vulnerability classes to test.

### sota_program.json

- `phases`: Define the testing workflow phases.
- `tools_config`: Configure specific tools and test cases.
- `safety_controls`: Set limits to prevent accidental damage.
- `reporting`: Configure report generation.

## Environment Variables

- `AUTH_TOKEN`: Authentication token for the target API.
- `SLACK_WEBHOOK`: Webhook URL for Slack notifications.

## License

MIT

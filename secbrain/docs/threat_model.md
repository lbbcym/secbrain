# SecBrain Threat Model

## Overview

SecBrain operates in a high-risk environment where malicious targets, compromised tools, or prompt injection could lead to unintended actions. This document outlines the threat landscape and mitigations.

## Threat Categories

### 1. Prompt Injection from Target

**Risk**: Malicious content in target responses (HTTP bodies, headers, error messages) could manipulate agent behavior.

**Attack Vectors**:
- HTML/JS content containing adversarial instructions
- Error messages with embedded prompts
- API responses with injected commands
- Headers with special characters/instructions

**Mitigations**:
- Sanitize all target-sourced content before passing to models
- Use structured data extraction, not raw text
- Limit context window exposure to target data
- Separate "trusted" (config) from "untrusted" (target) inputs
- Advisor review at critical decision points

### 2. Prompt Injection from Tools

**Risk**: Compromised or malicious tools could inject instructions via their output.

**Attack Vectors**:
- Modified tool binaries
- Tools fetching remote payloads
- Tool output with embedded instructions

**Mitigations**:
- Hash verification for known tools
- Sandbox tool execution where possible
- Parse tool output as data, not instructions
- Limit tool selection to allowlist

### 3. Tool Misuse / Overreach

**Risk**: Agents could use tools beyond intended scope or in harmful ways.

**Attack Vectors**:
- Scope creep during exploitation
- Denial of service via excessive requests
- Data exfiltration through HTTP client
- Privilege escalation via recon tools

**Mitigations**:
- **ACLs**: Per-tool, per-phase access control
- **Scope enforcement**: All URLs/hosts validated against scope.yaml
- **Rate limits**: Global and per-tool caps
- **Request auditing**: Every HTTP call logged
- **Human approval**: Required for high-risk actions

### 4. Model Hallucination

**Risk**: Models may generate non-existent vulnerabilities, wrong payloads, or unsafe commands.

**Attack Vectors**:
- False positive vulnerabilities
- Incorrect exploitation techniques
- Invalid tool commands

**Mitigations**:
- Advisor review for critical findings
- Research validation via Perplexity
- Structured output validation
- Human review before submission

### 5. Credential / Secret Exposure

**Risk**: API keys, tokens, or discovered credentials could be logged or transmitted insecurely.

**Attack Vectors**:
- Secrets in logs
- Credentials in tool arguments
- Tokens in HTTP requests

**Mitigations**:
- Secret masking in logs
- Environment-based credential management
- No credential storage in workspace files
- Encrypted storage for discovered secrets

### 6. Denial of Service to Target

**Risk**: Aggressive scanning could impact target availability or trigger bans.

**Attack Vectors**:
- High-frequency requests
- Resource-intensive payloads
- Concurrent tool execution

**Mitigations**:
- Rate limits enforced at tool layer
- Backoff on rate limit responses
- Respect robots.txt and rate limit headers
- Configurable concurrency caps

## Control Framework

### Access Control Lists (ACLs)

```yaml
# config/tools.yaml
tools:
  http_client:
    allowed_methods: [GET, POST, PUT]
    max_body_size: 1MB
    require_approval: [DELETE, PATCH]
  
  subfinder:
    allowed_phases: [recon]
    max_domains: 100
  
  nuclei:
    allowed_templates: [cves/, exposures/]
    blocked_templates: [fuzzing/, dos/]
    require_approval: true
```

### Rate Limits

| Resource | Limit | Window |
|----------|-------|--------|
| HTTP requests | 100 | per minute |
| Perplexity calls | 20 | per run |
| Gemini calls | 10 | per run |
| Tool executions | 50 | per phase |

### Kill-Switch

Three levels of halt:
1. **Soft**: Complete current operation, then stop
2. **Hard**: Immediate halt, may leave state inconsistent
3. **Emergency**: Process termination

Triggered by:
- External file creation
- API signal
- Internal error threshold
- Human intervention

### Human Approval Checkpoints

| Action | Approval Required |
|--------|-------------------|
| Exploit execution | Always |
| Authentication testing | Always |
| Nuclei scan | Template-dependent |
| Scope edge actions | Always |
| Report submission | Always |

## Incident Response

### Detection
- Anomaly detection in logs
- Rate limit breaches
- Scope violation attempts
- Unexpected tool outputs

### Response
1. Trigger kill-switch
2. Preserve logs and state
3. Isolate workspace
4. Review agent decision chain
5. Document and improve controls

## Security Checklist

- [ ] Verify tool binaries before use
- [ ] Review scope.yaml for accuracy
- [ ] Set appropriate rate limits
- [ ] Configure kill-switch file path
- [ ] Test with dry-run first
- [ ] Review logs after each run
- [ ] Keep models and tools updated

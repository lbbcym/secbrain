import json
from pathlib import Path

from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig
from secbrain.tools.http_client import SecBrainHTTPClient


def test_http_client_approval_deny_blocks_and_audits(tmp_path: Path) -> None:
    # Force http_client to require approval via tools.yaml by mutating config after init.
    run_context = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"], allowed_methods=["GET"]),
        program=ProgramConfig(name="Test", platform="Test"),
        approval_mode="deny",
        approval_audit_log=tmp_path / "audit.jsonl",
    )

    acl = run_context.tools_config.acls.get("http_client")
    if acl is None:
        raise AssertionError("tools.yaml missing http_client acl")
    acl.require_approval = True

    client = SecBrainHTTPClient(run_context)

    # This should be blocked before any network call by approval_mode=deny.
    resp = __import__("asyncio").run(client.get("https://example.com"))
    assert resp.success is False
    assert resp.status_code == 0
    assert resp.error is not None
    assert "Approval denied" in resp.error

    audit_path = tmp_path / "audit.jsonl"
    assert audit_path.exists()

    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1

    entry = json.loads(lines[-1])
    assert entry["request"]["tool_name"] == "http_client"
    assert entry["response"]["approved"] is False

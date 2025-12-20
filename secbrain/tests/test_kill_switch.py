from pathlib import Path

from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig


def test_kill_switch_file_trips_flag(tmp_path: Path) -> None:
    kill_file = tmp_path / "kill"
    kill_file.write_text("stop", encoding="utf-8")

    ctx = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"]),
        program=ProgramConfig(name="Test"),
        kill_switch_file=kill_file,
    )

    assert ctx.is_killed() is True


def test_kill_switch_manual_trigger(tmp_path: Path) -> None:
    ctx = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"]),
        program=ProgramConfig(name="Test"),
    )

    assert ctx.is_killed() is False
    ctx.kill()
    assert ctx.is_killed() is True

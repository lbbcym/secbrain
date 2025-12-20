from pathlib import Path

import pytest

from secbrain.core.validation import (
    ValidationError,
    validate_environment,
    validate_program_file,
    validate_scope_file,
    validate_tools_on_path,
)


def test_scope_requires_targets(tmp_path: Path) -> None:
    scope_file = tmp_path / "scope.yaml"
    scope_file.write_text("domains: []\nurls: []\nips: []\ncontracts: []\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_scope_file(scope_file)


def test_program_requires_name(tmp_path: Path) -> None:
    program_file = tmp_path / "program.json"
    program_file.write_text("{}", encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_program_file(program_file)


def test_validate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_KEY", raising=False)
    with pytest.raises(ValidationError):
        validate_environment(["MISSING_KEY"])

    monkeypatch.setenv("PRESENT_KEY", "1")
    assert validate_environment(["PRESENT_KEY"]) == ["PRESENT_KEY"]


def test_validate_tools_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    # Use a tool that should exist on CI (python) and one that likely doesn't.
    validate_tools_on_path(["python"])

    with pytest.raises(ValidationError):
        validate_tools_on_path(["definitely-not-a-real-tool-name-xyz"])

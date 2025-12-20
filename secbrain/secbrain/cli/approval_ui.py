from __future__ import annotations

import asyncio

from rich.console import Console

from secbrain.core.approval import ApprovalRequest

_console = Console()


async def interactive_approval_prompt(req: ApprovalRequest) -> tuple[bool, str | None]:
    _console.print("\n[bold yellow]APPROVAL REQUIRED[/]")
    _console.print(f"Tool: {req.tool_name}")
    _console.print(f"Risk: [bold]{req.risk_level}[/]")
    _console.print(f"Operation: {req.operation}")
    _console.print("\n[A]pprove / [D]eny")

    choice = await asyncio.to_thread(input, "> ")
    choice = (choice or "").strip().lower()

    if choice.startswith("a"):
        return True, "approved"
    return False, "denied"

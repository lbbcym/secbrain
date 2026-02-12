"""Interactive CLI approval prompt for high-risk operations.

Presents tool name, risk level, and operation details to the operator
and waits for an approve/deny response via stdin.
"""

from __future__ import annotations

import asyncio

from rich.console import Console

from secbrain.core.approval import ApprovalRequest

_console = Console()


async def interactive_approval_prompt(req: ApprovalRequest) -> tuple[bool, str | None]:
    """Display an approval prompt and return the operator's decision.

    Args:
        req: The approval request containing tool name, risk level, and operation.

    Returns:
        A tuple of (approved, reason) where approved is True if the operator
        chose to approve and reason is a short string describing the decision.
    """
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

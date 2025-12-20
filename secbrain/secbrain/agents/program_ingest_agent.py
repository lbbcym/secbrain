"""Program ingest agent - reads and normalizes program/scope configuration."""

from __future__ import annotations

from typing import Any

from secbrain.agents.base import AgentResult, BaseAgent


class ProgramIngestAgent(BaseAgent):
    """
    Program ingest agent.

    Responsibilities:
    - Reads program/scope config
    - Normalizes rules
    - Calls research to fetch related writeups and constraints
    """

    name = "program_ingest"
    phase = "ingest"

    async def run(self, **kwargs: Any) -> AgentResult:
        """Ingest and analyze the program configuration."""
        self._log("starting_ingest")

        if self._check_kill_switch():
            return self._failure("Kill-switch activated")

        # Extract scope and program info
        scope = self.run_context.scope
        program = self.run_context.program

        # Normalize and validate
        normalized_data = await self._normalize_config(scope, program)

        # Research related writeups if research client is available
        research_data = {}
        if self.research_client and program.name != "unknown":
            research_data = await self._research_program(program)

        # Store results
        if self.storage:
            await self.storage.start_run(
                scope_hash=self._hash_scope(scope),
                metadata={
                    "program_name": program.name,
                    "platform": program.platform,
                    "domains": scope.domains,
                },
            )

        return self._success(
            message="Program ingested successfully",
            data={
                "program_name": program.name,
                "platform": program.platform,
                "domains": scope.domains,
                "urls": scope.urls,
                "focus_areas": program.focus_areas,
                "rules": program.rules,
                "research": research_data,
                "normalized": normalized_data,
            },
            next_actions=["plan"],
        )

    async def _normalize_config(
        self,
        scope: Any,
        program: Any,
    ) -> dict[str, Any]:
        """Normalize scope and program configuration."""
        # Normalize domains (lowercase, remove protocol)
        normalized_domains = []
        for domain in scope.domains:
            d = domain.lower().strip()
            if d.startswith("http://"):
                d = d[7:]
            elif d.startswith("https://"):
                d = d[8:]
            if d.endswith("/"):
                d = d[:-1]
            normalized_domains.append(d)

        # Normalize URLs
        normalized_urls = [url.rstrip("/") for url in scope.urls]

        # Identify target types
        target_types = []
        if normalized_domains:
            target_types.append("web")
        if any("api" in d for d in normalized_domains):
            target_types.append("api")
        if any("mobile" in area.lower() for area in program.focus_areas):
            target_types.append("mobile")

        return {
            "domains": normalized_domains,
            "urls": normalized_urls,
            "target_types": target_types,
            "excluded_paths": scope.excluded_paths,
            "allowed_methods": scope.allowed_methods,
        }

    async def _research_program(self, program: Any) -> dict[str, Any]:
        """Research the program for related writeups and context."""
        research_results = {}

        # Research the target/platform
        if program.platform:
            platform_research = await self._research(
                question=f"What are common vulnerability patterns for {program.platform} bug bounty programs?",
                context=f"Program: {program.name}, Platform: {program.platform}",
            )
            research_results["platform_patterns"] = platform_research

        # Research focus areas
        if program.focus_areas:
            focus_str = ", ".join(program.focus_areas)
            focus_research = await self._research(
                question=f"What testing methodologies are effective for: {focus_str}?",
                context=f"Focus areas for bug bounty: {focus_str}",
            )
            research_results["focus_methodology"] = focus_research

        return research_results

    def _hash_scope(self, scope: Any) -> str:
        """Create a hash of the scope for tracking."""
        import hashlib
        content = f"{sorted(scope.domains)}:{sorted(scope.urls)}:{sorted(scope.excluded_paths)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

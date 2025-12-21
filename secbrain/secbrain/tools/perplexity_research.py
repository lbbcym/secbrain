"""Enhanced Perplexity research integration for SecBrain.

This module provides specialized security research queries with:
- TTL-based intelligent caching
- Strict rate limiting enforcement
- Domain-specific research methods
- Real-world data grounding for decisions
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from secbrain.core.context import RunContext


class PerplexityResearch:
    """
    Enhanced research integration via Perplexity API.

    Features:
    - Specialized security research queries
    - TTL-based caching (1h-168h depending on data type)
    - Strict rate limiting (10 req/min enforced)
    - Real-world data for severity, attacks, market conditions
    - Fallback strategies for API failures

    Used for:
    - Severity assessment with real-world context
    - Attack vector discovery from recent exploits
    - Market condition validation before execution
    - Historical exploit pattern matching
    - Profitability analysis
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "sonar-medium-online",
        max_calls_per_run: int = 50,  # Increased from 20 for intensive research
    ):
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY", "")
        self.model = model
        self.max_calls_per_run = max_calls_per_run
        self._call_count = 0

        # Rate limiting state
        self._request_times: list[float] = []
        self._rate_limit_per_minute = 10
        self._rate_limit_lock = asyncio.Lock()

        # TTL cache state
        self._cache_ttl: dict[str, datetime] = {}
        self._default_ttl = timedelta(hours=24)

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def _cache_key(self, question: str, context: str = "") -> str:
        """Generate cache key for a research query."""
        combined = f"{question}:{context}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    async def _enforce_rate_limit(self) -> None:
        """Enforce 10 requests per minute rate limit with proper concurrency control."""
        async with self._rate_limit_lock:
            now = time.time()
            
            # Remove requests older than 60 seconds
            self._request_times = [
                t for t in self._request_times
                if now - t < 60
            ]
            
            # If at limit, wait for oldest request to age out
            if len(self._request_times) >= self._rate_limit_per_minute:
                wait_time = 60 - (now - self._request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recurse to clean up and check again
                    return await self._enforce_rate_limit()
            
            # Record this request
            self._request_times.append(now)

    def _is_cache_valid(self, cache_key: str, ttl_hours: int) -> bool:
        """Check if cached data is still valid based on TTL."""
        if cache_key not in self._cache_ttl:
            return False
        
        cached_time = self._cache_ttl[cache_key]
        age = datetime.now() - cached_time
        return age < timedelta(hours=ttl_hours)

    async def ask_research(
        self,
        question: str,
        context: str,
        run_context: RunContext,
        ttl_hours: int = 24,
    ) -> dict[str, Any]:
        """
        Ask a research question with TTL-aware caching.

        Args:
            question: The research question
            context: Additional context (target info, phase, etc.)
            run_context: Current run context for caching and limits
            ttl_hours: Cache TTL in hours (default: 24)

        Returns:
            {
                "answer": str,
                "sources": list[str],
                "cached": bool,
                "cache_age_hours": float | None
            }
        """
        # Generate cache key
        cache_key = self._cache_key(question, context)
        
        # Check cache with TTL
        cached = run_context.get_cached_research(cache_key)
        if cached and self._is_cache_valid(cache_key, ttl_hours):
            cache_age = (datetime.now() - self._cache_ttl[cache_key]).total_seconds() / 3600
            return {
                **cached,
                "cached": True,
                "cache_age_hours": cache_age,
            }

        # Check call limits
        if self._call_count >= self.max_calls_per_run:
            return {
                "answer": f"[LIMIT] Research call limit ({self.max_calls_per_run}) reached for this run.",
                "sources": [],
                "cached": False,
                "limited": True,
            }

        # Check dry-run mode
        if run_context.dry_run:
            return {
                "answer": f"[DRY-RUN] Would research: {question[:100]}...",
                "sources": ["dry-run-source"],
                "cached": False,
            }

        # Enforce rate limiting
        await self._enforce_rate_limit()

        # Make the API call
        try:
            self._call_count += 1

            prompt = f"""Context: {context}

Question: {question}

Provide a focused, technical answer relevant to security research and bug bounty hunting. 
Include specific techniques, tools, CVE references, exploit dates, and profit amounts when applicable.
Prioritize data from 2024-2025."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security research assistant specializing in smart contract exploitation and bug bounty hunting. Provide accurate, actionable information with sources and specific data points.",
                    },
                    {"role": "user", "content": prompt},
                ],
            }

            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            sources = data.get("citations", [])

            result = {
                "answer": answer,
                "sources": sources,
                "cached": False,
            }

            # Cache the result with timestamp
            run_context.cache_research(cache_key, result)
            self._cache_ttl[cache_key] = datetime.now()

            return result

        except httpx.HTTPError as e:
            return {
                "answer": f"[ERROR] Research failed: {str(e)}",
                "sources": [],
                "cached": False,
                "error": True,
                "error_detail": str(e),
            }

    # ============================================================
    # SPECIALIZED SECURITY RESEARCH METHODS
    # ============================================================

    async def research_severity_context(
        self,
        vuln_type: str,
        run_context: RunContext,
        details: str = "",
    ) -> dict[str, Any]:
        """
        Research real-world severity assessment for a vulnerability type.

        Returns:
            {
                "answer": str with severity consensus and real examples,
                "sources": list[str],
                "cached": bool
            }

        Cache: 72 hours (severity standards change slowly)
        """
        question = f"""
Current severity assessment for {vuln_type} vulnerabilities in smart contracts (2025 data):

Required information:
1. Security researcher consensus on severity level (Critical/High/Medium/Low)
2. Recent exploit examples from 2024-2025 with:
   - Specific dates
   - Contract names
   - Financial impact in USD
3. Attack success rates and reliability
4. Typical remediation difficulty
5. Detection difficulty and time-to-exploit

{f'Additional context: {details}' if details else ''}

Provide concrete, data-driven assessment with specific examples and amounts.
"""
        
        return await self.ask_research(
            question=question,
            context=f"Severity research for {vuln_type}",
            run_context=run_context,
            ttl_hours=72,  # 3 day cache
        )

    async def research_attack_vectors(
        self,
        vuln_type: str,
        run_context: RunContext,
        contract_pattern: str = "",
    ) -> dict[str, Any]:
        """
        Research successful attack patterns and techniques.

        Returns:
            {
                "answer": str with attack techniques and real exploits,
                "sources": list[str],
                "cached": bool
            }

        Cache: 48 hours (attack patterns evolve moderately fast)
        """
        question = f"""
Successful attack vectors and exploitation techniques for {vuln_type} vulnerabilities in EVM smart contracts:

For each attack pattern, provide:
1. Step-by-step attack technique
2. Real exploit examples from 2024-2025 with:
   - Exact dates
   - Contract names and addresses
   - Transaction hashes (if public)
3. Gas costs in USD
4. Actual profit made (if known)
5. Time to execute (seconds/minutes)
6. Success rate / reliability
7. Detection difficulty and time-to-detect

{f'Contract pattern context: {contract_pattern}' if contract_pattern else ''}

Prioritize recent, successful exploits with verified outcomes.
"""
        
        return await self.ask_research(
            question=question,
            context=f"Attack vector research for {vuln_type}",
            run_context=run_context,
            ttl_hours=48,  # 2 day cache
        )

    async def research_market_conditions(
        self,
        target_protocol: str,
        exploit_type: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """
        Research current market conditions for exploit validation.

        Returns:
            {
                "answer": str with market analysis and timing recommendations,
                "sources": list[str],
                "cached": bool
            }

        Cache: 1 hour (market conditions change rapidly)
        """
        question = f"""
Current market conditions analysis for executing {exploit_type} exploit on {target_protocol}:

Required information:
1. Current TVL and liquidity depth
2. Recent similar exploit attempts (last 30 days) with outcomes
3. Current gas prices and network congestion
4. Active monitoring and response time of protocol team
5. MEV bot competition level for this exploit type
6. Recommended execution timing and conditions
7. Risk factors and detection likelihood
8. Expected profitability range given current market state

Provide actionable intelligence for go/no-go decision.
"""
        
        return await self.ask_research(
            question=question,
            context=f"Market conditions for {target_protocol} {exploit_type}",
            run_context=run_context,
            ttl_hours=1,  # 1 hour cache (market data changes fast)
        )

    # ============================================================
    # BACKWARD COMPATIBILITY METHODS
    # ============================================================

    async def research_technology(
        self,
        technology: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Research common vulnerabilities for a technology."""
        question = f"What are the most common security vulnerabilities and attack vectors for {technology}? Include recent CVEs if applicable."
        context = f"Researching technology: {technology}"
        return await self.ask_research(question, context, run_context)

    async def research_endpoint(
        self,
        endpoint: str,
        method: str,
        parameters: list[str],
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Research vulnerability patterns for an endpoint."""
        question = f"What vulnerability classes should be tested for a {method} endpoint at {endpoint} with parameters: {', '.join(parameters)}?"
        context = f"Endpoint analysis: {method} {endpoint}"
        return await self.ask_research(question, context, run_context)

    async def research_cwe(
        self,
        cwe_id: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Research a specific CWE for exploitation techniques."""
        question = f"How can {cwe_id} be exploited in web applications? What are the best testing techniques and payloads?"
        context = f"CWE research: {cwe_id}"
        return await self.ask_research(question, context, run_context)

    async def research_writeups(
        self,
        target_type: str,
        vuln_class: str,
        run_context: RunContext,
    ) -> dict[str, Any]:
        """Find relevant bug bounty writeups."""
        question = f"Find recent bug bounty writeups about {vuln_class} vulnerabilities in {target_type} applications. What techniques were successful?"
        context = f"Writeup research: {vuln_class} in {target_type}"
        return await self.ask_research(question, context, run_context)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


async def create_research_client(run_context: RunContext) -> PerplexityResearch:
    """Create a research client with run-specific configuration."""
    return PerplexityResearch()

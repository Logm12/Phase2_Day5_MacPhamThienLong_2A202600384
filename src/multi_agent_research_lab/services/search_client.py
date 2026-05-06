"""Search client abstraction for ResearcherAgent."""

import json
import urllib.request
from typing import Any

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        settings = get_settings()
        api_key = settings.tavily_api_key
        if not api_key:
            raise AgentExecutionError("Tavily API key is missing")

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=settings.timeout_seconds) as response:
                res_body = response.read().decode("utf-8")
                res_data: dict[str, Any] = json.loads(res_body)
                results: list[dict[str, Any]] = res_data.get("results", [])

                docs = []
                for item in results:
                    docs.append(
                        SourceDocument(
                            title=item.get("title", ""),
                            url=item.get("url"),
                            snippet=item.get("content", ""),
                        )
                    )
                return docs
        except Exception as e:
            raise AgentExecutionError(f"Tavily search failed: {str(e)}") from e


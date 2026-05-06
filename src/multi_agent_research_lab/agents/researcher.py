"""Researcher agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self.search_client = SearchClient()
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        with trace_span("Researcher Execution", {"query": state.request.query}):
            try:
                docs = self.search_client.search(
                    state.request.query, max_results=state.request.max_sources
                )
                state.sources = docs

                notes_lines = []
                for d in docs:
                    line = f"Title: {d.title}\nURL: {d.url or 'N/A'}\nSnippet: {d.snippet}\n"
                    notes_lines.append(line)
                state.research_notes = "\n".join(notes_lines)
                state.add_trace_event(
                    "researcher_execution", {"status": "search_success", "sources_count": len(docs)}
                )
            except Exception as e:
                system_prompt = (
                    "You are an expert researcher. Since the live web search API failed, "
                    "please use your own extensive internal knowledge to write a detailed, "
                    "structured set of research notes on the given query. "
                    "Include references or sources from your training data where appropriate."
                )
                user_prompt = f"Query: {state.request.query}"

                try:
                    response = self.llm_client.complete(system_prompt, user_prompt)
                    state.research_notes = response.content
                    if response.cost_usd is not None:
                        state.cost_tracker += response.cost_usd
                    state.add_trace_event(
                        "researcher_execution", {"status": "fallback_success", "error": str(e)}
                    )
                except Exception as llm_err:
                    state.research_notes = (
                        f"Failed to gather notes due to search and LLM failure. Error: {llm_err}"
                    )
                    state.add_trace_event(
                        "researcher_execution", {"status": "total_failure", "error": str(llm_err)}
                    )

            return state

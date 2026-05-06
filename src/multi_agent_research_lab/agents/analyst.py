"""Analyst agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        with trace_span("Analyst Execution", {"notes_length": len(state.research_notes or "")}):
            system_prompt = (
                "You are an expert systems analyst. Analyze the following research notes compiled "
                "for the query. Extract key claims, compare viewpoints, synthesize statistics or "
                "technical figures, and organize them into clear structured insights."
            )
            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Research Notes:\n{state.research_notes or 'No research notes available.'}"
            )
            try:
                response = self.llm_client.complete(system_prompt, user_prompt)
                state.analysis_notes = response.content
                if response.cost_usd is not None:
                    state.cost_tracker += response.cost_usd
                state.add_trace_event("analyst_execution", {"status": "success"})
            except Exception as e:
                state.analysis_notes = f"Failed to synthesize analysis due to LLM failure: {e}"
                state.add_trace_event("analyst_execution", {"status": "failure", "error": str(e)})

            return state

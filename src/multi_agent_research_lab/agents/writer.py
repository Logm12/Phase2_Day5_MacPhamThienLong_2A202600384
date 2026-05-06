"""Writer agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        with trace_span("Writer Execution", {"notes_length": len(state.research_notes or "")}):
            system_prompt = (
                "You are a professional technical writer. Write a comprehensive, well-structured "
                "report in Markdown format based on the research notes and analysis notes "
                "provided. Mandatory Citation Requirement: Extract and cite all relevant URLs or "
                "references mentioned in the research notes and place them in a dedicated "
                "section titled '## Tài liệu tham khảo (Citations)' at the very end of the "
                "report."
            )
            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Research Notes:\n{state.research_notes or 'None'}\n"
                f"Analysis Notes:\n{state.analysis_notes or 'None'}"
            )
            try:
                response = self.llm_client.complete(system_prompt, user_prompt)
                state.final_answer = response.content
                if response.cost_usd is not None:
                    state.cost_tracker += response.cost_usd
                state.add_trace_event("writer_execution", {"status": "success"})
            except Exception as e:
                state.final_answer = f"Failed to generate final report due to LLM failure: {e}"
                state.add_trace_event("writer_execution", {"status": "failure", "error": str(e)})

            return state

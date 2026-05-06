"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import AgentRoute, ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        with trace_span("Supervisor Routing", {"iteration": state.iteration}):
            route: AgentRoute
            if state.iteration >= 5:
                route = "WRITER"
            elif not state.research_notes:
                route = "RESEARCHER"
            else:
                system_prompt = (
                    "You are an expert orchestrator supervisor. Your task is to analyze "
                    "the research query and the collected research notes, and decide if we "
                    "need deep analysis ('ANALYST') or if the notes are complete enough "
                    "to write the final answer directly ('WRITER').\n"
                    "Respond with ONLY the word: ANALYST or WRITER. Do not add any explanation."
                )
                user_prompt = (
                    f"Query: {state.request.query}\n"
                    f"Research Notes: {state.research_notes}\n"
                    "Next Step (ANALYST/WRITER):"
                )
                try:
                    response = self.llm_client.complete(system_prompt, user_prompt)
                    content = response.content.strip().upper()
                    if response.cost_usd is not None:
                        state.cost_tracker += response.cost_usd

                    route = "ANALYST" if "ANALYST" in content else "WRITER"
                except Exception:
                    route = "WRITER"

            state.next_step = route
            state.record_route(route)
            state.add_trace_event(
                "supervisor_routing", {"route": route, "iteration": state.iteration}
            )
            return state

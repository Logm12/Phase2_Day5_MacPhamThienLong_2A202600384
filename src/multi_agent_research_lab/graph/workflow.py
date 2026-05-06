from typing import Any

from langgraph.graph import END, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

    def build(self) -> Any:
        """Create a LangGraph graph."""
        builder = StateGraph(ResearchState)

        # Add nodes
        builder.add_node("supervisor", self.supervisor.run)
        builder.add_node("researcher", self.researcher.run)
        builder.add_node("analyst", self.analyst.run)
        builder.add_node("writer", self.writer.run)

        # Set entry point
        builder.set_entry_point("supervisor")

        # Define conditional routing from supervisor
        def route_decision(state: ResearchState) -> str:
            if state.next_step == "RESEARCHER":
                return "researcher"
            elif state.next_step == "ANALYST":
                return "analyst"
            elif state.next_step == "WRITER":
                return "writer"
            else:
                return END

        builder.add_conditional_edges(
            "supervisor",
            route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                END: END,
            },
        )

        # Worker nodes transition back to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", END)

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        app: Any = self.build()
        # invoke can accept a dict or a ResearchState and returns the State type.
        raw_result = app.invoke(state)
        if isinstance(raw_result, dict):
            return ResearchState(**raw_result)
        assert isinstance(raw_result, ResearchState)
        return raw_result


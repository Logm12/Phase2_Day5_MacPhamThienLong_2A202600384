"""Benchmark implementation for single-agent vs multi-agent."""

import json
import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

Runner = Callable[[str], ResearchState]


class JudgeEngine:
    """Automated rubric-based Judge Engine using gpt-5.4-mini."""

    def __init__(self) -> None:
        self.client = LLMClient()
        self.model = "gpt-5.4-mini"

    def evaluate(self, query: str, report: str) -> tuple[float, str]:
        """Evaluate a generated report based on the strict 40-30-30 rubric and AI cliches penalty.

        Returns:
            tuple[float, str]: (quality_score out of 10, rationale)
        """
        system_prompt = (
            "You are an elite, extremely strict academic reviewer and editor.\n"
            "Evaluate the provided Markdown report based on three specific dimensions:\n"
            "1. Information Depth (40% weight): Logic, comprehensiveness, "
            "topic-alignment.\n"
            "2. Structure (30% weight): Flawless Markdown presentation, "
            "readability, hierarchy.\n"
            "3. Citations (30% weight): Explicit list of sources with valid "
            "URLs cited at the end.\n\n"
            "CRITICAL GUARDRAIL (Heavy Penalty):\n"
            "Actively look for and heavily penalize AI-generated cliché phrasing or structures.\n"
            "Examples of clichés: 'delve deep', 'delving', 'testament', "
            "'tapestry', 'in conclusion',\n"
            "'furthermore', 'moreover', 'it is important to note', 'beacon of', 'landscape of'.\n"
            "Academic/natural writing must sound objective, human, and "
            "professional, not robotic.\n\n"
            "You must return your evaluation in strict JSON format. "
            "No extra explanation outside JSON.\n"
            "JSON structure:\n"
            "{\n"
            "  \"score\": <float between 0.0 and 10.0>,\n"
            "  \"rationale\": \"<multi-line detailed explanation of scores for "
            "Depth, Structure, and Citations, including any cliché penalties>\"\n"
            "}"
        )

        user_prompt = (
            f"Research Query: {query}\n\n"
            f"Generated Report:\n{report}"
        )

        try:
            # Call using gpt-5.4-mini
            response = self.client.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model
            )
            content = response.content.strip()

            # Robust JSON extraction
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                score = float(data.get("score", 5.0))
                rationale = str(data.get("rationale", "No rationale provided by Judge."))
                return score, rationale
            else:
                return 5.0, f"Failed to parse JSON from Judge. Raw output: {content[:300]}"
        except Exception as e:
            # Graceful fallback to gpt-4o-mini if gpt-5.4-mini fails
            try:
                response = self.client.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model="gpt-4o-mini"
                )
                content = response.content.strip()
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    score = float(data.get("score", 5.0))
                    rationale = f"[Fallback to gpt-4o-mini] {data.get('rationale', '')}"
                    return score, rationale
            except Exception as fallback_err:
                return 0.0, f"Judge Engine failed: {str(e)} -> Fallback failed: {str(fallback_err)}"
            return 0.0, f"Judge Engine failed: {str(e)}"


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Execute runner, measure latency, track cost, and run JudgeEngine to score the report."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    cost = getattr(state, "cost_tracker", 0.0)

    quality_score = 0.0
    notes = "No report generated."
    if state.final_answer:
        judge = JudgeEngine()
        quality_score, notes = judge.evaluate(query, state.final_answer)

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=cost,
        quality_score=quality_score,
        notes=notes,
    )
    return state, metrics

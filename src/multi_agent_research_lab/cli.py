"""Command-line entrypoint for the lab starter."""

import time
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    console.print("[bold green]Starting single-agent baseline execution...[/bold green]")
    start_time = time.time()

    client = LLMClient()
    system_prompt = (
        "You are a professional research assistant. Write a detailed, comprehensive report "
        "in Markdown."
    )
    user_prompt = f"Please research and write a detailed report on the following topic: {query}"

    try:
        response = client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        state.final_answer = response.content
        latency = time.time() - start_time

        console.print(
            Panel.fit(
                state.final_answer,
                title="Single-Agent Baseline Answer",
                border_style="cyan",
            )
        )
        console.print("[bold cyan]Metrics:[/bold cyan]")
        console.print(f"  Latency: {latency:.2f} seconds")
        console.print(f"  Input Tokens: {response.input_tokens}")
        console.print(f"  Output Tokens: {response.output_tokens}")
        if response.cost_usd is not None:
            console.print(f"  Estimated Cost: ${response.cost_usd:.6f}")
    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]Error running baseline: {str(e)}[/bold red]",
                title="Error",
            )
        )
        raise typer.Exit(code=1) from e


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        with trace_span("Multi-Agent Workflow"):
            result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


def _run_baseline(query: str) -> ResearchState:
    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    client = LLMClient()
    system_prompt = (
        "You are a professional research assistant. Write a detailed, comprehensive report "
        "in Markdown."
    )
    user_prompt = f"Please research and write a detailed report on the following topic: {query}"
    with trace_span("Baseline (Single-Agent)"):
        response = client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        state.final_answer = response.content
        state.cost_tracker = response.cost_usd or 0.0
    return state


def _run_multi_agent(query: str) -> ResearchState:
    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    with trace_span("Multi-Agent Workflow"):
        result = workflow.run(state)
    return result


@app.command("benchmark")
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run comparative benchmark between Baseline and Multi-Agent Workflow."""
    _init()
    console.print(f"[bold green]Starting Benchmark Suite for query: '{query}'[/bold green]")

    import os

    from multi_agent_research_lab.evaluation.benchmark import run_benchmark
    from multi_agent_research_lab.evaluation.report import render_markdown_report

    # 1. Run Baseline
    console.print("\n[bold cyan]1. Executing Baseline (Single-Agent)...[/bold cyan]")
    _, baseline_metrics = run_benchmark(
        run_name="Baseline (Single-Agent)", query=query, runner=_run_baseline
    )

    # 2. Run Multi-Agent Workflow
    console.print("\n[bold cyan]2. Executing Multi-Agent Workflow...[/bold cyan]")
    _, ma_metrics = run_benchmark(
        run_name="Multi-Agent Workflow", query=query, runner=_run_multi_agent
    )

    # 3. Render and Save Report
    console.print("\n[bold green]Generating and saving Performance Report...[/bold green]")
    report_md = render_markdown_report([baseline_metrics, ma_metrics])

    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, "benchmark_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    console.print(f"[bold green]Success! Benchmark Report saved to {report_path}[/bold green]")


if __name__ == "__main__":
    app()

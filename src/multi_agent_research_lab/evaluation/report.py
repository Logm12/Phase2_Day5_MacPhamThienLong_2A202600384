"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown.

    BẮT BUỘC: Có một Bảng so sánh trực tiếp (Comparison Table) nằm ngay trên cùng của file,
    bao gồm các cột: Metric, Baseline (Single-Agent), Multi-Agent Workflow, Difference.
    """
    baseline = next((m for m in metrics if "baseline" in m.run_name.lower()), None)
    multi_agent = next((m for m in metrics if "multi-agent" in m.run_name.lower()), None)

    b_cost = (
        baseline.estimated_cost_usd
        if baseline and baseline.estimated_cost_usd is not None
        else 0.0
    )
    m_cost = (
        multi_agent.estimated_cost_usd
        if multi_agent and multi_agent.estimated_cost_usd is not None
        else 0.0
    )
    diff_cost = m_cost - b_cost

    b_lat = baseline.latency_seconds if baseline else 0.0
    m_lat = multi_agent.latency_seconds if multi_agent else 0.0
    diff_lat = m_lat - b_lat

    b_qual = (
        baseline.quality_score
        if baseline and baseline.quality_score is not None
        else 0.0
    )
    m_qual = (
        multi_agent.quality_score
        if multi_agent and multi_agent.quality_score is not None
        else 0.0
    )
    diff_qual = m_qual - b_qual

    lines = [
        "# Performance Benchmark Report",
        "",
        "## Performance Comparison Table",
        "",
        "| Metric | Baseline (Single-Agent) | Multi-Agent Workflow | Difference |",
        "|---|---:|---:|---:|",
        f"| **Total Cost (USD)** | ${b_cost:.6f} | ${m_cost:.6f} | {diff_cost:+.6f} |",
        f"| **Latency (s)** | {b_lat:.2f}s | {m_lat:.2f}s | {diff_lat:+.2f}s |",
        f"| **Quality Score (/10)** | {b_qual:.1f}/10 | {m_qual:.1f}/10 | {diff_qual:+.1f} |",
        "",
        "## Detailed Runs Breakdown",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]

    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | "
            f"{item.notes} |"
        )

    return "\n".join(lines) + "\n"

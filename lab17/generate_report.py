"""
Generate a Markdown benchmark report from saved results JSON.

Usage:
    python -m lab17.generate_report
    python -m lab17.generate_report --results-dir lab17/results
"""
from __future__ import annotations
import json
import argparse
from pathlib import Path
from datetime import datetime


def generate_report(results_dir: str = "lab17/results") -> str:
    results_path = Path(results_dir)
    bench_file = results_path / "benchmark_results.json"
    token_file = results_path / "token_budget_breakdown.json"

    if not bench_file.exists():
        return "ERROR: benchmark_results.json not found. Run the benchmark first."

    with open(bench_file, encoding="utf-8") as f:
        data = json.load(f)
    with open(token_file, encoding="utf-8") as f:
        token_data = json.load(f)

    summary = data["summary"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Lab 17 – Multi-Memory Agent Benchmark Report",
        f"**Generated:** {now}  ",
        "**Student:** Vo Thanh Chung (2A202600335)  ",
        "",
        "## Architecture Overview",
        "",
        "| Component | Implementation |",
        "|-----------|---------------|",
        "| Short-term | ConversationBufferMemory (in-memory deque, token-aware auto-trim) |",
        "| Long-term | Redis / FakeRedis (user preferences, persistent facts) |",
        "| Episodic | JSON JSONL log (timestamped conversation episodes) |",
        "| Semantic | ChromaDB vector store (cosine similarity retrieval) |",
        "| Router | Keyword-regex intent classifier → selects backend |",
        "| Context Mgmt | 4-level priority eviction (critical > important > normal > background) |",
        "| Graph | LangGraph StateGraph: memory_retrieve → llm_call → memory_store |",
        "",
        "## Benchmark: Memory Agent vs. Baseline (10 Conversations)",
        "",
        "| Conv | Name | Mem Relevance | Base Relevance | Delta | Ctx Util | Hit Rate | Tok Efficiency |",
        "|------|------|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for r in summary:
        delta_str = f"+{r['relevance_delta']:.3f}" if r['relevance_delta'] >= 0 else f"{r['relevance_delta']:.3f}"
        lines.append(
            f"| {r['conv_id']} | {r['name']} | {r['mem_relevance']:.3f} | "
            f"{r['base_relevance']:.3f} | **{delta_str}** | "
            f"{r['mem_context_util']:.2f} | {r['mem_hit_rate']:.2f} | {r['token_efficiency']:.4f} |"
        )

    avg_delta = sum(r["relevance_delta"] for r in summary) / len(summary)
    avg_hit = sum(r["mem_hit_rate"] for r in summary) / len(summary)
    avg_util = sum(r["mem_context_util"] for r in summary) / len(summary)
    avg_mem_rel = sum(r["mem_relevance"] for r in summary) / len(summary)
    avg_base_rel = sum(r["base_relevance"] for r in summary) / len(summary)

    lines += [
        f"| **AVG** | — | **{avg_mem_rel:.3f}** | **{avg_base_rel:.3f}** | "
        f"**{avg_delta:+.3f}** | **{avg_util:.2f}** | **{avg_hit:.2f}** | — |",
        "",
        "**Metrics:**",
        "- **Mem/Base Relevance**: fraction of expected recall keywords found in response (0–1)",
        "- **Delta**: improvement of memory agent over baseline",
        "- **Ctx Util**: fraction of turns where memory context was non-empty",
        "- **Hit Rate**: memory hits / expected recall items",
        "- **Tok Efficiency**: relevance × 1000 / avg_tokens",
        "",
        "## Memory Hit Rate Analysis",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg memory hit rate across all conversations | {token_data['avg_memory_hit_rate_across_convs']:.3f} |",
        f"| Context utilization (avg) | {avg_util:.3f} |",
        f"| Conversations where memory improved relevance | {sum(1 for r in summary if r['relevance_delta'] > 0)} / {len(summary)} |",
        f"| Relevance improvement (memory vs. baseline) | {avg_delta:+.3f} ({'+' if avg_delta>=0 else ''}{avg_delta/max(avg_base_rel,0.001)*100:.1f}%) |",
        "",
        "## Token Budget Breakdown",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Memory agent total tokens | {token_data['memory_agent_total_tokens']:,} |",
        f"| Baseline agent total tokens | {token_data['baseline_agent_total_tokens']:,} |",
        f"| Token overhead (memory vs. baseline) | {token_data['token_overhead_pct']:+.1f}% |",
        "",
        "## Key Findings",
        "",
        f"1. **Relevance improvement**: Memory agent achieved {avg_delta:+.3f} average relevance delta "
        f"({avg_mem_rel:.3f} vs {avg_base_rel:.3f} baseline)",
        f"2. **Memory hit rate**: {token_data['avg_memory_hit_rate_across_convs']:.1%} average hit rate across conversations",
        f"3. **Context utilization**: Memory context was injected in {avg_util:.0%} of turns",
        f"4. **Token overhead**: {token_data['token_overhead_pct']:+.1f}% more tokens for memory agent "
        "(includes retrieved context; justified by relevance gains)",
        "",
        "## Memory Backend Selection by Intent",
        "",
        "| Query Intent | Memory Backend | Example Patterns |",
        "|-------------|---------------|-----------------|",
        "| User preference | Long-term (Redis) | prefer, like, my name, call me |",
        "| Experience recall | Episodic (JSON) | last time, we discussed, remember when |",
        "| Factual recall | Semantic (Chroma) | what did I say, you mentioned, earlier |",
        "| Keyword search | Semantic (Chroma) | find, similar, related |",
        "| Default/context | Short-term (buffer) | all other queries |",
        "",
        "## Context Window Management",
        "",
        "The short-term buffer implements a 4-level priority eviction hierarchy:",
        "",
        "| Priority | Level | Content Type | Eviction Order |",
        "|----------|-------|-------------|----------------|",
        "| 4 | Critical | Emergency/safety info | Last to evict |",
        "| 3 | Important | Agent responses | Second to last |",
        "| 2 | Normal | User messages | Second to evict |",
        "| 1 | Background | System notes | First to evict |",
        "",
        "Auto-trim triggers when buffer exceeds `max_tokens` (default: 2000 tokens).  ",
        "Lowest-priority messages are evicted first, preserving critical context.",
    ]

    report = "\n".join(lines)

    report_path = results_path / "benchmark_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark report")
    parser.add_argument("--results-dir", default="lab17/results")
    args = parser.parse_args()
    report = generate_report(args.results_dir)
    print("\n" + report[:2000] + ("..." if len(report) > 2000 else ""))


if __name__ == "__main__":
    main()

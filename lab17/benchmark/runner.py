"""
Benchmark runner: compare memory agent vs. no-memory (baseline) agent.

Metrics per turn:
  - response_relevance: keyword overlap between expected_recall and response (0–1)
  - context_utilization: whether memory context was non-empty (0|1)
  - memory_hit_rate: memory_hits / expected_hits
  - token_count: tokens used in LLM call
  - memory_type: which backend was queried
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .conversations import BENCHMARK_CONVERSATIONS


@dataclass
class TurnResult:
    conv_id: str
    turn_idx: int
    agent_type: str          # "memory" | "baseline"
    user_input: str
    response: str
    response_relevance: float
    context_utilization: int  # 1 if context was non-empty, else 0
    memory_hit_rate: float
    memory_hits: int
    memory_type: str
    token_count: int
    latency_ms: int


@dataclass
class ConversationResult:
    conv_id: str
    conv_name: str
    agent_type: str
    turns: list[TurnResult] = field(default_factory=list)

    def avg_relevance(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.response_relevance for t in self.turns) / len(self.turns)

    def avg_context_util(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.context_utilization for t in self.turns) / len(self.turns)

    def avg_memory_hit_rate(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.memory_hit_rate for t in self.turns) / len(self.turns)

    def avg_tokens(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.token_count for t in self.turns) / len(self.turns)

    def total_tokens(self) -> int:
        return sum(t.token_count for t in self.turns)


def _relevance_score(response: str, expected_keywords: list[str]) -> float:
    """Keyword overlap metric: fraction of expected keywords found in response."""
    if not expected_keywords:
        return 1.0
    resp_lower = response.lower()
    matched = sum(1 for kw in expected_keywords if kw.lower() in resp_lower)
    return round(matched / len(expected_keywords), 3)


def _build_baseline_llm():
    """Build a stateless LLM (no memory injection) for baseline comparison."""
    import os
    from langchain_core.messages import HumanMessage, SystemMessage

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from langchain_groq import ChatGroq
        llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile", temperature=0.3)
    else:
        openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
        from langchain_openai import ChatOpenAI
        base_url = "https://models.inference.ai.azure.com" if os.getenv("GITHUB_TOKEN") else None
        llm = ChatOpenAI(
            api_key=openai_key,
            model="gpt-4o-mini",
            temperature=0.3,
            **({"base_url": base_url} if base_url else {}),
        )

    def call(user_input: str, history: list[dict]) -> tuple[str, int]:
        msgs = [SystemMessage(content="You are a helpful AI assistant.")]
        msgs += [HumanMessage(content=m["content"]) for m in history if m["role"] == "user"]
        msgs.append(HumanMessage(content=user_input))
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        resp = llm.invoke(msgs)
        text = resp.content if hasattr(resp, "content") else str(resp)
        tokens = len(enc.encode(user_input + text))
        return text, tokens

    return call


def run_benchmark(
    config=None,
    output_dir: str = "lab17/results",
    conversations: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Run the full benchmark: memory agent vs. baseline on all conversations.
    Saves results to JSON and prints a summary table.
    """
    from ..agent.graph import build_memory_agent, MemoryAgentConfig, run_turn

    if conversations is None:
        conversations = BENCHMARK_CONVERSATIONS

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if config is None:
        config = MemoryAgentConfig(session_id="benchmark")

    # Build agents
    memory_graph, _ = build_memory_agent(config)
    baseline_call = _build_baseline_llm()

    all_results: list[ConversationResult] = []
    summary_rows = []

    print(f"\n{'='*70}")
    print("  Lab 17 Benchmark: Multi-Memory Agent vs. Baseline")
    print(f"{'='*70}\n")

    for conv in conversations:
        conv_id = conv["id"]
        conv_name = conv["name"]
        expected_recall = conv.get("expected_recall", [])
        turns_text = conv["turns"]

        # ── Memory agent ─────────────────────────────────────────────────────
        mem_result = ConversationResult(conv_id=conv_id, conv_name=conv_name, agent_type="memory")
        mem_session = {"session_id": f"bench_{conv_id}", "messages": []}

        # ── Baseline agent ───────────────────────────────────────────────────
        base_result = ConversationResult(conv_id=conv_id, conv_name=conv_name, agent_type="baseline")
        base_history: list[dict] = []

        print(f"[{conv_id}] {conv_name}")

        for i, user_input in enumerate(turns_text):
            # Memory agent turn
            t0 = time.time()
            mem_state = run_turn(memory_graph, mem_session, user_input)
            mem_latency = int((time.time() - t0) * 1000)

            mem_response = mem_state.get("response", "")
            mem_context = mem_state.get("memory_context", "")
            mem_hits = mem_state.get("memory_hits", 0)
            mem_tokens = mem_state.get("token_count", 0)
            mem_type = mem_state.get("memory_type", "short_term")

            # Only score relevance on recall turn (last turn)
            is_recall_turn = (i == len(turns_text) - 1)
            relevance_kws = expected_recall if is_recall_turn else []
            mem_relevance = _relevance_score(mem_response, relevance_kws)

            mem_result.turns.append(TurnResult(
                conv_id=conv_id,
                turn_idx=i,
                agent_type="memory",
                user_input=user_input,
                response=mem_response,
                response_relevance=mem_relevance,
                context_utilization=1 if mem_context.strip() else 0,
                memory_hit_rate=min(mem_hits / max(len(expected_recall), 1), 1.0),
                memory_hits=mem_hits,
                memory_type=mem_type,
                token_count=mem_tokens,
                latency_ms=mem_latency,
            ))

            # Baseline agent turn
            t0 = time.time()
            base_response, base_tokens = baseline_call(user_input, base_history)
            base_latency = int((time.time() - t0) * 1000)
            base_history.append({"role": "user", "content": user_input})
            base_history.append({"role": "assistant", "content": base_response})

            base_relevance = _relevance_score(base_response, relevance_kws)

            base_result.turns.append(TurnResult(
                conv_id=conv_id,
                turn_idx=i,
                agent_type="baseline",
                user_input=user_input,
                response=base_response,
                response_relevance=base_relevance,
                context_utilization=0,
                memory_hit_rate=0.0,
                memory_hits=0,
                memory_type="none",
                token_count=base_tokens,
                latency_ms=base_latency,
            ))

            print(f"  Turn {i+1}: [{mem_type}] mem_hits={mem_hits} | "
                  f"mem_relevance={mem_relevance:.2f} base_relevance={base_relevance:.2f} | "
                  f"tokens={mem_tokens}")

        all_results.extend([mem_result, base_result])

        # Summary row for this conversation
        summary_rows.append({
            "conv_id": conv_id,
            "name": conv_name,
            "mem_relevance": round(mem_result.avg_relevance(), 3),
            "base_relevance": round(base_result.avg_relevance(), 3),
            "relevance_delta": round(mem_result.avg_relevance() - base_result.avg_relevance(), 3),
            "mem_context_util": round(mem_result.avg_context_util(), 3),
            "mem_hit_rate": round(mem_result.avg_memory_hit_rate(), 3),
            "mem_tokens_avg": round(mem_result.avg_tokens(), 1),
            "base_tokens_avg": round(base_result.avg_tokens(), 1),
            "token_efficiency": round(
                mem_result.avg_relevance() / max(mem_result.avg_tokens(), 1) * 1000, 4
            ),
        })

        print()

    # ── Save results ──────────────────────────────────────────────────────────
    raw_data = {
        "conversations": [
            {
                "conv_id": r.conv_id,
                "name": r.conv_name,
                "agent_type": r.agent_type,
                "turns": [asdict(t) for t in r.turns],
                "summary": {
                    "avg_relevance": r.avg_relevance(),
                    "avg_context_util": r.avg_context_util(),
                    "avg_memory_hit_rate": r.avg_memory_hit_rate(),
                    "avg_tokens": r.avg_tokens(),
                    "total_tokens": r.total_tokens(),
                },
            }
            for r in all_results
        ],
        "summary": summary_rows,
    }

    with open(output_path / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    # ── Print summary table ───────────────────────────────────────────────────
    _print_summary(summary_rows)

    # ── Memory hit rate analysis ──────────────────────────────────────────────
    mem_hit_rates = [r["mem_hit_rate"] for r in summary_rows]
    avg_hit_rate = sum(mem_hit_rates) / len(mem_hit_rates) if mem_hit_rates else 0

    # ── Token budget breakdown ────────────────────────────────────────────────
    mem_results = [r for r in all_results if r.agent_type == "memory"]
    base_results = [r for r in all_results if r.agent_type == "baseline"]
    total_mem_tokens = sum(r.total_tokens() for r in mem_results)
    total_base_tokens = sum(r.total_tokens() for r in base_results)

    token_breakdown = {
        "memory_agent_total_tokens": total_mem_tokens,
        "baseline_agent_total_tokens": total_base_tokens,
        "token_overhead_pct": round(
            (total_mem_tokens - total_base_tokens) / max(total_base_tokens, 1) * 100, 1
        ),
        "avg_memory_hit_rate_across_convs": round(avg_hit_rate, 3),
    }

    with open(output_path / "token_budget_breakdown.json", "w", encoding="utf-8") as f:
        json.dump(token_breakdown, f, indent=2)

    print("\n--- Token Budget Breakdown ---")
    for k, v in token_breakdown.items():
        print(f"  {k}: {v}")

    return {"summary": summary_rows, "token_breakdown": token_breakdown, "raw": raw_data}


def _print_summary(rows: list[dict]) -> None:
    print(f"\n{'='*90}")
    print("  BENCHMARK SUMMARY TABLE")
    print(f"{'='*90}")
    header = (
        f"{'Conv':<12} {'Name':<30} {'MemRel':>7} {'BaseRel':>7} "
        f"{'Delta':>7} {'CtxUtil':>7} {'HitRate':>8} {'TokEff':>8}"
    )
    print(header)
    print("-" * 90)
    for r in rows:
        print(
            f"{r['conv_id']:<12} {r['name'][:28]:<30} "
            f"{r['mem_relevance']:>7.3f} {r['base_relevance']:>7.3f} "
            f"{r['relevance_delta']:>+7.3f} {r['mem_context_util']:>7.3f} "
            f"{r['mem_hit_rate']:>8.3f} {r['token_efficiency']:>8.4f}"
        )
    print("-" * 90)
    avg_delta = sum(r["relevance_delta"] for r in rows) / len(rows)
    avg_hit = sum(r["mem_hit_rate"] for r in rows) / len(rows)
    avg_util = sum(r["mem_context_util"] for r in rows) / len(rows)
    print(
        f"{'AVERAGE':<12} {'':<30} {'':<8} {'':<8} "
        f"{avg_delta:>+7.3f} {avg_util:>7.3f} {avg_hit:>8.3f}"
    )
    print(f"{'='*90}\n")

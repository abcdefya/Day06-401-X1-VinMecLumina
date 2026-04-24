"""
Entry point: Run Lab 17 Multi-Memory Agent Benchmark.

Usage:
    python -m lab17.run_benchmark
    python -m lab17.run_benchmark --provider groq
    python -m lab17.run_benchmark --provider azure

Requires at least one of:
    GROQ_API_KEY=...
    OPENAI_API_KEY=...   (or GITHUB_TOKEN for Azure GitHub Models)
"""
from __future__ import annotations
import argparse
import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser(description="Lab 17: Multi-Memory Agent Benchmark")
    parser.add_argument("--provider", default="groq", choices=["groq", "azure", "openai"],
                        help="LLM provider (default: groq)")
    parser.add_argument("--model", default="", help="Model name (auto-selected if empty)")
    parser.add_argument("--output-dir", default="lab17/results", help="Where to save results")
    parser.add_argument("--session-id", default="benchmark_run", help="Session identifier")
    parser.add_argument("--quick", action="store_true",
                        help="Run only first 3 conversations for a quick test")
    args = parser.parse_args()

    # Validate at least one key is set
    has_key = any(os.getenv(k) for k in ["GROQ_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN"])
    if not has_key:
        print("ERROR: No API key found. Please set one of:")
        print("  GROQ_API_KEY, OPENAI_API_KEY, or GITHUB_TOKEN")
        print("\nExample (PowerShell):")
        print("  $env:GROQ_API_KEY = 'your_key_here'")
        print("  python -m lab17.run_benchmark")
        sys.exit(1)

    from .agent.graph import MemoryAgentConfig
    from .benchmark.runner import run_benchmark
    from .benchmark.conversations import BENCHMARK_CONVERSATIONS

    config = MemoryAgentConfig(
        session_id=args.session_id,
        provider=args.provider,
        model=args.model,
    )

    conversations = BENCHMARK_CONVERSATIONS[:3] if args.quick else BENCHMARK_CONVERSATIONS

    print(f"Starting benchmark with provider={args.provider}, conversations={len(conversations)}")
    results = run_benchmark(config=config, output_dir=args.output_dir, conversations=conversations)

    print(f"\nResults saved to: {args.output_dir}/")
    print("  - benchmark_results.json   (full turn-by-turn data)")
    print("  - token_budget_breakdown.json")
    return results


if __name__ == "__main__":
    main()

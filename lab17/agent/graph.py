"""
Multi-Memory LangGraph Agent.

Graph nodes:
  START → memory_retrieve → llm_call → memory_store → END
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START

from .state import MemoryAgentState
from ..memory.short_term import ShortTermMemory
from ..memory.long_term import LongTermMemory
from ..memory.episodic import EpisodicMemory
from ..memory.semantic import SemanticMemory
from ..memory.router import MemoryRouter, classify_intent


SYSTEM_PROMPT = """You are a helpful AI assistant with persistent memory.
You remember user preferences, past conversations, and factual details across sessions.
Use the provided MEMORY CONTEXT to give personalized, context-aware responses.
If relevant memory is available, reference it naturally in your response.
Be concise and friendly."""


@dataclass
class MemoryAgentConfig:
    session_id: str = "default"
    provider: str = "groq"           # "groq" | "azure" | "openai"
    model: str = ""                   # auto-selected if empty
    max_context_tokens: int = 2000
    log_dir: str = "lab17/data"
    chroma_dir: str = "lab17/data/chroma"


def _build_llm(config: MemoryAgentConfig):
    """Build LLM from env config with automatic fallback."""
    provider = config.provider.lower()

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            from langchain_groq import ChatGroq
            model = config.model or "llama-3.3-70b-versatile"
            return ChatGroq(api_key=api_key, model=model, temperature=0.3)

    if provider in ("azure", "openai") or os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
        if api_key:
            from langchain_openai import ChatOpenAI
            if os.getenv("GITHUB_TOKEN") and not os.getenv("OPENAI_API_KEY"):
                return ChatOpenAI(
                    api_key=api_key,
                    base_url="https://models.inference.ai.azure.com",
                    model=config.model or "gpt-4o-mini",
                    temperature=0.3,
                )
            return ChatOpenAI(api_key=api_key, model=config.model or "gpt-4o-mini", temperature=0.3)

    # Fallback: try GROQ with any available key
    for env_key in ("GROQ_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN"):
        key = os.getenv(env_key)
        if key:
            try:
                from langchain_groq import ChatGroq
                return ChatGroq(api_key=key, model="llama-3.3-70b-versatile", temperature=0.3)
            except Exception:
                pass

    raise RuntimeError(
        "No API key found. Set GROQ_API_KEY, OPENAI_API_KEY, or GITHUB_TOKEN."
    )


def build_memory_agent(config: MemoryAgentConfig | None = None):
    """
    Build and return a compiled LangGraph memory agent.

    Returns (graph, router) – the graph for invocation and router for direct access.
    """
    if config is None:
        config = MemoryAgentConfig()

    # Instantiate memory backends
    short_term = ShortTermMemory(max_tokens=config.max_context_tokens)
    long_term = LongTermMemory(session_id=config.session_id)
    episodic = EpisodicMemory(session_id=config.session_id, log_dir=config.log_dir)
    semantic = SemanticMemory(session_id=config.session_id, persist_dir=config.chroma_dir)
    router = MemoryRouter(short_term, long_term, episodic, semantic)

    llm = _build_llm(config)

    # ── Node definitions ──────────────────────────────────────────────────────

    def memory_retrieve(state: MemoryAgentState) -> dict:
        """Retrieve relevant context from memory based on intent."""
        user_input = state.get("user_input", "")
        intent = classify_intent(user_input)
        retrieval = router.retrieve(user_input)
        return {
            "memory_context": retrieval["context"],
            "memory_type": retrieval["memory_type"],
            "memory_hits": retrieval["hit_count"],
            "intent": intent,
        }

    def llm_call(state: MemoryAgentState) -> dict:
        """Call LLM with memory-enriched context."""
        user_input = state.get("user_input", "")
        memory_context = state.get("memory_context", "")

        system_content = SYSTEM_PROMPT
        if memory_context:
            system_content += f"\n\n--- MEMORY CONTEXT ---\n{memory_context}\n--- END MEMORY ---"

        messages = [SystemMessage(content=system_content), HumanMessage(content=user_input)]

        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Estimate tokens
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        token_count = len(enc.encode(system_content + user_input + response_text))

        return {
            "response": response_text,
            "token_count": token_count,
            "messages": [HumanMessage(content=user_input), AIMessage(content=response_text)],
        }

    def memory_store(state: MemoryAgentState) -> dict:
        """Persist this turn to all memory backends."""
        user_input = state.get("user_input", "")
        response = state.get("response", "")
        intent = state.get("intent", "unknown")

        router.store_turn("user", user_input, intent=intent)
        router.store_turn("assistant", response, intent=intent)
        return {}

    # ── Graph construction ────────────────────────────────────────────────────

    builder = StateGraph(MemoryAgentState)
    builder.add_node("memory_retrieve", memory_retrieve)
    builder.add_node("llm_call", llm_call)
    builder.add_node("memory_store", memory_store)

    builder.add_edge(START, "memory_retrieve")
    builder.add_edge("memory_retrieve", "llm_call")
    builder.add_edge("llm_call", "memory_store")
    builder.add_edge("memory_store", END)

    graph = builder.compile()
    return graph, router


def run_turn(graph, session_state: dict, user_input: str) -> dict:
    """
    Run a single conversation turn through the memory agent graph.

    Args:
        graph: compiled LangGraph
        session_state: mutable dict tracking session_id
        user_input: user's message

    Returns updated state dict with response, memory_type, etc.
    """
    state = {
        "user_input": user_input,
        "session_id": session_state.get("session_id", "default"),
        "messages": session_state.get("messages", []),
    }
    result = graph.invoke(state)
    session_state["messages"] = result.get("messages", [])
    return result

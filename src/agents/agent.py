from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.core.logger import logger
from src.core.metrics import tracker
from src.state import AgentState


load_dotenv()


def load_system_prompt() -> str:
    prompt_path = Path(__file__).with_name("system_prompt.md")
    try:
        content = prompt_path.read_text(encoding="utf-8").strip()
        if content:
            return content
        logger.error(f"System prompt file is empty: {prompt_path}")
    except FileNotFoundError:
        logger.error(f"System prompt file not found: {prompt_path}")

    return (
        "Ban la Vinmec Lumina, tro ly giai thich ket qua xet nghiem. "
        "Khong chan doan benh, khong ke don thuoc, va luon khuyen "
        "nguoi dung tham khao bac si khi can."
    )


def load_tools() -> list[Any]:
    try:
        # Optional tools module; keep runtime resilient when tools are not ready.
        from src.tools import tools as tools_module
    except Exception:
        return []

    if hasattr(tools_module, "TOOLS") and isinstance(tools_module.TOOLS, list):
        return tools_module.TOOLS

    if hasattr(tools_module, "tools") and isinstance(tools_module.tools, list):
        return tools_module.tools

    return []


@lru_cache(maxsize=1)
def _get_llm_bundle() -> tuple[Any, str, str]:
    """Create Azure AI OpenAI-compatible client with fixed endpoint/model."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Set it in .env before chat.")

    from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

    llm = AzureAIOpenAIApiChatModel(
        endpoint="https://models.inference.ai.azure.com",
        credential=api_key,
        model="gpt-4o",
    )
    return llm, "azure", "gpt-4o"


SYSTEM_PROMPT = load_system_prompt()
tools_list = load_tools()


def build_model_messages(state: AgentState):
    history = list(state.get("messages", []))

    if history and isinstance(history[0], SystemMessage):
        return history

    return [SystemMessage(content=SYSTEM_PROMPT), *history]


def agent_node(state: AgentState):
    llm, provider, model_name = _get_llm_bundle()
    llm_with_tools = llm.bind_tools(tools_list) if tools_list else llm

    model_messages = build_model_messages(state)
    start_time = time.time()
    response = llm_with_tools.invoke(model_messages)
    latency = int((time.time() - start_time) * 1000)

    if getattr(response, "tool_calls", None):
        for tc in response.tool_calls:
            logger.log_event(
                "TOOL_CALL",
                {
                    "tool": tc.get("name"),
                    "arguments": tc.get("args"),
                    "latency_ms": latency,
                },
            )
    else:
        preview = (response.content[:100] + "...") if response.content else ""
        logger.log_event("DIRECT_RESPONSE", {"content": preview})

    if getattr(response, "usage_metadata", None):
        tracker.track_request(
            provider=provider,
            model=model_name,
            usage=response.usage_metadata,
            latency_ms=latency,
        )

    return {"messages": [response]}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)

    if tools_list:
        builder.add_node("tools", ToolNode(tools_list))
        builder.add_edge(START, "agent")
        builder.add_conditional_edges("agent", tools_condition)
        builder.add_edge("tools", "agent")
    else:
        builder.add_edge(START, "agent")
        builder.add_edge("agent", END)
    return builder.compile()


graph = build_graph()


def run_agent_turn(user_input: str, history: list[Any] | None = None) -> list[Any]:
    """
    Run one chat turn through the graph and return updated history.
    """
    history = history or []
    state = graph.invoke({"messages": [*history, HumanMessage(content=user_input)]})
    return list(state.get("messages", []))


def chat_loop() -> None:
    """
    Interactive CLI loop:
      - type /exit to quit
      - each turn calls LLM API through graph
    """
    history: list[Any] = []
    print("Vinmec Lumina chat ready. Type /exit to stop.")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "exit", "quit"}:
            print("Exiting chat.")
            break

        history = run_agent_turn(user_input, history)
        last_ai = next((m for m in reversed(history) if isinstance(m, AIMessage)), None)
        print(f"Lumina: {getattr(last_ai, 'content', '')}")


if __name__ == "__main__":
    chat_loop()

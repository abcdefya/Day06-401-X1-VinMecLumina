"""LangGraph state for the multi-memory agent."""
from __future__ import annotations
from typing import Any, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class MemoryAgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]   # Full message history for LLM
    user_input: str                            # Current user message
    memory_context: str                        # Retrieved memory context
    memory_type: str                           # Which memory was used
    memory_hits: int                           # Number of memory hits
    response: str                              # Final agent response
    intent: str                                # Classified intent
    token_count: int                           # Tokens used this turn
    session_id: str                            # Session identifier

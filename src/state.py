from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Shared graph state used across agent and workflow modules."""

    # Chat history channel for LangGraph message-based flows.
    messages: Annotated[list[AnyMessage], add_messages]

    # Workflow-centric fields for the Lumina pipeline.
    patient_profile: dict[str, Any]
    lab_results: list[dict[str, Any]]
    is_critical: bool
    critical_alert: dict[str, Any] | None
    overall_severity: str
    per_test_severity: list[dict[str, Any]]
    explanations: list[dict[str, Any]] | str
    suggestions: list[str]
    errors: list[str]

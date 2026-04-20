from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Shared graph state used across agent and workflow modules."""

    messages: Annotated[list[AnyMessage], add_messages] # Chat message history
    patient_profile: dict[str, Any]                      # Patient demographics and history
    lab_results: list[dict[str, Any]]                   # Normalized lab test results
    llm_provider: str                                   # LLM provider selection: 'azure' or 'groq'
    is_critical: bool                                   # Flag for life-threatening values
    critical_alert: dict[str, Any] | None               # Data for emergency notifications
    overall_severity: str                               # Overall health status (e.g., Normal, High Risk)
    per_test_severity: list[dict[str, Any]]             # Severity level mapped to each test
    explanations: list[dict[str, Any]] | str            # Human-readable interpretations
    suggestions: list[str]                              # Actionable health tips and follow-ups
    summary: str                                        # Brief overview of key findings
    is_critical_escalation: bool                        # Trigger for emergency workflow branch
    errors: list[str]                                   # List of pipeline execution errors

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from src.data.mock_patients import get_patient
from src.nodes.explain_node import explain_node
from src.nodes.guard_node import guard_node
from src.nodes.severity_node import severity_node
from src.nodes.suggest_node import suggest_node
from src.agents.state import AgentState


def _route_from_guard(state: AgentState) -> str:
    return "critical" if state.get("is_critical") else "normal"


def build_graph():
    """
    Build the LangGraph workflow:
      START -> guard
      guard (critical) -> END
      guard (normal) -> severity -> explain -> suggest -> END
    """
    builder = StateGraph(AgentState)
    builder.add_node("guard", guard_node)
    builder.add_node("severity", severity_node)
    builder.add_node("explain", explain_node)
    builder.add_node("suggest", suggest_node)

    builder.add_edge(START, "guard")
    builder.add_conditional_edges(
        "guard",
        _route_from_guard,
        {
            "critical": END,
            "normal": "severity",
        },
    )
    builder.add_edge("severity", "explain")
    builder.add_edge("explain", "suggest")
    builder.add_edge("suggest", END)
    return builder.compile()


graph = build_graph()


def _state_from_patient_id(patient_id: str) -> AgentState:
    patient = get_patient(patient_id)
    return {
        "patient_profile": {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "age": patient.age,
            "sex": patient.sex,
            "conditions": patient.conditions,
            "test_date": patient.test_date,
        },
        "lab_results": [result.model_dump() for result in patient.lab_results],
        "errors": [],
    }


def _fill_critical_defaults(state: AgentState) -> AgentState:
    if not state.get("is_critical"):
        return state
    if not state.get("summary"):
        state["summary"] = "Phát hiện chỉ số nguy kịch. Cần chăm sóc y tế ngay lập tức."
    if "suggestions" not in state:
        state["suggestions"] = [
            "Đến cơ sở y tế gần nhất ngay lập tức.",
            "Không tự ý dùng thuốc. Mang theo kết quả xét nghiệm để bác sĩ xem xét khẩn cấp.",
            "Liên hệ tổng đài Vinmec hoặc bác sĩ của bạn ngay.",
        ]
    if "explanations" not in state:
        state["explanations"] = []
    state["is_critical_escalation"] = True
    return state


def run_workflow(*, patient_id: str | None = None, initial_state: AgentState | None = None) -> AgentState:
    """
    Run the complete Lumina workflow.

    Inputs:
      - patient_id: load patient from mock dataset, or
      - initial_state: caller-supplied state payload
    """
    if initial_state is None and patient_id is None:
        raise ValueError("Provide either patient_id or initial_state")

    state = initial_state if initial_state is not None else _state_from_patient_id(patient_id)  # type: ignore[arg-type]
    result = graph.invoke(state)
    return _fill_critical_defaults(result)

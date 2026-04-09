from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from src.data.mock_patients import get_patient
from src.nodes.explain_node import explain_node
from src.nodes.guard_node import guard_node
from src.nodes.severity_node import severity_node
from src.nodes.suggest_node import suggest_node
from src.agents.state import AgentState
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
from langchain_core.messages import HumanMessage
import os


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


def _state_from_patient_id(patient_id: str, llm_provider: str = "azure") -> AgentState:
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
        "llm_provider": llm_provider,
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


def run_workflow(*, patient_id: str | None = None, initial_state: AgentState | None = None, llm_provider: str = "azure") -> AgentState:
    """
    Run the complete Lumina workflow.

    Inputs:
      - patient_id: load patient from mock dataset, or
      - initial_state: caller-supplied state payload
      - llm_provider: 'azure' (default) or 'groq'
    """
    if initial_state is None and patient_id is None:
        raise ValueError("Provide either patient_id or initial_state")

    state = initial_state if initial_state is not None else _state_from_patient_id(patient_id, llm_provider=llm_provider)  # type: ignore[arg-type]
    result = graph.invoke(state)
    return _fill_critical_defaults(result)


def build_llm(provider: str = "azure"):
    """
    Build LLM client for the specified provider.
    Supported: 'azure' or 'groq'
    """
    if provider.lower() == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise RuntimeError("langchain-groq not installed. Run: pip install langchain-groq")
        return ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile")
    
    # Default to Azure
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    try:
        from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
    except ImportError:
        raise RuntimeError("langchain-azure-ai not installed")
    return AzureAIOpenAIApiChatModel(
        endpoint="https://models.inference.ai.azure.com",
        credential=api_key,
        model="gpt-4o",
    )


def run_agent_turn(user_q: str, history: list, provider: str = "azure"):
    """
    Run a single turn of the chat agent for follow-up questions.
    
    Args:
      - user_q: User's question
      - history: List of previous messages
      - provider: 'azure' (default) or 'groq'
    """
    llm = build_llm(provider=provider)
    messages = history + [HumanMessage(content=user_q)]
    response = llm.invoke(messages)
    return messages + [response]

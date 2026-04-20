from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from src.data.lab_kb import get_kb_entry

load_dotenv()

_BANNED_PATTERNS = [
    r"\bdiagnos(?:e|is)\b",
    r"\bprescrib(?:e|ed|ing)\b",
    r"\bKê đơn thuốc\b",
    r"\bChẩn đoán bệnh\b",
    r"\bDùng thuốc\b",
]


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "agents" / "system_prompt.md"
    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
        if prompt:
            return prompt
    except FileNotFoundError:
        pass
    return (
        "You are Vinmec Lumina. Explain lab results in simple language. "
        "Do not diagnose and do not prescribe medications."
    )


def _build_llm(provider: str = "azure"):
    """
    Build LLM client for the specified provider.
    Supported: 'azure' or 'groq'
    """
    if provider.lower() == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        try:
            from langchain_groq import ChatGroq
        except Exception:
            return None
        return ChatGroq(api_key=api_key, model="mixtral-8x7b-32768")
    
    # Default to Azure
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
    except Exception:
        return None
    return AzureAIOpenAIApiChatModel(
        endpoint="https://models.inference.ai.azure.com",
        credential=api_key,
        model="gpt-4o",
    )


def _sanitize_text(text: str) -> str:
    if not text:
        return text
    sanitized = text
    for pattern in _BANNED_PATTERNS:
        sanitized = re.sub(pattern, "medical assessment", sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


def _severity_lookup(state: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in state.get("per_test_severity", []) or []:
        test_code = item.get("test_code")
        if test_code:
            mapping[test_code] = item.get("severity", "NORMAL")
    return mapping


_SEVERITY_VI = {
    "NORMAL": "Bình thường",
    "WATCH": "Theo dõi",
    "SEE_DOCTOR": "Gặp bác sĩ",
    "CRITICAL": "Khẩn cấp",
}


def _fallback_explanation(lab: dict[str, Any], severity: str) -> str:
    kb = get_kb_entry(lab.get("test_code", ""))
    flag = (lab.get("flag") or "NORMAL").upper()
    hint = kb["high_hint"] if "HIGH" in flag else kb["low_hint"] if "LOW" in flag else kb["meaning"]
    sev_label = _SEVERITY_VI.get(severity, severity)
    return (
        f"{lab.get('test_name', lab.get('test_code', 'Xét nghiệm này'))}: "
        f"giá trị {lab.get('value')} {lab.get('unit', '')}. "
        f"Mức độ: {sev_label}. {kb['meaning']} {hint} {kb['safe_next_step']}"
    )


def _llm_explanation(llm, system_prompt: str, patient_profile: dict[str, Any], lab: dict[str, Any], severity: str) -> str:
    kb = get_kb_entry(lab.get("test_code", ""))
    human_prompt = (
        "Explain this abnormal lab result in plain Vietnamese for non-medical adults.\n"
        "Keep to 2-4 short sentences. Avoid diagnosis and medication advice.\n"
        f"Patient: age={patient_profile.get('age')}, sex={patient_profile.get('sex')}, "
        f"conditions={patient_profile.get('conditions', [])}\n"
        f"Test: code={lab.get('test_code')}, name={lab.get('test_name')}, value={lab.get('value')}, "
        f"unit={lab.get('unit')}, ref_low={lab.get('ref_low')}, ref_high={lab.get('ref_high')}, "
        f"flag={lab.get('flag')}, severity={severity}\n"
        f"Knowledge: meaning={kb['meaning']}; high_hint={kb['high_hint']}; "
        f"low_hint={kb['low_hint']}; next_step={kb['safe_next_step']}"
    )
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
    )
    return str(getattr(response, "content", "") or "").strip()


def explain_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Create per-test explanations for abnormal indicators.
    Falls back to deterministic explanations when model access is unavailable.
    """
    if state.get("is_critical"):
        return {
            "summary": "Phát hiện nguy cơ nghiêm trọng. Chuyển sang xử lý khẩn cấp.",
            "explanations": [],
            "is_critical_escalation": True,
        }

    lab_results = state.get("lab_results", []) or []
    abnormal = [item for item in lab_results if (item.get("flag") or "NORMAL") != "NORMAL"]

    if not abnormal:
        return {
            "summary": "Tất cả các chỉ số đều nằm trong khoảng tham chiếu bình thường.",
            "explanations": [],
            "is_critical_escalation": False,
        }

    severity_map = _severity_lookup(state)
    system_prompt = _load_system_prompt()
    provider = state.get("llm_provider", "azure")
    llm = _build_llm(provider=provider)

    explanations: list[dict[str, Any]] = []
    for lab in abnormal:
        code = lab.get("test_code", "")
        severity = severity_map.get(code, "WATCH")
        text = _fallback_explanation(lab, severity)

        if llm is not None:
            try:
                llm_text = _llm_explanation(llm, system_prompt, state.get("patient_profile", {}), lab, severity)
                if len(llm_text.split()) >= 12:
                    text = llm_text
            except Exception:
                # Keep deterministic fallback when LLM request fails.
                pass

        explanations.append(
            {
                "test_code": code,
                "test_name": lab.get("test_name", code),
                "value": lab.get("value"),
                "unit": lab.get("unit", ""),
                "severity": severity,
                "explanation": _sanitize_text(text),
            }
        )

    summary = f"{len(explanations)} chỉ số bất thường cần chú ý."
    return {"summary": summary, "explanations": explanations, "is_critical_escalation": False}

"""Suggest node for Vinmec Lumina."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from src.nodes.lab_kb import (
    DEFAULT_DISCLAIMER,
    SAFE_STYLE_GUIDE,
    load_system_prompt,
    normalize_patient_data,
    summarize_tests_for_prompt,
)

LLMCallable = Callable[[str, str], str]
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_PRIORITY = {"routine", "follow_up", "doctor_soon", "urgent"}
SEVERITY_TO_PRIORITY = {
    "NORMAL": "routine",
    "WATCH": "follow_up",
    "SEE_DOCTOR": "doctor_soon",
    "CRITICAL": "urgent",
}
FALLBACK_SYSTEM_PROMPT = (
    "Ban la Lumina, tro ly goi y buoc tiep theo sau khi giai thich ket qua xet nghiem. "
    "Khong chan doan benh, khong ke thuoc, khong dua huong dan nguy hiem. "
    "Luon tra ve duy nhat mot JSON hop le."
)


@dataclass
class SuggestNodeConfig:
    max_suggestions: int = 3
    language: str = "vi"


def _safe_json_dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        return dumped if isinstance(dumped, dict) else {}

    dict_fn = getattr(value, "dict", None)
    if callable(dict_fn):
        dumped = dict_fn()
        return dumped if isinstance(dumped, dict) else {}

    return {}


def _coerce_result_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    results: list[dict[str, Any]] = []
    for item in value:
        mapped = _coerce_mapping(item)
        if mapped:
            results.append(mapped)
    return results


def _normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    base = (
        _coerce_mapping(state.get("patient_profile"))
        or _coerce_mapping(state.get("patient"))
        or _coerce_mapping(state.get("patient_data"))
        or _coerce_mapping(state.get("input"))
    )
    raw_results = _coerce_result_list(state.get("lab_results")) or _coerce_result_list(base.get("lab_results"))
    normalized = normalize_patient_data({**base, "lab_results": raw_results})
    return {
        "patient_profile": {
            "patient_id": normalized.get("patient_id", ""),
            "name": normalized.get("name", ""),
            "age": normalized.get("age"),
            "sex": normalized.get("sex", ""),
            "conditions": normalized.get("conditions", []),
            "test_date": normalized.get("test_date", "2026-04-08"),
        },
        "lab_results": normalized.get("lab_results", []),
    }


def _overall_severity(state: dict[str, Any], lab_results: list[dict[str, Any]]) -> str:
    severity = str(state.get("overall_severity") or "").strip().upper()
    if severity in SEVERITY_TO_PRIORITY:
        return severity

    flags = {str(item.get("flag", "NORMAL")).upper() for item in lab_results}
    if {"CRITICAL_LOW", "CRITICAL_HIGH"} & flags:
        return "CRITICAL"
    if {"HIGH", "LOW"} & flags:
        if len([item for item in lab_results if str(item.get("flag", "NORMAL")).upper() in {"HIGH", "LOW"}]) >= 3:
            return "SEE_DOCTOR"
        return "WATCH"
    return "NORMAL"


def _priority_from_state(state: dict[str, Any], lab_results: list[dict[str, Any]]) -> str:
    severity = _overall_severity(state, lab_results)
    return SEVERITY_TO_PRIORITY.get(severity, "follow_up")


def build_suggest_user_prompt(state: dict[str, Any], config: SuggestNodeConfig | None = None) -> str:
    cfg = config or SuggestNodeConfig()
    normalized = _normalize_state(state)
    patient_profile = normalized["patient_profile"]
    lab_results = normalized["lab_results"]
    overall_severity = _overall_severity(state, lab_results)
    explain_output = _coerce_mapping(state.get("explain_output"))
    if not explain_output and state.get("explanations"):
        explain_output = {
            "patient_id": patient_profile.get("patient_id", ""),
            "overall_severity": overall_severity,
            "explanations": state.get("explanations", []),
        }

    payload = {
        "node_name": "suggest_node",
        "patient_profile": patient_profile,
        "lab_results": lab_results,
        "overall_severity": overall_severity,
        "priority": _priority_from_state(state, lab_results),
        "per_test_severity": state.get("per_test_severity", []),
        "critical_alert": state.get("critical_alert"),
        "is_critical": state.get("is_critical", False),
        "explain_output": explain_output,
        "lab_kb_context": summarize_tests_for_prompt(lab_results),
        "style_rules": {
            "must_do": SAFE_STYLE_GUIDE["must_do"],
            "must_not_do": SAFE_STYLE_GUIDE["must_not_do"],
            "preferred_phrases": SAFE_STYLE_GUIDE["preferred_phrases"],
            "banned_phrases": SAFE_STYLE_GUIDE["banned_phrases"],
            "max_suggestions": cfg.max_suggestions,
        },
        "default_disclaimer": DEFAULT_DISCLAIMER,
        "instruction": (
            "Return JSON only with schema: "
            "{patient_id, overall_severity, priority, rationale, suggestions[], when_to_seek_help, confidence, disclaimer}. "
            "Suggestions must be safe, concrete, and short."
        ),
    }
    return _safe_json_dumps(payload)


def _extract_first_json_block(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        raise ValueError("LLM output does not contain a JSON object.")
    return match.group(0)


def parse_suggest_response(raw_text: str, patient_id: str, overall_severity: str) -> dict[str, Any]:
    data = json.loads(_extract_first_json_block(raw_text))
    confidence = str(data.get("confidence", "medium")).strip().lower()
    priority = str(data.get("priority", _priority_from_state({"overall_severity": overall_severity}, []))).strip().lower()

    suggestions = [str(item).strip() for item in data.get("suggestions", []) if str(item).strip()]
    return {
        "patient_id": str(data.get("patient_id") or patient_id or ""),
        "overall_severity": str(data.get("overall_severity") or overall_severity or "NORMAL").strip().upper(),
        "priority": priority if priority in ALLOWED_PRIORITY else _priority_from_state({"overall_severity": overall_severity}, []),
        "rationale": str(data.get("rationale", "")).strip(),
        "suggestions": suggestions,
        "when_to_seek_help": str(data.get("when_to_seek_help", "")).strip(),
        "confidence": confidence if confidence in ALLOWED_CONFIDENCE else "medium",
        "disclaimer": str(data.get("disclaimer", DEFAULT_DISCLAIMER)).strip() or DEFAULT_DISCLAIMER,
    }


def fallback_suggest_response(state: dict[str, Any], config: SuggestNodeConfig | None = None) -> dict[str, Any]:
    cfg = config or SuggestNodeConfig()
    normalized = _normalize_state(state)
    patient_profile = normalized["patient_profile"]
    lab_results = normalized["lab_results"]
    overall_severity = _overall_severity(state, lab_results)
    priority = _priority_from_state(state, lab_results)
    has_conditions = bool(patient_profile.get("conditions"))

    suggestions: list[str] = []
    if priority == "urgent":
        suggestions.append(
            "Lien he bac si hoac co so y te som neu ban co trieu chung bat thuong hoac da duoc gan co nguy co cao."
        )
    else:
        suggestions.append(
            "Mang theo ket qua xet nghiem de trao doi voi bac si trong dung boi canh suc khoe hien tai."
        )

    if has_conditions:
        suggestions.append(
            "Dat ket qua trong boi canh benh nen hien co de xem muc tieu theo doi co can dieu chinh khong."
        )

    if priority in {"routine", "follow_up"}:
        suggestions.append("Tiep tuc theo doi va tai kham theo lich hen, khong tu y thay doi thuoc.")
    else:
        suggestions.append("Khong tu y chan doan hay thay doi thuoc chi dua vao mot ket qua xet nghiem.")

    suggestions = suggestions[: cfg.max_suggestions]
    return {
        "patient_id": patient_profile.get("patient_id", ""),
        "overall_severity": overall_severity,
        "priority": priority,
        "rationale": "Uu tien duoc chon theo huong an toan dua tren muc do bat thuong cua xet nghiem va thong tin co san trong state.",
        "suggestions": suggestions,
        "when_to_seek_help": "Nen lien he co so y te som neu co trieu chung bat thuong, tinh trang xau di, hoac ket qua duoc gan co nguy co cao.",
        "confidence": "low",
        "disclaimer": DEFAULT_DISCLAIMER,
    }


def suggest_node(
    state: dict[str, Any],
    llm: LLMCallable | None = None,
    config: SuggestNodeConfig | None = None,
) -> dict[str, Any]:
    cfg = config or SuggestNodeConfig()
    normalized = _normalize_state(state)
    patient_profile = normalized["patient_profile"]
    lab_results = normalized["lab_results"]
    overall_severity = _overall_severity(state, lab_results)
    prompt = build_suggest_user_prompt({**state, **normalized}, config=cfg)
    system_prompt = load_system_prompt("suggest_node", FALLBACK_SYSTEM_PROMPT)

    if llm is None:
        result = fallback_suggest_response({**state, **normalized}, config=cfg)
        raw_text = _safe_json_dumps(result)
    else:
        raw_text = llm(system_prompt, prompt)
        try:
            result = parse_suggest_response(raw_text, patient_profile.get("patient_id", ""), overall_severity)
            if not result["suggestions"]:
                result = fallback_suggest_response({**state, **normalized}, config=cfg)
        except Exception:
            result = fallback_suggest_response({**state, **normalized}, config=cfg)

    return {
        **state,
        "patient_profile": patient_profile,
        "lab_results": lab_results,
        "overall_severity": result["overall_severity"],
        "suggest_prompt": prompt,
        "suggest_raw": raw_text,
        "suggest_output": result,
        "suggestions": result["suggestions"],
    }

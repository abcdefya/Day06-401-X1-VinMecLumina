"""Explain node for Vinmec Lumina."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from src.nodes.lab_kb import (
    DEFAULT_DISCLAIMER,
    SAFE_STYLE_GUIDE,
    canonicalize_test_code,
    load_system_prompt,
    normalize_patient_data,
    summarize_tests_for_prompt,
)

LLMCallable = Callable[[str, str], str]
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_SEVERITY = {"NORMAL", "WATCH", "SEE_DOCTOR", "CRITICAL"}
SEVERITY_ORDER = {
    "NORMAL": 0,
    "WATCH": 1,
    "SEE_DOCTOR": 2,
    "CRITICAL": 3,
}
FALLBACK_SYSTEM_PROMPT = (
    "Ban la Lumina, tro ly giai thich ket qua xet nghiem cho benh nhan Vinmec. "
    "Chi su dung du lieu co trong state. Khong chan doan benh, khong ke thuoc, "
    "khong dua ra khang dinh tuyet doi. Luon tra ve duy nhat mot JSON hop le."
)


@dataclass
class ExplainNodeConfig:
    max_explanations: int = 4
    language: str = "vi"
    include_normal_when_all_normal: bool = True


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


def _severity_map_from_state(state: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in state.get("per_test_severity") or []:
        entry = _coerce_mapping(item)
        test_code = canonicalize_test_code(entry.get("test_code"), entry.get("test_name"))
        severity = str(entry.get("severity") or entry.get("level") or "").strip().upper()
        if test_code and severity in ALLOWED_SEVERITY:
            result[test_code] = severity
    return result


def _derive_severity(result: dict[str, Any], overall_severity: str, severity_map: dict[str, str]) -> str:
    test_code = result.get("test_code", "")
    if test_code in severity_map:
        return severity_map[test_code]

    flag = str(result.get("flag", "NORMAL")).upper()
    if flag in {"CRITICAL_LOW", "CRITICAL_HIGH"}:
        return "CRITICAL"
    if flag in {"HIGH", "LOW"}:
        if overall_severity in {"SEE_DOCTOR", "CRITICAL"}:
            return "SEE_DOCTOR"
        return "WATCH"
    return "NORMAL"


def _compute_overall_severity(lab_results: list[dict[str, Any]], state: dict[str, Any], severity_map: dict[str, str]) -> str:
    explicit = str(state.get("overall_severity") or "").strip().upper()
    if explicit in ALLOWED_SEVERITY:
        return explicit

    worst = "NORMAL"
    for item in lab_results:
        severity = _derive_severity(item, explicit, severity_map)
        if SEVERITY_ORDER[severity] > SEVERITY_ORDER[worst]:
            worst = severity
    return worst


def _select_focus_results(
    lab_results: list[dict[str, Any]],
    overall_severity: str,
    severity_map: dict[str, str],
    config: ExplainNodeConfig,
) -> list[dict[str, Any]]:
    ranked = sorted(
        lab_results,
        key=lambda item: (
            -SEVERITY_ORDER[_derive_severity(item, overall_severity, severity_map)],
            item.get("test_code", ""),
        ),
    )
    abnormal = [item for item in ranked if str(item.get("flag", "NORMAL")).upper() != "NORMAL"]
    if abnormal:
        return abnormal[: config.max_explanations]
    if config.include_normal_when_all_normal:
        return ranked[:1]
    return []


def build_explain_user_prompt(state: dict[str, Any], config: ExplainNodeConfig | None = None) -> str:
    cfg = config or ExplainNodeConfig()
    normalized = _normalize_state(state)
    patient_profile = normalized["patient_profile"]
    lab_results = normalized["lab_results"]
    severity_map = _severity_map_from_state(state)
    overall_severity = _compute_overall_severity(lab_results, state, severity_map)
    focus_results = _select_focus_results(lab_results, overall_severity, severity_map, cfg)

    payload = {
        "node_name": "explain_node",
        "patient_profile": patient_profile,
        "lab_results": lab_results,
        "focus_results": focus_results,
        "overall_severity": overall_severity,
        "per_test_severity": [
            {
                "test_code": item["test_code"],
                "severity": _derive_severity(item, overall_severity, severity_map),
            }
            for item in focus_results
        ],
        "lab_kb_context": summarize_tests_for_prompt(focus_results or lab_results),
        "style_rules": {
            "must_do": SAFE_STYLE_GUIDE["must_do"],
            "must_not_do": SAFE_STYLE_GUIDE["must_not_do"],
            "preferred_phrases": SAFE_STYLE_GUIDE["preferred_phrases"],
            "banned_phrases": SAFE_STYLE_GUIDE["banned_phrases"],
            "max_explanations": cfg.max_explanations,
        },
        "default_disclaimer": DEFAULT_DISCLAIMER,
        "instruction": (
            "Return JSON only with schema: "
            "{patient_id, overall_severity, summary, explanations[], confidence, disclaimer}. "
            "Each explanation item must contain test_code and explanation."
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


def _default_explanation_text(patient_profile: dict[str, Any], result: dict[str, Any], severity: str) -> str:
    value = result.get("value")
    unit = result.get("unit", "")
    ref_low = result.get("ref_low")
    ref_high = result.get("ref_high")
    condition_text = ", ".join(patient_profile.get("conditions", [])) or "boi canh suc khoe hien tai"
    if severity == "CRITICAL":
        return (
            f"{result['test_name']} dang o muc rat dang chu y ({value} {unit}). "
            f"Chi so nay can duoc danh gia som cung bac si, nhat la trong boi canh {condition_text}."
        )
    if str(result.get("flag", "")).upper() == "HIGH":
        return (
            f"{result['test_name']} dang cao hon khoang tham chieu ({value} {unit}; "
            f"tham chieu {ref_low}-{ref_high} {unit}). Ket qua nay nen duoc doc cung boi canh {condition_text}."
        )
    if str(result.get("flag", "")).upper() in {"LOW", "CRITICAL_LOW"}:
        return (
            f"{result['test_name']} dang thap hon khoang tham chieu ({value} {unit}; "
            f"tham chieu {ref_low}-{ref_high} {unit}). Nen doi chieu them voi trieu chung va danh gia cua bac si."
        )
    return (
        f"{result['test_name']} hien trong gioi han tham chieu ({value} {unit}). "
        f"Day la mot dau hieu tuong doi on dinh trong boi canh hien tai."
    )


def _materialize_explanations(
    patient_profile: dict[str, Any],
    focus_results: list[dict[str, Any]],
    parsed_items: list[dict[str, str]],
    overall_severity: str,
    severity_map: dict[str, str],
) -> list[dict[str, Any]]:
    parsed_by_code = {
        canonicalize_test_code(item.get("test_code"), item.get("test_name")): item
        for item in parsed_items
        if canonicalize_test_code(item.get("test_code"), item.get("test_name")) != "UNKNOWN"
    }

    explanations: list[dict[str, Any]] = []
    for result in focus_results:
        test_code = result["test_code"]
        parsed_item = parsed_by_code.get(test_code, {})
        severity = _derive_severity(result, overall_severity, severity_map)
        explanation_text = str(parsed_item.get("explanation", "")).strip() or _default_explanation_text(
            patient_profile,
            result,
            severity,
        )
        explanations.append(
            {
                "test_code": test_code,
                "test_name": result["test_name"],
                "value": result["value"],
                "unit": result["unit"],
                "severity": severity,
                "explanation": explanation_text,
            }
        )
    return explanations


def parse_explain_response(
    raw_text: str,
    patient_profile: dict[str, Any],
    focus_results: list[dict[str, Any]],
    overall_severity: str,
    severity_map: dict[str, str],
) -> dict[str, Any]:
    data = json.loads(_extract_first_json_block(raw_text))
    confidence = str(data.get("confidence", "medium")).strip().lower()

    parsed_items: list[dict[str, str]] = []
    for item in data.get("explanations", []):
        entry = _coerce_mapping(item)
        parsed_items.append(
            {
                "test_code": str(entry.get("test_code", "")).strip(),
                "test_name": str(entry.get("test_name", "")).strip(),
                "explanation": str(entry.get("explanation", "")).strip(),
            }
        )

    explanations = _materialize_explanations(
        patient_profile,
        focus_results,
        parsed_items,
        overall_severity,
        severity_map,
    )
    return {
        "patient_id": str(data.get("patient_id") or patient_profile.get("patient_id") or ""),
        "overall_severity": overall_severity,
        "summary": str(data.get("summary", "")).strip(),
        "explanations": explanations,
        "confidence": confidence if confidence in ALLOWED_CONFIDENCE else "medium",
        "disclaimer": str(data.get("disclaimer", DEFAULT_DISCLAIMER)).strip() or DEFAULT_DISCLAIMER,
    }


def fallback_explain_response(state: dict[str, Any], config: ExplainNodeConfig | None = None) -> dict[str, Any]:
    cfg = config or ExplainNodeConfig()
    normalized = _normalize_state(state)
    patient_profile = normalized["patient_profile"]
    lab_results = normalized["lab_results"]
    severity_map = _severity_map_from_state(state)
    overall_severity = _compute_overall_severity(lab_results, state, severity_map)
    focus_results = _select_focus_results(lab_results, overall_severity, severity_map, cfg)

    explanations = _materialize_explanations(
        patient_profile,
        focus_results,
        [],
        overall_severity,
        severity_map,
    )

    if not lab_results:
        summary = "Chua co du lieu xet nghiem hop le de giai thich."
    elif not focus_results:
        summary = "Chua co chi so nao can giai thich them."
    elif overall_severity == "NORMAL":
        summary = f"Ket qua hien tai cua {patient_profile['name']} chu yeu nam trong gioi han tham chieu."
    else:
        test_names = ", ".join(item["test_name"] for item in focus_results)
        summary = f"Ghi nhan {len(focus_results)} chi so can luu y: {test_names}."

    return {
        "patient_id": patient_profile.get("patient_id", ""),
        "overall_severity": overall_severity,
        "summary": summary,
        "explanations": explanations,
        "confidence": "low",
        "disclaimer": DEFAULT_DISCLAIMER,
    }


def explain_node(
    state: dict[str, Any],
    llm: LLMCallable | None = None,
    config: ExplainNodeConfig | None = None,
) -> dict[str, Any]:
    cfg = config or ExplainNodeConfig()
    normalized = _normalize_state(state)
    patient_profile = normalized["patient_profile"]
    lab_results = normalized["lab_results"]
    severity_map = _severity_map_from_state(state)
    overall_severity = _compute_overall_severity(lab_results, state, severity_map)
    focus_results = _select_focus_results(lab_results, overall_severity, severity_map, cfg)
    prompt = build_explain_user_prompt({**state, **normalized}, config=cfg)
    system_prompt = load_system_prompt("explain_node", FALLBACK_SYSTEM_PROMPT)

    if llm is None:
        result = fallback_explain_response({**state, **normalized}, config=cfg)
        raw_text = _safe_json_dumps(result)
    else:
        raw_text = llm(system_prompt, prompt)
        try:
            result = parse_explain_response(raw_text, patient_profile, focus_results, overall_severity, severity_map)
            if not result["summary"]:
                result["summary"] = fallback_explain_response({**state, **normalized}, config=cfg)["summary"]
        except Exception:
            result = fallback_explain_response({**state, **normalized}, config=cfg)

    return {
        **state,
        "patient_profile": patient_profile,
        "lab_results": lab_results,
        "overall_severity": result["overall_severity"],
        "explain_prompt": prompt,
        "explain_raw": raw_text,
        "explain_output": result,
        "explanations": result["explanations"],
    }

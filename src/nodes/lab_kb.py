"""Shared lab knowledge and normalization helpers for the Lumina workflow."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Iterable

DEFAULT_DISCLAIMER = (
    "Thong tin nay chi de tham khao, khong thay the tu van, chan doan, "
    "hoac chi dinh dieu tri tu bac si."
)

SAFE_STYLE_GUIDE: dict[str, list[str]] = {
    "must_do": [
        "Bam sat gia tri, don vi, khoang tham chieu va flag trong du lieu.",
        "Giai thich ngan gon, de hieu, an toan cho benh nhan.",
        "Neu du lieu thieu, noi ro la chua du thong tin.",
        "Uu tien goi y theo doi va trao doi voi bac si.",
    ],
    "must_not_do": [
        "Khong chan doan ten benh.",
        "Khong ke thuoc, doi thuoc, ngung thuoc hoac dua lieu dung.",
        "Khong dua ra ket luan tuyet doi khi du lieu chua day du.",
    ],
    "preferred_phrases": [
        "co the lien quan",
        "can duoc danh gia them",
        "nen theo doi them",
        "nen trao doi voi bac si",
    ],
    "banned_phrases": [
        "ban chac chan bi",
        "day la chan doan",
        "khong can gap bac si",
        "hay tu dung thuoc",
    ],
}

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "agents" / "system_prompt.txt"

LAB_KB: dict[str, dict[str, Any]] = {
    "HBA1C": {
        "display_name": "HbA1c",
        "group": "Duong huyet",
        "plain_meaning": "HbA1c phan anh duong huyet trung binh trong khoang 2-3 thang gan day.",
        "why_high": "Gia tri cao thuong goi y kiem soat duong huyet chua tot trong thoi gian gan day.",
        "why_low": "Gia tri thap co the gap khi duong huyet xuong thap keo dai hoac kiem soat qua chat.",
        "patient_friendly_tips": [
            "Nen doc cung duong huyet doi va muc tieu dieu tri hien tai.",
            "Day la chi so theo doi xu huong dai han, khong chi mot thoi diem.",
        ],
        "follow_up_hints": [
            "trao doi ve muc tieu kiem soat duong huyet voi bac si",
            "theo doi lai theo lich hen",
        ],
        "priority": 95,
    },
    "GLUCOSE_F": {
        "display_name": "Glucose doi",
        "group": "Duong huyet",
        "plain_meaning": "Glucose doi cho biet muc duong huyet tai thoi diem lay mau sau khi nhin an.",
        "why_high": "Gia tri cao co the goi y duong huyet dang tang va can duoc doc trong boi canh benh nen.",
        "why_low": "Gia tri thap co the lien quan den ha duong huyet va can doi chieu trieu chung.",
        "patient_friendly_tips": [
            "Nen doc cung HbA1c hoac lich su xet nghiem.",
            "Khong nen tu y thay doi thuoc chi dua vao mot ket qua.",
        ],
        "follow_up_hints": [
            "theo doi duong huyet theo huong dan cua bac si",
            "trao doi neu ket qua tiep tuc cao hoac co trieu chung",
        ],
        "priority": 90,
    },
    "LDL": {
        "display_name": "LDL Cholesterol",
        "group": "Mo mau",
        "plain_meaning": "LDL la mot thanh phan mo mau lien quan den nguy co tim mach khi tang keo dai.",
        "why_high": "Gia tri cao thuong goi y can chu y hon den nguy co tim mach tong the.",
        "why_low": "Gia tri thap thuong khong dang lo neu phu hop muc tieu dieu tri ca nhan.",
        "patient_friendly_tips": [
            "Nen doc cung cac chi so mo mau khac va benh nen tim mach/chuyen hoa.",
        ],
        "follow_up_hints": [
            "xem lai che do an, van dong va muc tieu mo mau voi bac si",
            "theo doi dinh ky theo ke hoach dieu tri",
        ],
        "priority": 75,
    },
    "CREATININE": {
        "display_name": "Creatinine",
        "group": "Chuc nang than",
        "plain_meaning": "Creatinine thuong duoc dung de theo doi chuc nang than.",
        "why_high": "Gia tri cao co the goi y chuc nang than dang bi anh huong hoac can danh gia them.",
        "why_low": "Gia tri thap thuong it y nghia hon va doi khi lien quan den khoi co thap.",
        "patient_friendly_tips": [
            "Nen doc cung tuoi, gioi tinh va cac chi so than lien quan.",
        ],
        "follow_up_hints": [
            "duy tri theo doi chuc nang than theo lich hen",
        ],
        "priority": 70,
    },
    "HGB": {
        "display_name": "Hemoglobin",
        "group": "Cong thuc mau",
        "plain_meaning": "Hemoglobin la thanh phan giup hong cau van chuyen oxy trong mau.",
        "why_high": "Gia tri cao can duoc dat trong boi canh mat nuoc, hut thuoc la hoac cac yeu to khac.",
        "why_low": "Gia tri thap co the goi y thieu mau hoac tinh trang lien quan, can doc cung cac chi so mau khac.",
        "patient_friendly_tips": [
            "Nen doc cung RBC va trieu chung nhu met, chong mat neu co.",
        ],
        "follow_up_hints": [
            "trao doi voi bac si neu thieu mau keo dai hoac co trieu chung",
        ],
        "priority": 80,
    },
    "WBC": {
        "display_name": "WBC",
        "group": "Cong thuc mau",
        "plain_meaning": "WBC phan anh so luong bach cau, thuong lien quan den phan ung viem hoac nhiem trung.",
        "why_high": "Gia tri cao co the lien quan den viem, nhiem trung hoac cac boi canh khac.",
        "why_low": "Gia tri thap co the lien quan den giam bach cau va can danh gia them.",
        "patient_friendly_tips": [
            "Khong nen tu ket luan nguyen nhan chi tu WBC don le.",
        ],
        "follow_up_hints": [
            "trao doi voi bac si neu WBC bat thuong keo dai hoac co trieu chung",
        ],
        "priority": 75,
    },
    "PLATELET": {
        "display_name": "Platelet",
        "group": "Cong thuc mau",
        "plain_meaning": "Platelet phan anh so luong tieu cau, lien quan den qua trinh dong cam mau.",
        "why_high": "Gia tri cao co the can theo doi them tuy boi canh lam sang.",
        "why_low": "Gia tri thap co the can luu y hon vi lien quan den nguy co chay mau trong mot so truong hop.",
        "patient_friendly_tips": [
            "Nen doc cung cac xet nghiem mau khac va trieu chung thuc te.",
        ],
        "follow_up_hints": [
            "trao doi them voi bac si neu co bam tim, chay mau hoac ket qua giam ro",
        ],
        "priority": 78,
    },
    "AST": {
        "display_name": "AST",
        "group": "Chuc nang gan",
        "plain_meaning": "AST la men gan, thuong duoc doc cung ALT va cac xet nghiem gan khac.",
        "why_high": "Gia tri cao co the goi y gan hoac mo khac dang bi anh huong va can doc trong boi canh lam sang.",
        "why_low": "Gia tri thap thuong khong phai van de dang lo.",
        "patient_friendly_tips": [
            "Mot ket qua tang don le can duoc doc cung cac xet nghiem gan khac va trieu chung.",
        ],
        "follow_up_hints": [
            "xem lai voi bac si neu men gan tang keo dai hoac tang ro",
        ],
        "priority": 65,
    },
}

DEFAULT_TEST_ENTRY: dict[str, Any] = {
    "display_name": "Unknown test",
    "group": "Khac",
    "plain_meaning": "Day la mot chi so can duoc doc trong boi canh gia tri thuc te va khoang tham chieu di kem.",
    "why_high": "Gia tri cao co the can duoc danh gia them tuy boi canh.",
    "why_low": "Gia tri thap co the can duoc danh gia them tuy boi canh.",
    "patient_friendly_tips": ["Nen doi chieu voi khoang tham chieu va cac xet nghiem lien quan."],
    "follow_up_hints": ["trao doi them voi bac si neu co trieu chung hoac lo lang"],
    "priority": 20,
}

TEST_CODE_ALIASES: dict[str, str] = {
    "HBA1C": "HBA1C",
    "A1C": "HBA1C",
    "HB_A1C": "HBA1C",
    "GLUCOSE_F": "GLUCOSE_F",
    "GLUCOSE_FASTING": "GLUCOSE_F",
    "FASTING_GLUCOSE": "GLUCOSE_F",
    "FBS": "GLUCOSE_F",
    "LDL": "LDL",
    "LDL_CHOLESTEROL": "LDL",
    "CREATININE": "CREATININE",
    "CRE": "CREATININE",
    "HGB": "HGB",
    "HEMOGLOBIN": "HGB",
    "HB": "HGB",
    "WBC": "WBC",
    "LEUKOCYTE": "WBC",
    "PLT": "PLATELET",
    "PLATELET": "PLATELET",
    "AST": "AST",
    "SGOT": "AST",
}

FLAG_ALIASES = {
    "H": "HIGH",
    "HIGH": "HIGH",
    "L": "LOW",
    "LOW": "LOW",
    "N": "NORMAL",
    "NORMAL": "NORMAL",
    "CRITICAL": "CRITICAL",
    "PANIC": "CRITICAL",
    "HH": "CRITICAL_HIGH",
    "LL": "CRITICAL_LOW",
    "CRITICAL_HIGH": "CRITICAL_HIGH",
    "CRITICAL_LOW": "CRITICAL_LOW",
    "ABNORMAL": "ABNORMAL",
}


def _pick_first(source: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return default


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _to_float(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    return int(number) if number.is_integer() else number


def canonicalize_test_code(test_code: str | None, test_name: str | None = None) -> str:
    candidates = [test_code or "", test_name or ""]
    for raw in candidates:
        key = raw.strip().upper().replace("-", "_").replace(" ", "_")
        if key in TEST_CODE_ALIASES:
            return TEST_CODE_ALIASES[key]
    if test_code:
        return str(test_code).strip().upper().replace(" ", "_")
    if test_name:
        return str(test_name).strip().upper().replace(" ", "_")
    return "UNKNOWN"


def get_lab_entry(test_code: str | None, test_name: str | None = None) -> dict[str, Any]:
    canonical_code = canonicalize_test_code(test_code, test_name)
    entry = LAB_KB.get(canonical_code)
    if entry:
        result = deepcopy(entry)
        result["canonical_code"] = canonical_code
        return result
    result = deepcopy(DEFAULT_TEST_ENTRY)
    result["display_name"] = test_name or test_code or DEFAULT_TEST_ENTRY["display_name"]
    result["canonical_code"] = canonical_code
    return result


def normalize_flag(
    flag: str | None,
    value: Any = None,
    ref_low: Any = None,
    ref_high: Any = None,
    critical_low: Any = None,
    critical_high: Any = None,
) -> str:
    explicit = FLAG_ALIASES.get(str(flag).strip().upper()) if flag is not None else None
    if explicit in {"HIGH", "LOW", "NORMAL", "CRITICAL_LOW", "CRITICAL_HIGH"}:
        return explicit

    value_num = _to_float(value)
    low_num = _to_float(ref_low)
    high_num = _to_float(ref_high)
    crit_low_num = _to_float(critical_low)
    crit_high_num = _to_float(critical_high)

    if isinstance(value_num, (int, float)):
        if isinstance(crit_low_num, (int, float)) and value_num <= crit_low_num:
            return "CRITICAL_LOW"
        if isinstance(crit_high_num, (int, float)) and value_num >= crit_high_num:
            return "CRITICAL_HIGH"
        if isinstance(low_num, (int, float)) and value_num < low_num:
            return "LOW"
        if isinstance(high_num, (int, float)) and value_num > high_num:
            return "HIGH"
        if isinstance(low_num, (int, float)) or isinstance(high_num, (int, float)):
            return "NORMAL"

    if explicit == "CRITICAL":
        return "CRITICAL_HIGH"
    if explicit == "ABNORMAL":
        return "HIGH"
    return "UNKNOWN"


def normalize_lab_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    test_code = _pick_first(raw_result, ["test_code", "code", "loinc_code", "exam_code", "id"], "")
    test_name = _pick_first(raw_result, ["test_name", "name", "display_name", "label"], "")
    value = _pick_first(raw_result, ["value", "result_value", "numeric_value", "result"])
    unit = _pick_first(raw_result, ["unit", "result_unit", "units"], "")
    ref_low = _pick_first(raw_result, ["ref_low", "reference_low", "range_low", "normal_low"])
    ref_high = _pick_first(raw_result, ["ref_high", "reference_high", "range_high", "normal_high"])
    critical_low = _pick_first(raw_result, ["critical_low"])
    critical_high = _pick_first(raw_result, ["critical_high"])

    canonical_code = canonicalize_test_code(str(test_code or ""), str(test_name or ""))
    kb = get_lab_entry(canonical_code, str(test_name or ""))
    normalized_flag = normalize_flag(
        _pick_first(raw_result, ["flag", "abnormal_flag", "status"]),
        value=value,
        ref_low=ref_low,
        ref_high=ref_high,
        critical_low=critical_low,
        critical_high=critical_high,
    )

    return {
        "test_code": canonical_code,
        "test_name": test_name or kb["display_name"],
        "value": _to_float(value),
        "unit": unit,
        "ref_low": _to_float(ref_low),
        "ref_high": _to_float(ref_high),
        "flag": normalized_flag,
        "critical_low": _to_float(critical_low),
        "critical_high": _to_float(critical_high),
        "group": kb["group"],
    }


def normalize_patient_data(patient_data: dict[str, Any]) -> dict[str, Any]:
    patient = deepcopy(patient_data or {})
    conditions = patient.get("conditions") or patient.get("medical_conditions") or patient.get("history") or []
    lab_results = patient.get("lab_results") or patient.get("results") or patient.get("labs") or []

    normalized_results = [normalize_lab_result(item) for item in lab_results if isinstance(item, dict)]
    return {
        "patient_id": _pick_first(patient, ["patient_id", "id", "mrn"], ""),
        "name": _pick_first(patient, ["name", "full_name", "patient_name"], ""),
        "age": _to_float(_pick_first(patient, ["age"], None)),
        "sex": _pick_first(patient, ["sex", "gender"], ""),
        "conditions": [str(item) for item in _to_list(conditions) if str(item).strip()],
        "test_date": str(_pick_first(patient, ["test_date"], "2026-04-08")),
        "lab_results": normalized_results,
    }


def summarize_tests_for_prompt(lab_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for item in lab_results:
        normalized = normalize_lab_result(item)
        kb = get_lab_entry(normalized.get("test_code"), normalized.get("test_name"))
        summaries.append(
            {
                "test_code": normalized["test_code"],
                "test_name": normalized["test_name"],
                "group": kb["group"],
                "plain_meaning": kb["plain_meaning"],
                "why_high": kb["why_high"],
                "why_low": kb["why_low"],
                "tips": kb["patient_friendly_tips"],
                "follow_up_hints": kb["follow_up_hints"],
                "priority": kb["priority"],
                "flag": normalized["flag"],
                "value": normalized["value"],
                "unit": normalized["unit"],
                "ref_low": normalized["ref_low"],
                "ref_high": normalized["ref_high"],
            }
        )
    return summaries


def load_system_prompt(node_name: str, fallback_text: str) -> str:
    try:
        raw_text = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raw_text = ""

    if not raw_text:
        return fallback_text

    sections: dict[str, list[str]] = {"shared": []}
    current = "shared"
    for line in raw_text.splitlines():
        match = re.fullmatch(r"\[([a-zA-Z0-9_]+)\]", line.strip())
        if match:
            current = match.group(1)
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    shared_text = "\n".join(sections.get("shared", [])).strip()
    node_text = "\n".join(sections.get(node_name, [])).strip()
    prompt = "\n\n".join(part for part in (shared_text, node_text) if part).strip()
    return prompt or fallback_text


__all__ = [
    "DEFAULT_DISCLAIMER",
    "SAFE_STYLE_GUIDE",
    "canonicalize_test_code",
    "get_lab_entry",
    "load_system_prompt",
    "normalize_flag",
    "normalize_lab_result",
    "normalize_patient_data",
    "summarize_tests_for_prompt",
]

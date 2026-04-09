"""
Shared data schema for Vinmec Lumina.
All nodes, the UI, and the data layer import from here.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SeverityLevel(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    SEE_DOCTOR = "SEE_DOCTOR"
    CRITICAL = "CRITICAL"


class ResultFlag(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_LOW = "CRITICAL_LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"


class LabResult(BaseModel):
    test_code: str           # e.g. "HBA1C", "WBC"
    test_name: str           # e.g. "HbA1c", "Bạch cầu"
    value: float
    unit: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    flag: ResultFlag = ResultFlag.NORMAL
    critical_low: Optional[float] = None   # override if present in raw data
    severity: Optional[SeverityLevel] = None  # filled by severity_node


class PatientProfile(BaseModel):
    patient_id: str          # "P001", "P002", "P003"
    name: str
    age: int
    sex: str                 # "Nam" | "Nữ"
    conditions: list[str]
    lab_results: list[LabResult]
    test_date: str = "2026-04-08"


class TestExplanation(BaseModel):
    test_code: str
    test_name: str
    value: float
    unit: str
    severity: SeverityLevel
    explanation: str         # plain-Vietnamese explanation from LLM


class ExplanationResult(BaseModel):
    patient_id: str
    overall_severity: SeverityLevel
    summary: str             # 1-line summary
    explanations: list[TestExplanation]
    suggestions: list[str]   # 1–3 follow-up action strings
    is_critical_escalation: bool = False  # True → skip LLM, show hard-coded alert

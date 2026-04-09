"""
Reference ranges, critical thresholds, and severity classification rules.

Consumed by:
  - guard_node  → checks CRITICAL_THRESHOLDS before any LLM call
  - severity_node → maps flag + deviation to SeverityLevel
"""
from __future__ import annotations
from typing import Optional
from src.services.models import SeverityLevel, LabResult, ResultFlag


# ---------------------------------------------------------------------------
# Critical thresholds — trigger immediate escalation, skip LLM
# ---------------------------------------------------------------------------
CRITICAL_THRESHOLDS: dict[str, dict[str, float]] = {
    "HGB":       {"critical_low": 70,   "critical_high": 200},
    "POTASSIUM": {"critical_low": 2.5,  "critical_high": 6.0},
    "GLUCOSE_F": {"critical_low": 2.8,  "critical_high": 25.0},
    "PLATELET":  {"critical_low": 50,   "critical_high": 1000},
    "WBC":       {"critical_low": 2.0,  "critical_high": 30.0},
    "SODIUM":    {"critical_low": 120,  "critical_high": 160},
}

# ---------------------------------------------------------------------------
# Standard reference ranges (fallback if not in the lab result itself)
# Keyed by test_code; sex-specific ranges use sub-keys "M" / "F" / "any"
# ---------------------------------------------------------------------------
REFERENCE_RANGES: dict[str, dict] = {
    "HGB":        {"M": (130, 170), "F": (110, 160), "unit": "g/L"},
    "WBC":        {"any": (4.0, 10.0),               "unit": "×10⁹/L"},
    "PLATELET":   {"any": (150, 400),                "unit": "×10⁹/L"},
    "HBA1C":      {"any": (4.0, 5.6),                "unit": "%"},
    "GLUCOSE_F":  {"any": (3.9, 6.1),                "unit": "mmol/L"},
    "LDL":        {"any": (None, 3.0),               "unit": "mmol/L"},
    "HDL":        {"M": (1.0, None), "F": (1.2, None), "unit": "mmol/L"},
    "TRIGLYCERIDE": {"any": (None, 1.7),             "unit": "mmol/L"},
    "CREATININE": {"M": (62, 106), "F": (44, 97),    "unit": "μmol/L"},
    "AST":        {"any": (0, 40),                   "unit": "U/L"},
    "ALT":        {"any": (0, 40),                   "unit": "U/L"},
    "TSH":        {"any": (0.4, 4.0),                "unit": "mIU/L"},
    "URIC_ACID":  {"M": (200, 420), "F": (140, 360), "unit": "μmol/L"},
}


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------

def _deviation_pct(value: float, ref_low: Optional[float], ref_high: Optional[float]) -> float:
    """Return how far outside the reference range a value is, as a percentage of range width."""
    if ref_low is not None and ref_high is not None and ref_high > ref_low:
        range_width = ref_high - ref_low
        if value < ref_low:
            return (ref_low - value) / range_width * 100
        if value > ref_high:
            return (value - ref_high) / range_width * 100
    elif ref_high is not None and value > ref_high:
        return (value - ref_high) / ref_high * 100
    elif ref_low is not None and value < ref_low:
        return (ref_low - value) / ref_low * 100
    return 0.0


def classify_severity(result: LabResult) -> SeverityLevel:
    """
    Rule-based severity for a single LabResult.

    Priority:
      1. CRITICAL_LOW / CRITICAL_HIGH flag → CRITICAL
      2. Value crosses a known critical threshold → CRITICAL
      3. HIGH / LOW with deviation > 50 % of range → SEE_DOCTOR
      4. HIGH / LOW with deviation ≤ 50 % → WATCH
      5. NORMAL → NORMAL
    """
    # 1. Explicit critical flag
    if result.flag in (ResultFlag.CRITICAL_LOW, ResultFlag.CRITICAL_HIGH):
        return SeverityLevel.CRITICAL

    # 2. Check against hard critical thresholds
    thresholds = CRITICAL_THRESHOLDS.get(result.test_code, {})
    if thresholds:
        crit_low = thresholds.get("critical_low")
        crit_high = thresholds.get("critical_high")
        if crit_low is not None and result.value <= crit_low:
            return SeverityLevel.CRITICAL
        if crit_high is not None and result.value >= crit_high:
            return SeverityLevel.CRITICAL

    # 3 & 4. Deviation-based for HIGH / LOW
    if result.flag in (ResultFlag.HIGH, ResultFlag.LOW):
        deviation = _deviation_pct(result.value, result.ref_low, result.ref_high)
        if deviation > 50:
            return SeverityLevel.SEE_DOCTOR
        return SeverityLevel.WATCH

    return SeverityLevel.NORMAL


def classify_overall_severity(results: list[LabResult]) -> SeverityLevel:
    """Return the worst severity across all lab results."""
    order = [SeverityLevel.NORMAL, SeverityLevel.WATCH, SeverityLevel.SEE_DOCTOR, SeverityLevel.CRITICAL]
    worst = SeverityLevel.NORMAL
    for r in results:
        sev = classify_severity(r)
        if order.index(sev) > order.index(worst):
            worst = sev
    return worst

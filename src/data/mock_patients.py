"""
Data loader for mock patient data.

Usage:
    from src.data.mock_patients import get_patient, get_all_patients, PATIENTS

    patient = get_patient("P001")          # PatientProfile
    all_patients = get_all_patients()      # list[PatientProfile]
"""
from __future__ import annotations
import json
from pathlib import Path
from src.services.models import PatientProfile, LabResult, ResultFlag

_DATA_DIR = Path(__file__).parent / "patients"

# ---------------------------------------------------------------------------
# Internal cache — loaded once on first import
# ---------------------------------------------------------------------------
_cache: dict[str, PatientProfile] = {}


def _load_patient_from_file(path: Path) -> PatientProfile:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["lab_results"] = [
        LabResult(
            test_code=r["test_code"],
            test_name=r["test_name"],
            value=float(r["value"]),
            unit=r["unit"],
            ref_low=r.get("ref_low"),
            ref_high=r.get("ref_high"),
            flag=ResultFlag(r.get("flag", "NORMAL")),
            critical_low=r.get("critical_low"),
        )
        for r in raw["lab_results"]
    ]
    return PatientProfile(**raw)


def _ensure_loaded() -> None:
    if _cache:
        return
    for json_file in sorted(_DATA_DIR.glob("P*.json")):
        patient = _load_patient_from_file(json_file)
        _cache[patient.patient_id] = patient


def get_patient(patient_id: str) -> PatientProfile:
    """Return a PatientProfile by ID (e.g. 'P001'). Raises KeyError if not found."""
    _ensure_loaded()
    return _cache[patient_id]


def get_all_patients() -> list[PatientProfile]:
    """Return all patients sorted by patient_id."""
    _ensure_loaded()
    return [_cache[k] for k in sorted(_cache)]


# Convenience dict exposed for direct import
def _build_patients_dict() -> dict[str, PatientProfile]:
    _ensure_loaded()
    return dict(_cache)


PATIENTS: dict[str, PatientProfile] = {}  # populated lazily on first access


def __getattr__(name: str):
    if name == "PATIENTS":
        _ensure_loaded()
        PATIENTS.update(_cache)
        return PATIENTS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

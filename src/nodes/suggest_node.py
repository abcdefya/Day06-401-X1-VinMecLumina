from __future__ import annotations

from typing import Any


def _suggestions_for_severity(severity: str) -> list[str]:
    severity = (severity or "NORMAL").upper()
    if severity == "CRITICAL":
        return [
            "Go to the nearest medical facility immediately.",
            "Do not self-medicate. Bring your test report for urgent review.",
            "Contact Vinmec support or your doctor right away.",
        ]
    if severity == "SEE_DOCTOR":
        return [
            "Book a doctor appointment within 24-72 hours.",
            "Repeat the relevant tests as instructed by your clinician.",
            "Track symptoms and share them during the consultation.",
        ]
    if severity == "WATCH":
        return [
            "Monitor your condition and keep healthy routines.",
            "Plan follow-up testing based on doctor guidance.",
            "Seek care sooner if new symptoms appear.",
        ]
    return [
        "Continue regular health maintenance and periodic checkups.",
        "Keep current lifestyle and medication plan from your doctor.",
    ]


def suggest_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate safe, constrained follow-up suggestions from overall severity.
    """
    if state.get("is_critical"):
        return {"suggestions": _suggestions_for_severity("CRITICAL")}

    overall = state.get("overall_severity", "NORMAL")
    return {"suggestions": _suggestions_for_severity(overall)}

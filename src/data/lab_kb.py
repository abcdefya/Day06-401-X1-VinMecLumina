"""
Small inline knowledge base for common lab tests in MVP scope.
"""

from __future__ import annotations

LAB_KB: dict[str, dict[str, str]] = {
    "HBA1C": {
        "meaning": "Reflects average blood glucose in the last 2-3 months.",
        "high_hint": "May indicate glucose control is not optimal.",
        "low_hint": "Can happen in some uncommon situations and should be reviewed by a doctor.",
        "safe_next_step": "Follow up with your doctor and repeat test as advised.",
    },
    "GLUCOSE_F": {
        "meaning": "Fasting blood glucose after not eating for several hours.",
        "high_hint": "Can suggest elevated blood sugar.",
        "low_hint": "Can indicate low blood sugar and may need urgent attention if symptomatic.",
        "safe_next_step": "Monitor symptoms and seek medical advice.",
    },
    "LDL": {
        "meaning": "Low-density lipoprotein cholesterol.",
        "high_hint": "Higher values are associated with cardiovascular risk.",
        "low_hint": "Lower values are usually acceptable in routine context.",
        "safe_next_step": "Discuss lifestyle and risk management with your doctor.",
    },
    "HGB": {
        "meaning": "Hemoglobin level related to oxygen-carrying capacity of blood.",
        "high_hint": "May be related to dehydration or other conditions.",
        "low_hint": "Can indicate anemia and should be clinically evaluated.",
        "safe_next_step": "See your doctor for context-specific assessment.",
    },
    "WBC": {
        "meaning": "White blood cell count, often related to inflammation or infection.",
        "high_hint": "May suggest inflammation, stress response, or infection.",
        "low_hint": "May suggest reduced immune cell count and needs review.",
        "safe_next_step": "Correlate with symptoms and medical examination.",
    },
    "PLATELET": {
        "meaning": "Platelet count related to blood clotting.",
        "high_hint": "May increase clotting risk in some contexts.",
        "low_hint": "May increase bleeding risk and needs medical review.",
        "safe_next_step": "Consult doctor, especially if bruising/bleeding signs appear.",
    },
    "AST": {
        "meaning": "Liver enzyme that can rise when liver or muscle cells are stressed.",
        "high_hint": "May indicate liver or muscle-related stress.",
        "low_hint": "Usually not clinically significant when isolated and low.",
        "safe_next_step": "Review with physician along with ALT and clinical context.",
    },
    "ALT": {
        "meaning": "Liver enzyme commonly used to monitor liver cell injury.",
        "high_hint": "May suggest liver inflammation or injury.",
        "low_hint": "Usually not clinically significant when low.",
        "safe_next_step": "Recheck and discuss with physician.",
    },
    "CREATININE": {
        "meaning": "Marker used to estimate kidney function.",
        "high_hint": "May suggest reduced kidney filtration in some cases.",
        "low_hint": "Often not concerning alone.",
        "safe_next_step": "Review kidney trend and hydration status with clinician.",
    },
}


def get_kb_entry(test_code: str) -> dict[str, str]:
    """Return KB entry or a neutral fallback when test code is unknown."""
    return LAB_KB.get(
        test_code,
        {
            "meaning": "General lab indicator requiring clinical context.",
            "high_hint": "High value may be clinically relevant depending on context.",
            "low_hint": "Low value may be clinically relevant depending on context.",
            "safe_next_step": "Discuss this result with your doctor.",
        },
    )

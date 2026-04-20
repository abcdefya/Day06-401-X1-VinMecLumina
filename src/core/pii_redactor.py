"""PII redaction for logs — strips names, patient IDs, phones, emails."""
import re

# Use capture groups instead of variable-width lookbehinds
_PATTERNS = [
    # Patient IDs like P001, P-001
    (re.compile(r'\b(P-?\d{3,}|PAT-\d+)\b', re.IGNORECASE), "[PATIENT_ID]"),
    # Vietnamese phone numbers
    (re.compile(r'\b(0|\+84)[1-9]\d{8,9}\b'), "[PHONE]"),
    # Email addresses
    (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), "[EMAIL]"),
    # "name": "..." in JSON — use group so replacement works
    (re.compile(r'("name"\s*:\s*")[^"]{2,50}(")'), r'\1[NAME]\2'),
]

# Known patient names from mock data — redact these explicitly
_KNOWN_NAMES = [
    "Nguyễn Văn An", "Trần Thị Bình", "Lê Hoàng Cường",
    "Phạm Thị Dung", "Võ Minh Đức",
]


def redact(text: str) -> str:
    """Return text with PII replaced by safe placeholders."""
    for name in _KNOWN_NAMES:
        text = text.replace(name, "[NAME]")
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_dict(data: dict) -> dict:
    """Recursively redact PII from a dict (for structured log payloads)."""
    import json
    return json.loads(redact(json.dumps(data, ensure_ascii=False)))

"""Append-only JSONL metrics store for observability dashboard."""
import json
import os
import time
from pathlib import Path
from typing import Any

METRICS_PATH = Path("metrics/metrics.jsonl")


def _ensure_dir():
    METRICS_PATH.parent.mkdir(exist_ok=True)


def record(event_type: str, data: dict[str, Any]):
    _ensure_dir()
    entry = {"ts": time.time(), "event": event_type, **data}
    with open(METRICS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_all() -> list[dict]:
    if not METRICS_PATH.exists():
        return []
    records = []
    with open(METRICS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

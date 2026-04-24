"""Episodic memory: JSON log of conversation episodes with timestamps."""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class EpisodicMemory:
    """
    Append-only JSON log of conversation episodes.
    Each episode captures: timestamp, session_id, turn, role, content, intent, metadata.
    """

    def __init__(self, session_id: str = "default", log_dir: str = "lab17/data"):
        self.session_id = session_id
        self.log_path = Path(log_dir) / f"episodic_{session_id}.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._turn = 0

    def log(self, role: str, content: str, intent: str = "unknown", metadata: dict | None = None) -> None:
        self._turn += 1
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "session": self.session_id,
            "turn": self._turn,
            "role": role,
            "content": content,
            "intent": intent,
            "meta": metadata or {},
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recall(self, n: int = 5, intent_filter: str | None = None) -> list[dict[str, Any]]:
        """Return the last n episodes, optionally filtered by intent."""
        episodes = self._load_all()
        if intent_filter:
            episodes = [e for e in episodes if e.get("intent") == intent_filter]
        return episodes[-n:]

    def recall_by_keyword(self, keyword: str, n: int = 5) -> list[dict[str, Any]]:
        """Return episodes whose content contains keyword."""
        episodes = self._load_all()
        matched = [e for e in episodes if keyword.lower() in e.get("content", "").lower()]
        return matched[-n:]

    def _load_all(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        with open(self.log_path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def clear(self) -> None:
        if self.log_path.exists():
            self.log_path.unlink()
        self._turn = 0

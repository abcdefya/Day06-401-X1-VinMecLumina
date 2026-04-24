"""Short-term memory: ConversationBufferMemory (in-memory deque, auto-trimmed)."""
from __future__ import annotations
from collections import deque
from typing import Any
import tiktoken


MAX_TOKENS = 2000
PRIORITY_LEVELS = {"critical": 4, "important": 3, "normal": 2, "background": 1}


class ShortTermMemory:
    """ConversationBufferMemory with token-aware auto-trim and 4-level priority eviction."""

    def __init__(self, max_tokens: int = MAX_TOKENS, max_turns: int = 20):
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self._buffer: deque[dict[str, Any]] = deque(maxlen=max_turns)
        self._enc = tiktoken.get_encoding("cl100k_base")

    def add(self, role: str, content: str, priority: str = "normal") -> None:
        entry = {
            "role": role,
            "content": content,
            "priority": priority,
            "tokens": len(self._enc.encode(content)),
        }
        self._buffer.append(entry)
        self._auto_trim()

    def get_messages(self) -> list[dict[str, str]]:
        return [{"role": m["role"], "content": m["content"]} for m in self._buffer]

    def total_tokens(self) -> int:
        return sum(m["tokens"] for m in self._buffer)

    def _auto_trim(self) -> None:
        """Evict lowest-priority messages when over token budget."""
        while self.total_tokens() > self.max_tokens and len(self._buffer) > 1:
            # Find lowest priority item (keep most recent if tie)
            min_priority = min(PRIORITY_LEVELS[m["priority"]] for m in self._buffer)
            for i, msg in enumerate(self._buffer):
                if PRIORITY_LEVELS[msg["priority"]] == min_priority:
                    del self._buffer[i]
                    break

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)

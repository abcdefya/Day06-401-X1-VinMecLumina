"""Memory router: classifies query intent and selects appropriate memory backends."""
from __future__ import annotations
import re
from typing import Literal

MemoryType = Literal["short_term", "long_term", "episodic", "semantic", "all"]

# Keyword patterns → memory type
_PREFERENCE_PATTERNS = [
    r"\b(prefer|like|want|favorite|always|usually|setting|option|style|format)\b",
    r"\b(my name|call me|remind me|remember that i)\b",
    r"\b(don'?t|do not|never|always) (want|like|use|do)\b",
]
_FACTUAL_PATTERNS = [
    r"\b(what did (i|you) (say|tell|mention|ask)|what was|earlier|before|previously)\b",
    r"\b(you (said|told|mentioned)|i (said|told|mentioned))\b",
    r"\b(fact|information|data|detail|specific)\b",
]
_EXPERIENCE_PATTERNS = [
    r"\b(last time|in our (last|previous) (conversation|session|chat))\b",
    r"\b(we (discussed|talked|spoke) about|recall|remember when)\b",
    r"\b(history|past|experience|before we)\b",
]
_SEMANTIC_PATTERNS = [
    r"\b(similar|related|like|about|topic|concept|meaning)\b",
    r"\b(find|search|look for|anything about)\b",
]


def classify_intent(query: str) -> MemoryType:
    """
    Route query to the most relevant memory backend.

    Priority (highest first): preference > experience > factual > semantic > short_term
    """
    q = query.lower()
    if any(re.search(p, q) for p in _PREFERENCE_PATTERNS):
        return "long_term"
    if any(re.search(p, q) for p in _EXPERIENCE_PATTERNS):
        return "episodic"
    if any(re.search(p, q) for p in _FACTUAL_PATTERNS):
        return "semantic"
    if any(re.search(p, q) for p in _SEMANTIC_PATTERNS):
        return "semantic"
    return "short_term"


class MemoryRouter:
    """
    Wraps all four memory backends and routes retrieval based on query intent.
    """

    def __init__(self, short_term, long_term, episodic, semantic):
        self.short_term = short_term
        self.long_term = long_term
        self.episodic = episodic
        self.semantic = semantic

    def retrieve(self, query: str) -> dict:
        """
        Retrieve relevant context from the appropriate memory backend(s).
        Returns dict with memory_type, hits, and formatted context string.
        """
        mem_type = classify_intent(query)
        hits = []
        context_parts = []

        if mem_type == "long_term":
            prefs = self.long_term.retrieve_all("preference")
            facts = self.long_term.retrieve_all("fact")
            if prefs:
                context_parts.append("User preferences: " + "; ".join(f"{k}={v}" for k, v in prefs.items()))
                hits.append({"source": "long_term:preference", "count": len(prefs)})
            if facts:
                context_parts.append("Known facts: " + "; ".join(f"{k}={v}" for k, v in facts.items()))
                hits.append({"source": "long_term:fact", "count": len(facts)})

        elif mem_type == "episodic":
            episodes = self.episodic.recall(n=5)
            if episodes:
                ep_texts = [f"[Turn {e['turn']}] {e['role']}: {e['content'][:200]}" for e in episodes]
                context_parts.append("Past conversation episodes:\n" + "\n".join(ep_texts))
                hits.append({"source": "episodic", "count": len(episodes)})

        elif mem_type == "semantic":
            results = self.semantic.query(query, n_results=3)
            if results:
                sem_texts = [r["text"][:300] for r in results]
                context_parts.append("Semantically related facts:\n" + "\n".join(sem_texts))
                hits.append({"source": "semantic", "count": len(results)})

        # Always include short-term buffer as baseline context
        recent = self.short_term.get_messages()[-6:]
        if recent:
            recent_texts = [f"{m['role']}: {m['content'][:150]}" for m in recent]
            context_parts.append("Recent conversation:\n" + "\n".join(recent_texts))

        return {
            "memory_type": mem_type,
            "hits": hits,
            "context": "\n\n".join(context_parts),
            "hit_count": sum(h["count"] for h in hits),
        }

    def store_turn(self, role: str, content: str, intent: str = "unknown") -> None:
        """Persist a conversation turn to all relevant backends."""
        # Always log to short-term and episodic
        priority = "important" if role == "assistant" else "normal"
        self.short_term.add(role, content, priority=priority)
        self.episodic.log(role, content, intent=intent)

        # Store to semantic for future similarity queries
        self.semantic.store(content, metadata={"role": role, "intent": intent})

        # Extract and store preferences / facts to long-term
        self._extract_to_longterm(role, content)

    def _extract_to_longterm(self, role: str, content: str) -> None:
        """Simple rule-based extraction of preferences and facts from user messages."""
        if role != "user":
            return
        text = content.lower()
        # Preference detection
        if re.search(r"(my name is|call me)\s+(\w+)", text):
            m = re.search(r"(my name is|call me)\s+(\w+)", text)
            if m:
                self.long_term.store("preference", "name", m.group(2))
        if "prefer" in text or "i like" in text:
            self.long_term.store("preference", "preference_hint", content[:200])
        # Fact detection
        fact_match = re.search(r"(i am|i'm)\s+(\d+)\s+years? old", text)
        if fact_match:
            self.long_term.store("fact", "age", fact_match.group(2))
        if "i work" in text or "my job" in text:
            self.long_term.store("fact", "job_context", content[:200])

"""Semantic memory: Chroma vector store for similarity-based fact retrieval."""
from __future__ import annotations
import hashlib
import os
from typing import Any

from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.utils.embedding_functions import register_embedding_function


@register_embedding_function
class _SimpleEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Deterministic hash-based embedding for offline/no-key use.
    Projects text to 384-dim float vector via SHA-256 chunking.
    """

    def __init__(self) -> None:
        pass

    @classmethod
    def name(cls) -> str:
        return "simple_hash_embedding"

    def get_config(self) -> dict:
        return {}

    @classmethod
    def build_from_config(cls, config: dict) -> "_SimpleEmbeddingFunction":
        return cls()

    def __call__(self, input: Documents) -> Embeddings:
        results = []
        for text in input:
            dim = 384
            vec = []
            for i in range(dim):
                seed = f"{text}_{i}"
                h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
                vec.append((h % 2001 - 1000) / 1000.0)
            results.append(vec)
        return results


class SemanticMemory:
    """
    Chroma-backed semantic memory.
    Uses OpenAI embeddings when OPENAI_API_KEY is set, otherwise a simple hash-based fallback.
    """

    def __init__(self, session_id: str = "default", persist_dir: str = "lab17/data/chroma"):
        self.session_id = session_id
        self._ef = self._build_embedding_function()
        self._collection = self._init_collection(persist_dir, session_id)
        self._doc_count = 0

    def _build_embedding_function(self):
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
        if api_key:
            try:
                from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
                api_base = "https://models.inference.ai.azure.com" if os.getenv("GITHUB_TOKEN") and not os.getenv("OPENAI_API_KEY") else None
                kwargs = {"api_key": api_key, "model_name": "text-embedding-3-small"}
                if api_base:
                    kwargs["api_base"] = api_base
                return OpenAIEmbeddingFunction(**kwargs)
            except Exception:
                pass
        return _SimpleEmbeddingFunction()

    def _init_collection(self, persist_dir: str, session_id: str):
        import chromadb
        client = chromadb.PersistentClient(path=persist_dir)
        # Pass embedding function to avoid auto-downloading ONNX model
        col_name = f"sem_{session_id[:30]}"
        try:
            return client.get_or_create_collection(
                name=col_name,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            return client.get_or_create_collection(
                name=col_name,
                embedding_function=self._ef,
            )

    def store(self, text: str, metadata: dict | None = None) -> str:
        self._doc_count += 1
        doc_id = f"{self.session_id}_{self._doc_count}"
        try:
            self._collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
        except Exception:
            pass
        return doc_id

    def query(self, query_text: str, n_results: int = 3) -> list[dict[str, Any]]:
        try:
            count = self._collection.count()
            if count == 0:
                return []
            results = self._collection.query(
                query_texts=[query_text],
                n_results=min(n_results, count),
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            return [
                {"text": d, "meta": m, "distance": round(dist, 4)}
                for d, m, dist in zip(docs, metas, distances)
            ]
        except Exception:
            return []

    def clear(self) -> None:
        try:
            col_name = f"sem_{self.session_id[:30]}"
            import chromadb
            # Recreate to clear
        except Exception:
            pass

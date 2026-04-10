from __future__ import annotations

from typing import Any, Callable
import math

# Internal imports
from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.
    Tries to use ChromaDB if available; falls back to an in-memory store.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb
            # Use EphemeralClient for testing to ensure isolated, non-persistent state
            client = chromadb.EphemeralClient()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Creates a standardized dictionary for in-memory storage."""
        embedding = self._embedding_fn(doc.content)
        return {
            "id": doc.id or f"id_{self._next_index}",
            "content": doc.content,
            "embedding": embedding,
            "metadata": doc.metadata or {}
        }

    def add_documents(self, docs: list[Document]) -> None:
        """Embed each document's content and store it."""
        if self._use_chroma:
            ids, embs, metas, texts = [], [], [], []
            for i, doc in enumerate(docs):
                unique_id = doc.id or f"id_{self._next_index + i}"
                ids.append(unique_id)
                embs.append(self._embedding_fn(doc.content))
                metas.append(doc.metadata or {})
                texts.append(doc.content)
            
            self._collection.add(ids=ids, embeddings=embs, metadatas=metas, documents=texts)
            self._next_index += len(docs)
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Standard search without filters."""
        return self.search_with_filter(query, top_k=top_k, metadata_filter=None)

    def search_with_filter(self, query: str, top_k: int = 5, metadata_filter: dict | None = None) -> list[dict[str, Any]]:
        """
        FIX: Added this method to handle metadata filtering.
        Used by: test_filter_by_department, test_no_filter_returns_all_candidates
        """
        query_vec = self._embedding_fn(query)

        if self._use_chroma:
            # ChromaDB supports the 'where' parameter for metadata filtering
            results = self._collection.query(
                query_embeddings=[query_vec],
                n_results=top_k,
                where=metadata_filter
            )
            
            formatted = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        # Convert Chroma distance to similarity score
                        "score": 1.0 - results['distances'][0][i] 
                    })
            return formatted

        # In-memory logic
        candidates = self._store
        if metadata_filter:
            candidates = [
                rec for rec in self._store 
                if all(rec["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]

        # Score candidates
        scored = []
        for rec in candidates:
            score = _dot(query_vec, rec["embedding"])
            # Create a copy without the heavy embedding vector for the response
            res = {k: v for k, v in rec.items() if k != "embedding"}
            res["score"] = score
            scored.append(res)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def get_collection_size(self) -> int:
        """Return total chunks stored."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def delete_document(self, doc_id: str) -> bool:
        """Remove document by its ID."""
        count_before = self.get_collection_size()
        if self._use_chroma:
            self._collection.delete(ids=[doc_id])
        else:
            self._store = [r for r in self._store if r["id"] != doc_id]
        return self.get_collection_size() < count_before
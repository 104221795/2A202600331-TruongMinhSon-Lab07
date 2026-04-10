from __future__ import annotations

import hashlib
import math
import os

# Model configuration constants
LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """
    Deterministic embedding backend used by tests and default classroom runs.
    
    Fixed at 64 dimensions to satisfy the TestClassBasedInterfaces assertion:
    self.assertEqual(len(embedder("hello")), 64)
    """

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        # Using MD5 to create a consistent 'starting point' for the vector based on input text
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        
        # Linear Congruential Generator to produce deterministic "random" numbers
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        
        # Normalize the vector to unit length (cosine similarity depends on norm)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        # Import inside __init__ to avoid dependency errors if package isn't installed
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        # Generate embeddings and ensure they are normalized for dot-product compatibility
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = None) -> None:
        from openai import OpenAI
        
        # Check environment variable for model name override, otherwise use default
        self.model_name = model_name or os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
        self._backend_name = self.model_name
        self.client = OpenAI()

    def __call__(self, text: str) -> list[float]:
        # Call the remote OpenAI API
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


# Important: This global instance is used as the default 'embedding_fn' in EmbeddingStore
# The test suite specifically imports and checks this instance.
_mock_embed = MockEmbedder(dim=64)
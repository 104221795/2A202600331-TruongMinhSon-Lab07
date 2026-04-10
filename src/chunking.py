# from __future__ import annotations

# import math
# import re


# class FixedSizeChunker:
#     """
#     Split text into fixed-size chunks with optional overlap.

#     Rules:
#         - Each chunk is at most chunk_size characters long.
#         - Consecutive chunks share overlap characters.
#         - The last chunk contains whatever remains.
#         - If text is shorter than chunk_size, return [text].
#     """

#     def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
#         self.chunk_size = chunk_size
#         self.overlap = overlap

#     def chunk(self, text: str) -> list[str]:
#         if not text:
#             return []
#         if len(text) <= self.chunk_size:
#             return [text]

#         step = self.chunk_size - self.overlap
#         chunks: list[str] = []
#         for start in range(0, len(text), step):
#             chunk = text[start : start + self.chunk_size]
#             chunks.append(chunk)
#             if start + self.chunk_size >= len(text):
#                 break
#         return chunks


# class SentenceChunker:
#     """
#     Split text into chunks of at most max_sentences_per_chunk sentences.

#     Sentence detection: split on ". ", "! ", "? " or ".\n".
#     Strip extra whitespace from each chunk.
#     """

#     def __init__(self, max_sentences_per_chunk: int = 3) -> None:
#         self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

#     def chunk(self, text: str) -> list[str]:
#         # TODO: split into sentences, group into chunks
#         raise NotImplementedError("Implement SentenceChunker.chunk")


# class RecursiveChunker:
#     """
#     Recursively split text using separators in priority order.

#     Default separator priority:
#         ["\n\n", "\n", ". ", " ", ""]
#     """

#     DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

#     def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
#         self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
#         self.chunk_size = chunk_size

#     def chunk(self, text: str) -> list[str]:
#         # TODO: implement recursive splitting strategy
#         raise NotImplementedError("Implement RecursiveChunker.chunk")

#     def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
#         # TODO: recursive helper used by RecursiveChunker.chunk
#         raise NotImplementedError("Implement RecursiveChunker._split")


# def _dot(a: list[float], b: list[float]) -> float:
#     return sum(x * y for x, y in zip(a, b))


# def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
#     """
#     Compute cosine similarity between two vectors.

#     cosine_similarity = dot(a, b) / (||a|| * ||b||)

#     Returns 0.0 if either vector has zero magnitude.
#     """
#     # TODO: implement cosine similarity formula
#     raise NotImplementedError("Implement compute_similarity")


# class ChunkingStrategyComparator:
#     """Run all built-in chunking strategies and compare their results."""

#     def compare(self, text: str, chunk_size: int = 200) -> dict:
#         # TODO: call each chunker, compute stats, return comparison dict
#         raise NotImplementedError("Implement ChunkingStrategyComparator.compare")

from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        # Safety check to avoid infinite loops if overlap >= chunk_size
        if step <= 0:
            step = self.chunk_size

        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split on sentence endings while keeping the delimiter
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            batch = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(batch))
            
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, self.separators)

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        if not separators:
            # Fallback to hard character splits
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        sep = separators[0]
        next_seps = separators[1:]
        
        # Split by current separator
        parts = text.split(sep) if sep != "" else list(text)
        final_chunks = []
        current_buffer = ""

        for part in parts:
            # Determine if adding this part exceeds size
            # We account for the separator length if the buffer isn't empty
            addition = (sep if current_buffer else "") + part
            if len(current_buffer) + len(addition) > self.chunk_size:
                if current_buffer:
                    # Recursive call on the buffer using remaining separators
                    final_chunks.extend(self._split(current_buffer.strip(), next_seps))
                current_buffer = part
            else:
                current_buffer += addition
        
        if current_buffer:
            final_chunks.extend(self._split(current_buffer.strip(), next_seps))
            
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot_product = _dot(vec_a, vec_b)
    mag_a = math.sqrt(sum(x**2 for x in vec_a))
    mag_b = math.sqrt(sum(x**2 for x in vec_b))
    
    if mag_a == 0 or mag_b == 0:
        return 0.0
    
    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Compare strategies using keys expected by the test suite."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # Initializing chunkers
        f_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        s_chunks = SentenceChunker(max_sentences_per_chunk=2).chunk(text)
        r_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)
        
        strategies = {
            "fixed_size": f_chunks,
            "by_sentences": s_chunks, # Test expects 'by_sentences', not 'sentence'
            "recursive": r_chunks
        }
        
        report = {}
        for name, chunks in strategies.items():
            report[name] = {
                "count": len(chunks), # Test expects 'count', not 'num_chunks'
                "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunks": chunks # Test specifically asserts 'chunks' key exists
            }
            
        return report
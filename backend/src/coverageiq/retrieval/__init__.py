"""Retrieval: one interface, several backends (see ADR-0001)."""

from coverageiq.retrieval.base import Chunk, Query, RetrievedChunk, Retriever
from coverageiq.retrieval.bm25 import BM25Retriever
from coverageiq.retrieval.fusion import reciprocal_rank_fusion

__all__ = [
    "BM25Retriever",
    "Chunk",
    "Query",
    "RetrievedChunk",
    "Retriever",
    "reciprocal_rank_fusion",
]

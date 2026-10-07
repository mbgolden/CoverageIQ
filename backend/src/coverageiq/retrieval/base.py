"""The retrieval interface shared by every backend.

A retriever takes a question scoped to one plan and plan year and returns
ranked chunks. Filtering by plan and year happens inside the retriever,
before ranking, so a chunk from another plan can never be returned
(SCOPE.md, "Hybrid retrieval").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

DocType = Literal["sbc", "formulary", "prior_auth"]


@dataclass(frozen=True)
class Chunk:
    """One retrievable piece of a plan document, with the metadata every answer cites."""

    chunk_id: str
    text: str
    plan_id: str
    plan_year: int
    doc_type: DocType
    doc_version: str
    section: str
    page: int


@dataclass(frozen=True)
class Query:
    text: str
    plan_id: str
    plan_year: int


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float
    source: str
    """Which backend produced the score: "bm25", "vector" or "fused"."""


class Retriever(Protocol):
    def retrieve(self, query: Query, k: int = 10) -> list[RetrievedChunk]:
        """Return at most k chunks for the query's plan and year, best first."""
        ...

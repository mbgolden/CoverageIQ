"""Reciprocal rank fusion: combine ranked lists from several retrievers."""

from __future__ import annotations

from collections.abc import Sequence

from coverageiq.retrieval.base import RetrievedChunk


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[RetrievedChunk]], *, k: int = 60, limit: int | None = None
) -> list[RetrievedChunk]:
    """Fuse rankings by summing 1 / (k + rank) for each chunk across lists.

    A chunk that appears high in several lists beats one that appears high in
    only one. k = 60 is the value from the original paper and a common
    default; it damps the advantage of the very top ranks.
    """
    scores: dict[str, float] = {}
    chunks: dict[str, RetrievedChunk] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            cid = item.chunk.chunk_id
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            chunks.setdefault(cid, item)
    fused = [
        RetrievedChunk(chunk=chunks[cid].chunk, score=score, source="fused")
        for cid, score in scores.items()
    ]
    fused.sort(key=lambda r: (-r.score, r.chunk.chunk_id))
    return fused[:limit] if limit is not None else fused

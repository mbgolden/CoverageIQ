"""Did retrieval find the right chunk, and did it avoid the wrong plan's?

Scored per item, then summarized per question type, because the scope's
ablation table (vector only, BM25 only, hybrid, hybrid plus reranker) is
broken out that way: drug names and procedure codes are where semantic
search alone is expected to fall short.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from coverageiq.evals.golden import GoldenItem
from coverageiq.retrieval.base import RetrievedChunk, Retriever


@dataclass(frozen=True)
class RetrievalScore:
    item_id: str
    question_type: str
    hit: bool
    """At least one expected chunk is in the top k."""
    recall: float
    """Fraction of expected chunks in the top k (1.0 when nothing was expected)."""
    reciprocal_rank: float
    """1 / rank of the first expected chunk, 0.0 when none was retrieved or expected."""
    forbidden_hit: bool
    """A chunk from forbidden_chunk_ids (the wrong plan) is in the top k."""


@dataclass(frozen=True)
class RetrievalSummary:
    n: int
    hit_rate: float
    mean_recall: float
    mrr: float
    forbidden_rate: float


def score_retrieval(
    item: GoldenItem, retrieved: Sequence[RetrievedChunk], *, k: int
) -> RetrievalScore:
    if not item.scores_retrieval:
        raise ValueError(f"{item.item_id}: a {item.kind} item has no retrieval metrics")
    top = [r.chunk.chunk_id for r in retrieved[:k]]
    expected = item.expected_chunk_ids
    found = [cid for cid in top if cid in expected]
    first_rank = next((i + 1 for i, cid in enumerate(top) if cid in expected), None)
    return RetrievalScore(
        item_id=item.item_id,
        question_type=item.question_type,
        hit=bool(found),
        recall=(len(set(found)) / len(expected)) if expected else 1.0,
        reciprocal_rank=(1.0 / first_rank) if first_rank else 0.0,
        forbidden_hit=any(cid in item.forbidden_chunk_ids for cid in top),
    )


def evaluate_retrieval(
    retriever: Retriever, items: Iterable[GoldenItem], *, k: int = 10
) -> list[RetrievalScore]:
    """Run every scorable item through the retriever and score the top k."""
    return [
        score_retrieval(item, retriever.retrieve(item.to_query(), k=k), k=k)
        for item in items
        if item.scores_retrieval
    ]


def summarize(scores: Iterable[RetrievalScore]) -> dict[str, RetrievalSummary]:
    """Aggregate per question type, plus an ``"all"`` row."""
    groups: dict[str, list[RetrievalScore]] = defaultdict(list)
    for s in scores:
        groups[s.question_type].append(s)
        groups["all"].append(s)
    return {name: _summarize_group(group) for name, group in sorted(groups.items())}


def _summarize_group(group: Sequence[RetrievalScore]) -> RetrievalSummary:
    n = len(group)
    return RetrievalSummary(
        n=n,
        hit_rate=sum(s.hit for s in group) / n,
        mean_recall=sum(s.recall for s in group) / n,
        mrr=sum(s.reciprocal_rank for s in group) / n,
        forbidden_rate=sum(s.forbidden_hit for s in group) / n,
    )

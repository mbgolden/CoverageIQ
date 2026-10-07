"""The evaluation harness (SCOPE.md, section 5).

Two things are measured separately: whether retrieval found the right
chunk, and whether the generated answer only claims what the chunk says.
This package starts with the first.
"""

from coverageiq.evals.golden import GoldenItem, Kind, QuestionType, load_golden
from coverageiq.evals.retrieval_metrics import (
    RetrievalScore,
    RetrievalSummary,
    evaluate_retrieval,
    score_retrieval,
    summarize,
)

__all__ = [
    "GoldenItem",
    "Kind",
    "QuestionType",
    "RetrievalScore",
    "RetrievalSummary",
    "evaluate_retrieval",
    "load_golden",
    "score_retrieval",
    "summarize",
]

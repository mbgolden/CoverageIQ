import pytest

from coverageiq.evals import (
    GoldenItem,
    QuestionType,
    evaluate_retrieval,
    score_retrieval,
    summarize,
)
from coverageiq.retrieval import BM25Retriever, Chunk, RetrievedChunk
from tests.conftest import chunk


def retrieved(*ids: str) -> list[RetrievedChunk]:
    return [RetrievedChunk(chunk=chunk(cid, cid), score=1.0, source="bm25") for cid in ids]


def answerable(item_id: str, *expected: str, question_type: QuestionType = "drug") -> GoldenItem:
    return GoldenItem(
        item_id, "q", "plan-a", 2026, "answerable", question_type, frozenset(expected)
    )


def test_hit_recall_and_reciprocal_rank() -> None:
    score = score_retrieval(
        answerable("q", "want-1", "want-2"), retrieved("x", "want-1", "y"), k=10
    )
    assert score.hit is True
    assert score.recall == 0.5
    assert score.reciprocal_rank == 0.5
    assert score.forbidden_hit is False


def test_only_the_top_k_counts() -> None:
    score = score_retrieval(answerable("q", "want"), retrieved("a", "b", "want"), k=2)
    assert score.hit is False
    assert score.recall == 0.0
    assert score.reciprocal_rank == 0.0


def test_wrong_plan_trap_records_the_forbidden_hit() -> None:
    trap = GoldenItem(
        "t",
        "q",
        "plan-a",
        2026,
        "wrong_plan_trap",
        "drug",
        forbidden_chunk_ids=frozenset({"b-ozempic"}),
    )
    score = score_retrieval(trap, retrieved("b-ozempic"), k=5)
    assert score.forbidden_hit is True
    assert score.recall == 1.0  # nothing was expected, so nothing was missed


def test_unscorable_items_are_rejected() -> None:
    item = GoldenItem("u", "q", "plan-a", 2026, "unanswerable", "general")
    with pytest.raises(ValueError, match="no retrieval metrics"):
        score_retrieval(item, [], k=5)


def test_summary_breaks_out_question_types() -> None:
    scores = [
        score_retrieval(answerable("d1", "want"), retrieved("want"), k=5),
        score_retrieval(answerable("d2", "want"), retrieved("other"), k=5),
        score_retrieval(
            answerable("c1", "want", question_type="procedure_code"), retrieved("x", "want"), k=5
        ),
    ]
    summary = summarize(scores)
    assert set(summary) == {"all", "drug", "procedure_code"}
    assert summary["drug"].n == 2
    assert summary["drug"].hit_rate == 0.5
    assert summary["procedure_code"].mrr == 0.5
    assert summary["all"].n == 3
    assert summary["all"].mean_recall == pytest.approx(2 / 3)


def test_end_to_end_against_bm25(corpus: list[Chunk]) -> None:
    items = [
        GoldenItem(
            "drug",
            "Is Ozempic covered?",
            "plan-a",
            2026,
            "answerable",
            "drug",
            frozenset({"a-ozempic"}),
        ),
        GoldenItem(
            "code",
            "CPT 45378",
            "plan-a",
            2026,
            "answerable",
            "procedure_code",
            frozenset({"a-cpt"}),
        ),
        GoldenItem("clinical", "Should I take Ozempic?", "plan-a", 2026, "out_of_scope", "drug"),
        GoldenItem(
            "trap",
            "Is Ozempic covered?",
            "plan-a",
            2026,
            "wrong_plan_trap",
            "drug",
            expected_chunk_ids=frozenset({"a-ozempic"}),
            forbidden_chunk_ids=frozenset({"b-ozempic", "a-2025-ozempic"}),
        ),
    ]
    scores = evaluate_retrieval(BM25Retriever(corpus), items, k=5)
    assert [s.item_id for s in scores] == ["drug", "code", "trap"]  # out_of_scope is skipped
    summary = summarize(scores)
    assert summary["all"].hit_rate == 1.0
    assert summary["all"].mrr == 1.0
    assert summary["all"].forbidden_rate == 0.0  # plan and year filtering kept the traps out

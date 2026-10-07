from coverageiq.retrieval import Chunk, RetrievedChunk, reciprocal_rank_fusion
from tests.conftest import chunk


def ranked(*ids: str, source: str) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(chunk=chunk(cid, cid), score=float(len(ids) - i), source=source)
        for i, cid in enumerate(ids)
    ]


def test_chunk_in_both_lists_beats_chunk_in_one() -> None:
    fused = reciprocal_rank_fusion(
        [ranked("x", "shared", source="bm25"), ranked("y", "shared", source="vector")]
    )
    assert fused[0].chunk.chunk_id == "shared"
    assert fused[0].source == "fused"


def test_scores_are_summed_reciprocal_ranks() -> None:
    fused = reciprocal_rank_fusion([ranked("a", source="bm25"), ranked("a", source="vector")], k=60)
    assert fused[0].score == 2 / 61


def test_limit_and_empty_input() -> None:
    assert reciprocal_rank_fusion([]) == []
    fused = reciprocal_rank_fusion([ranked("a", "b", "c", source="bm25")], limit=2)
    assert [r.chunk.chunk_id for r in fused] == ["a", "b"]


def test_keeps_chunk_metadata() -> None:
    c: Chunk = chunk("m", "text", plan_id="plan-z", plan_year=2027)
    fused = reciprocal_rank_fusion([[RetrievedChunk(chunk=c, score=1.0, source="bm25")]])
    assert fused[0].chunk.plan_id == "plan-z"
    assert fused[0].chunk.plan_year == 2027

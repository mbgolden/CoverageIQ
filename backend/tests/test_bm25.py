from coverageiq.retrieval import BM25Retriever, Chunk, Query


def test_exact_drug_name_ranks_first(corpus: list[Chunk]) -> None:
    results = BM25Retriever(corpus).retrieve(Query("Is Ozempic covered?", "plan-a", 2026))
    assert results[0].chunk.chunk_id == "a-ozempic"
    assert results[0].source == "bm25"


def test_procedure_code_is_an_exact_match(corpus: list[Chunk]) -> None:
    results = BM25Retriever(corpus).retrieve(Query("45378", "plan-a", 2026))
    assert [r.chunk.chunk_id for r in results] == ["a-cpt"]


def test_other_plans_and_years_are_filtered_out(corpus: list[Chunk]) -> None:
    results = BM25Retriever(corpus).retrieve(Query("Ozempic", "plan-a", 2026))
    ids = {r.chunk.chunk_id for r in results}
    assert "b-ozempic" not in ids
    assert "a-2025-ozempic" not in ids


def test_same_question_different_year_gets_that_years_chunk(corpus: list[Chunk]) -> None:
    results = BM25Retriever(corpus).retrieve(Query("Ozempic", "plan-a", 2025))
    assert [r.chunk.chunk_id for r in results] == ["a-2025-ozempic"]


def test_no_match_returns_nothing(corpus: list[Chunk]) -> None:
    assert BM25Retriever(corpus).retrieve(Query("acupuncture", "plan-a", 2026)) == []


def test_k_limits_results(corpus: list[Chunk]) -> None:
    results = BM25Retriever(corpus).retrieve(Query("visit copay deductible", "plan-a", 2026), k=1)
    assert len(results) == 1


def test_empty_corpus_and_empty_query() -> None:
    assert BM25Retriever([]).retrieve(Query("anything", "plan-a", 2026)) == []
    assert BM25Retriever([]).retrieve(Query("the and of", "plan-a", 2026)) == []

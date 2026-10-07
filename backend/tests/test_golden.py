import json
from pathlib import Path

import pytest

from coverageiq.evals import GoldenItem, load_golden


def test_answerable_item_needs_expected_chunks() -> None:
    with pytest.raises(ValueError, match="expected_chunk_ids"):
        GoldenItem("q1", "What is my deductible?", "plan-a", 2026, "answerable", "benefit_table")


def test_unanswerable_item_cannot_have_expected_chunks() -> None:
    with pytest.raises(ValueError, match="cannot"):
        GoldenItem(
            "q1",
            "Do you cover dental?",
            "plan-a",
            2026,
            "unanswerable",
            "general",
            frozenset({"x"}),
        )


def test_wrong_plan_trap_needs_forbidden_chunks() -> None:
    with pytest.raises(ValueError, match="forbidden_chunk_ids"):
        GoldenItem("q1", "Is Ozempic covered?", "plan-a", 2026, "wrong_plan_trap", "drug")


def test_which_kinds_score_retrieval() -> None:
    assert GoldenItem("a", "q", "p", 2026, "answerable", "drug", frozenset({"c"})).scores_retrieval
    assert GoldenItem(
        "t", "q", "p", 2026, "wrong_plan_trap", "drug", forbidden_chunk_ids=frozenset({"c"})
    ).scores_retrieval
    assert not GoldenItem("u", "q", "p", 2026, "unanswerable", "general").scores_retrieval
    assert not GoldenItem("o", "q", "p", 2026, "out_of_scope", "general").scores_retrieval


def test_to_query_carries_plan_and_year() -> None:
    item = GoldenItem(
        "a", "Is Ozempic covered?", "plan-a", 2025, "answerable", "drug", frozenset({"c"})
    )
    query = item.to_query()
    assert (query.text, query.plan_id, query.plan_year) == ("Is Ozempic covered?", "plan-a", 2025)


def test_load_golden_round_trip(tmp_path: Path) -> None:
    rows = [
        {
            "item_id": "q1",
            "question": "Is Ozempic covered?",
            "plan_id": "plan-a",
            "plan_year": 2026,
            "kind": "answerable",
            "question_type": "drug",
            "expected_chunk_ids": ["a-ozempic"],
        },
        {
            "item_id": "q2",
            "question": "Should I take Ozempic?",
            "plan_id": "plan-a",
            "plan_year": 2026,
            "kind": "out_of_scope",
            "question_type": "drug",
        },
    ]
    path = tmp_path / "golden.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n\n", encoding="utf-8")
    items = load_golden(path)
    assert [i.item_id for i in items] == ["q1", "q2"]
    assert items[0].expected_chunk_ids == frozenset({"a-ozempic"})
    assert items[1].kind == "out_of_scope"


def test_load_golden_rejects_bad_kind_and_duplicates(tmp_path: Path) -> None:
    base = {"question": "q", "plan_id": "p", "plan_year": 2026, "question_type": "general"}
    path = tmp_path / "bad-kind.jsonl"
    path.write_text(json.dumps({**base, "item_id": "x", "kind": "maybe"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown kind"):
        load_golden(path)

    path = tmp_path / "dup.jsonl"
    row = json.dumps({**base, "item_id": "x", "kind": "unanswerable"})
    path.write_text(row + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_golden(path)

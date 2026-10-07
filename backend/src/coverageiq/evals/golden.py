"""The golden set: questions with known-correct sources.

Each item is one line of JSON. The four kinds match the scope:

- ``answerable``: the plan's documents answer it; ``expected_chunk_ids``
  names the chunk(s) a correct answer must cite.
- ``unanswerable``: nothing in the documents answers it; the right
  response is to abstain and route to the plan.
- ``out_of_scope``: a clinical question; the right response is to refuse.
- ``wrong_plan_trap``: another plan's document has a tempting answer, named
  in ``forbidden_chunk_ids``. ``expected_chunk_ids`` holds this plan's
  answer when it has one, and is empty when the right response is to
  abstain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast, get_args

from coverageiq.retrieval.base import Query

Kind = Literal["answerable", "unanswerable", "out_of_scope", "wrong_plan_trap"]
QuestionType = Literal["benefit_table", "drug", "procedure_code", "prior_auth", "general"]


@dataclass(frozen=True)
class GoldenItem:
    item_id: str
    question: str
    plan_id: str
    plan_year: int
    kind: Kind
    question_type: QuestionType
    expected_chunk_ids: frozenset[str] = field(default_factory=frozenset)
    forbidden_chunk_ids: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.kind == "answerable" and not self.expected_chunk_ids:
            raise ValueError(f"{self.item_id}: an answerable item needs expected_chunk_ids")
        if self.kind in ("unanswerable", "out_of_scope") and self.expected_chunk_ids:
            raise ValueError(f"{self.item_id}: a {self.kind} item cannot have expected_chunk_ids")
        if self.kind == "wrong_plan_trap" and not self.forbidden_chunk_ids:
            raise ValueError(f"{self.item_id}: a wrong_plan_trap item needs forbidden_chunk_ids")

    @property
    def scores_retrieval(self) -> bool:
        """Retrieval metrics apply when there is a right chunk to find or a wrong one to avoid."""
        return bool(self.expected_chunk_ids or self.forbidden_chunk_ids)

    def to_query(self) -> Query:
        return Query(text=self.question, plan_id=self.plan_id, plan_year=self.plan_year)


def _item_from_dict(raw: dict[str, Any], *, line_no: int) -> GoldenItem:
    kind = raw.get("kind")
    if kind not in get_args(Kind):
        raise ValueError(f"line {line_no}: unknown kind {kind!r}")
    question_type = raw.get("question_type")
    if question_type not in get_args(QuestionType):
        raise ValueError(f"line {line_no}: unknown question_type {question_type!r}")
    return GoldenItem(
        item_id=str(raw["item_id"]),
        question=str(raw["question"]),
        plan_id=str(raw["plan_id"]),
        plan_year=int(raw["plan_year"]),
        kind=cast(Kind, kind),
        question_type=cast(QuestionType, question_type),
        expected_chunk_ids=frozenset(str(c) for c in raw.get("expected_chunk_ids", [])),
        forbidden_chunk_ids=frozenset(str(c) for c in raw.get("forbidden_chunk_ids", [])),
    )


def load_golden(path: Path) -> list[GoldenItem]:
    """Read a JSONL golden set. Blank lines are skipped; item ids must be unique."""
    items: list[GoldenItem] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            item = _item_from_dict(json.loads(line), line_no=line_no)
            if item.item_id in seen:
                raise ValueError(f"line {line_no}: duplicate item_id {item.item_id!r}")
            seen.add(item.item_id)
            items.append(item)
    return items

import pytest

from coverageiq.retrieval import Chunk


def chunk(chunk_id: str, text: str, *, plan_id: str = "plan-a", plan_year: int = 2026) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        text=text,
        plan_id=plan_id,
        plan_year=plan_year,
        doc_type="sbc",
        doc_version="v1",
        section="test",
        page=1,
    )


@pytest.fixture
def corpus() -> list[Chunk]:
    return [
        chunk("a-deductible", "The overall deductible is $1,500 per person, $3,000 per family."),
        chunk("a-ozempic", "Ozempic (semaglutide) is Tier 3; prior authorization required."),
        chunk("a-office", "Primary care office visit: $25 copay. Specialist visit: $50 copay."),
        chunk("a-cpt", "Colonoscopy, CPT 45378, is covered as preventive at no cost."),
        chunk("a-2025-ozempic", "Ozempic is Tier 2 with no prior authorization.", plan_year=2025),
        chunk("b-ozempic", "Ozempic is not covered under this plan.", plan_id="plan-b"),
    ]

"""The one tokenizer.

Keyword search only works if queries are tokenized exactly as documents were
at ingestion. Every BM25 index and every sparse vector in the project uses
this function, so there is nothing to keep in step.

It lowercases and splits on anything that is not a letter or digit, which
keeps drug names ("ozempic"), procedure codes ("99213", "j1817") and plan
names intact as single terms. No stemming: "deductible" and "deductibles"
are different terms, and that is accepted for now (see docs/BACKLOG.md).

The stopword list has a domain half. In a coverage assistant nearly every
question contains "covered", "cover" or "plan", so those words carry no
signal about which chunk is wanted. The first BM25 test caught this: with
"covered" scored, a chunk about colonoscopy outranked the chunk about the
drug the question named.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")

_GENERAL = (
    "a an and are as at be by do does for from how i in is it my of on or the this to what with"
)
_DOMAIN = "cover coverage covered covers plan plans"

STOPWORDS: frozenset[str] = frozenset(f"{_GENERAL} {_DOMAIN}".split())


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]

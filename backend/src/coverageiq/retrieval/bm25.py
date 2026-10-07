"""In-process BM25 over the chunk corpus.

This is the keyword half of the demo's hybrid retrieval (ADR-0001). The
corpus is a few thousand chunks, so the whole index lives in memory in the
Cloud Run service. Document frequencies are computed over the full corpus;
the plan and year filter is applied before scoring.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable

from coverageiq.retrieval.base import Chunk, Query, RetrievedChunk
from coverageiq.retrieval.tokenize import tokenize


class BM25Retriever:
    def __init__(self, chunks: Iterable[Chunk], *, k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks = list(chunks)
        self._k1 = k1
        self._b = b
        self._term_freqs: list[Counter[str]] = []
        self._lengths: list[int] = []
        doc_freq: Counter[str] = Counter()
        for chunk in self._chunks:
            tokens = tokenize(chunk.text)
            freqs = Counter(tokens)
            self._term_freqs.append(freqs)
            self._lengths.append(len(tokens))
            doc_freq.update(freqs.keys())
        n = len(self._chunks)
        self._avg_len = (sum(self._lengths) / n) if n else 0.0
        self._idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in doc_freq.items()
        }

    def retrieve(self, query: Query, k: int = 10) -> list[RetrievedChunk]:
        terms = tokenize(query.text)
        if not terms:
            return []
        scored: list[RetrievedChunk] = []
        for i, chunk in enumerate(self._chunks):
            if chunk.plan_id != query.plan_id or chunk.plan_year != query.plan_year:
                continue
            score = self._score(i, terms)
            if score > 0:
                scored.append(RetrievedChunk(chunk=chunk, score=score, source="bm25"))
        scored.sort(key=lambda r: (-r.score, r.chunk.chunk_id))
        return scored[:k]

    def _score(self, i: int, terms: list[str]) -> float:
        freqs = self._term_freqs[i]
        length_norm = 1 - self._b + self._b * (self._lengths[i] / self._avg_len)
        score = 0.0
        for term in terms:
            tf = freqs.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf.get(term, 0.0)
            score += idf * (tf * (self._k1 + 1)) / (tf + self._k1 * length_norm)
        return score

"""BM25 sparse retrieval: Elasticsearch `_search` or in-memory Okapi index."""

from __future__ import annotations

import asyncio
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
import httpx

from config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

_token_re = re.compile(r"[a-z0-9]+", re.I)


@dataclass
class BM25Document:
    text: str
    source: str
    score: float


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _token_re.findall(text)]


_memory_lock = asyncio.Lock()
_memory_corpus: list[tuple[str, str]] = []  # (source_id, text)


async def bm25_memory_index_add(source_id: str, text: str) -> None:
    """Append a document to the in-memory corpus (for demos / tests)."""
    async with _memory_lock:
        _memory_corpus.append((source_id, text))


def _memory_bm25_scores(query: str, corpus: list[tuple[str, str]], k1: float = 1.5, b: float = 0.75) -> list[tuple[int, float]]:
    if not corpus:
        return []
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []
    doc_tokens = [_tokenize(t) for _, t in corpus]
    doc_len = [len(toks) for toks in doc_tokens]
    avgdl = sum(doc_len) / len(doc_len) if doc_len else 0.0
    df: dict[str, int] = defaultdict(int)
    for toks in doc_tokens:
        seen = set(toks)
        for t in seen:
            df[t] += 1
    n_docs = len(corpus)
    scores: list[tuple[int, float]] = []
    for i, toks in enumerate(doc_tokens):
        tf: dict[str, int] = defaultdict(int)
        for t in toks:
            tf[t] += 1
        score = 0.0
        dl = doc_len[i]
        for term in q_tokens:
            if term not in tf:
                continue
            idf = math.log((n_docs - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
            f = tf[term]
            denom = f + k1 * (1 - b + b * (dl / avgdl if avgdl else 1.0))
            score += idf * (f * (k1 + 1)) / denom if denom else 0.0
        scores.append((i, score))
    return scores


async def _bm25_memory_search(query: str, top_k: int) -> list[BM25Document]:
    async with _memory_lock:
        corpus = list(_memory_corpus)
    ranked = _memory_bm25_scores(query, corpus)
    ranked.sort(key=lambda x: x[1], reverse=True)
    out: list[BM25Document] = []
    for idx, sc in ranked[:top_k]:
        if sc <= 0:
            continue
        source, text = corpus[idx]
        out.append(BM25Document(text=text, source=source, score=float(sc)))
    return out


async def _bm25_elasticsearch(query: str, top_k: int) -> list[BM25Document]:
    s = get_settings()
    if not s.elasticsearch_url:
        return []
    base = s.elasticsearch_url.rstrip("/")
    url = f"{base}/{s.elasticsearch_index}/_search"
    field = s.elasticsearch_content_field
    body = {"query": {"match": {field: query}}, "size": top_k}
    out: list[BM25Document] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
        for hit in data.get("hits", {}).get("hits", []):
            src = hit.get("_source") or {}
            text = str(src.get(field) or src.get("text") or src.get("content") or "")
            score = float(hit.get("_score") or 0.0)
            out.append(
                BM25Document(
                    text=text or json.dumps(src)[:500],
                    source=str(hit.get("_id") or src.get("source") or "es"),
                    score=score,
                )
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("elasticsearch_bm25_failed: %s", exc)
    return out


async def bm25_search(query: str, top_k: int = 10) -> list[BM25Document]:
    es = await _bm25_elasticsearch(query, top_k)
    if es:
        return es
    mem = await _bm25_memory_search(query, top_k)
    if mem:
        return mem
    return [
        BM25Document(
            text=f"BM25: no index hits for: {query[:120]} (configure ELASTICSEARCH_URL or index via bm25_memory_index_add).",
            source="bm25_empty",
            score=0.0,
        )
    ]


async def bm25_search_stub(query: str, top_k: int = 10) -> list[BM25Document]:
    """Backward-compatible name: delegates to real `bm25_search`."""
    return await bm25_search(query, top_k=top_k)

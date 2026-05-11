"""Corrective RAG: relevance + consistency (post-retrieval middleware)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from config.settings import get_settings
from src.crag.evaluators import consistency_judge, relevance_scores
from src.llm.client import ChatClient


class RelevanceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CRAGResult:
    verified_chunks: list[str]
    confidence_score: float
    has_conflict: bool
    conflict_description: str | None
    triggered_web_search: bool
    reasoning: str


class CRAGModule:
    """Standalone middleware as in v1.1 architecture report (§4)."""

    def __init__(
        self,
        *,
        llm: ChatClient | None = None,
        relevance_threshold: float | None = None,
        web_search_fn=None,
    ) -> None:
        settings = get_settings()
        self._llm = llm
        self.threshold = relevance_threshold if relevance_threshold is not None else settings.crag_relevance_threshold
        self.web_search = web_search_fn

    async def evaluate(self, query: str, retrieved_chunks: list[str]) -> CRAGResult:
        if not retrieved_chunks:
            return CRAGResult(
                verified_chunks=[],
                confidence_score=0.0,
                has_conflict=False,
                conflict_description=None,
                triggered_web_search=bool(self.web_search),
                reasoning="no_chunks",
            )

        scores = await relevance_scores(query, retrieved_chunks, self._llm)
        high = [c for c, s in zip(retrieved_chunks, scores, strict=True) if s >= self.threshold]
        low = [c for c, s in zip(retrieved_chunks, scores, strict=True) if s < self.threshold]
        web_triggered = False
        if len(high) < 2 and self.web_search is not None:
            extra = await self.web_search(query)
            high.extend(extra)
            web_triggered = True
            _ = low

        conflict, desc = await consistency_judge(query, high, self._llm)
        verified = high
        if conflict:
            verified = high[: max(1, min(3, len(high)))]

        overall = sum(scores) / len(scores) if scores else 0.0
        return CRAGResult(
            verified_chunks=verified,
            confidence_score=overall,
            has_conflict=conflict,
            conflict_description=desc,
            triggered_web_search=web_triggered,
            reasoning=f"evaluated={len(retrieved_chunks)} kept={len(verified)}",
        )

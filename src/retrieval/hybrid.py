"""Hybrid fusion (e.g. RRF) for merging ranked lists."""

from __future__ import annotations

from collections import defaultdict


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    Reciprocal Rank Fusion (Cormack et al.). Returns scored items descending.
    """
    scores: dict[str, float] = defaultdict(float)
    for rlist in ranked_lists:
        for rank, item in enumerate(rlist, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


__all__ = ["reciprocal_rank_fusion"]

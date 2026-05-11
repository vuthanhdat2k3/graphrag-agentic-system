"""Unit tests for RRF."""

from src.retrieval.hybrid import reciprocal_rank_fusion


def test_rrf_orders_by_fused_score() -> None:
    ranked = [["a", "b"], ["b", "c"]]
    out = reciprocal_rank_fusion(ranked, k=60)
    assert out[0][0] in {"a", "b"}

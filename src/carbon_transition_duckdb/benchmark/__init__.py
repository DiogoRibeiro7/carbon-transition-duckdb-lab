"""Peer-group benchmarking of transition-risk scores (v0.6).

Score countries *within* a peer group (EU, OECD, an income tier) so risk is
relative to comparable economies, and report where each country sits versus its
peers: rank, percentile, and the gap to the peer median and the peer leader.
"""

from __future__ import annotations

from carbon_transition_duckdb.benchmark.benchmark import (
    benchmark_group,
    benchmark_scores,
)

__all__ = ["benchmark_group", "benchmark_scores"]

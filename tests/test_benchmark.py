"""Tests for peer-group benchmarking."""

import pandas as pd

from carbon_transition_duckdb.benchmark import benchmark_group, benchmark_scores


def _scored() -> pd.DataFrame:
    # Pre-scored frame for a single year; lower score = lower risk = better.
    return pd.DataFrame(
        {
            "country": ["A", "B", "C", "D"],
            "year": [2024, 2024, 2024, 2024],
            "transition_risk_score": [80.0, 60.0, 40.0, 20.0],
        }
    )


def test_benchmark_scores_rank_and_gaps() -> None:
    """Rank, median, and leader gaps are computed correctly."""
    out = benchmark_scores(_scored()).set_index("country")

    # A has the highest score -> rank 1 (highest risk).
    assert out.loc["A", "risk_rank"] == 1
    assert out.loc["D", "risk_rank"] == 4
    # Median of [80,60,40,20] is 50.
    assert out.loc["A", "peer_median"] == 50.0
    assert out.loc["A", "gap_to_median"] == 30.0
    # Leader is the lowest score (20).
    assert out.loc["A", "gap_to_leader"] == 60.0
    assert out.loc["D", "gap_to_leader"] == 0.0


def test_benchmark_percentile_orientation() -> None:
    """The lowest-risk country sits at the top percentile; highest at the bottom."""
    out = benchmark_scores(_scored()).set_index("country")
    assert out.loc["D", "peer_percentile"] == 100.0  # best
    assert out.loc["A", "peer_percentile"] == 0.0  # worst


def test_benchmark_scores_year_selection() -> None:
    """An explicit year filters to that year before benchmarking."""
    frame = pd.DataFrame(
        {
            "country": ["A", "A", "B", "B"],
            "year": [2023, 2024, 2023, 2024],
            "transition_risk_score": [10.0, 90.0, 50.0, 50.0],
        }
    )
    out = benchmark_scores(frame, year=2023).set_index("country")
    assert out.loc["A", "risk_rank"] == 2  # 10 < 50 in 2023


def test_benchmark_group_explicit_codes() -> None:
    """benchmark_group scores within a peer group given by ISO3 codes."""
    mart = pd.DataFrame(
        {
            "country": ["A", "A", "B", "B", "C", "C"],
            "iso_code": ["AAA", "AAA", "BBB", "BBB", "CCC", "CCC"],
            "year": [2023, 2024, 2023, 2024, 2023, 2024],
            "co2": [10.0, 11.0, 30.0, 45.0, 5.0, 4.0],
            "co2_per_capita": [1.0, 1.1, 4.0, 5.0, 0.5, 0.4],
            "carbon_intensity": [0.1, 0.11, 0.4, 0.5, 0.05, 0.04],
            "fossil_share_energy": [30.0, 32.0, 80.0, 82.0, 20.0, 18.0],
            "renewables_share_elec": [50.0, 52.0, 10.0, 9.0, 80.0, 82.0],
        }
    )
    out = benchmark_group(mart, group={"AAA", "BBB"})
    # Only the two peers are present, and B is higher-risk than A.
    assert set(out["country"]) == {"A", "B"}
    assert out.set_index("country").loc["B", "risk_rank"] == 1

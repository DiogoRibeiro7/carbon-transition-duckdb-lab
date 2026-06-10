# Benchmarking & Configurable Scoring (v0.6)

v0.6 makes the transition-risk score **contextual and configurable**: weights
come from a versioned profile, and countries can be scored and benchmarked
*within a peer group* instead of against the whole world.

## Scoring profiles

A profile is a named, validated set of component weights. Built-ins live in
`carbon_transition_duckdb.risk.profiles`; custom profiles load from YAML or JSON.

```yaml
# profiles/trend_focused.yaml
name: trend_focused
description: Emphasise recent emissions trend and fossil dependence.
weights:
  co2_trend: 0.40
  co2_per_capita: 0.15
  carbon_intensity: 0.15
  fossil_share: 0.20
  renewable_gap: 0.10
```

```python
from carbon_transition_duckdb.risk.profiles import get_profile
weights = get_profile("trend_focused").weights          # built-in name
weights = get_profile("profiles/my_profile.yaml").weights  # or a file path
```

Weights are validated on load: each must be non-negative and the five must sum
to 1. Built-in profiles: `default`, `trend_focused`, `renewables_focused`.

## Peer-group scoring

Passing a `group` scales every score component min-max *within* that group, so
the result is relative to comparable economies rather than the whole world.
Groups are the ISO3-based sets from `quality.country_groups` (`eu`, `oecd`, the
income tiers) or any explicit iterable of ISO3 codes.

```python
from carbon_transition_duckdb.pipeline import compute_transition_scores
scores = compute_transition_scores(db, group="eu", weights=weights)
```

## Benchmark report

`benchmark.benchmark_group` scores a peer group and reports where each country
sits among its peers for a given year:

- `risk_rank` — 1 = highest risk in the group
- `peer_percentile` — share of peers with higher risk (higher = better position)
- `peer_median`, `gap_to_median` — distance from the group median
- `gap_to_leader` — distance from the lowest-risk peer

```python
from carbon_transition_duckdb.benchmark import benchmark_group
benchmark_group(mart, group="oecd", weights=weights)
```

## CLI

```bash
# Score within a peer group using a profile
poetry run carbon-duckdb score --group eu --profile trend_focused

# Benchmark a peer group (rank, percentile, gaps)
poetry run carbon-duckdb benchmark --group oecd --profile profiles/renewables_focused.yaml
```

The synthetic sample countries are fictional, so `--group eu/oecd` only returns
rows on real OWID data. See `notebooks/08_benchmarking.ipynb` for a runnable
tour.

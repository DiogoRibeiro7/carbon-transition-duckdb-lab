# Uncertainty-Aware Scoring (v0.7)

The transition-risk score is a weighted sum of min-max scaled components, so one
set of weights yields one score and one ranking — false precision. The
`carbon_transition_duckdb.uncertainty` subpackage replaces that point estimate
with honest uncertainty about the *weighting choice*.

## Method

The weights are perturbed many times around a chosen profile using **Dirichlet
samples whose mean is the profile** (a `concentration` parameter controls the
spread — higher is tighter). Each sample rescores the mart; the distribution of
each country's score and rank is then summarised.

The procedure is pure-Python and **deterministic given the seed**, so runs are
reproducible — no extra dependencies.

## Output

`uncertainty_summary(mart, weights=..., n_samples=500, concentration=60.0,
seed=42, top_k=3)` returns one row per country:

| Column | Meaning |
| --- | --- |
| `score_mean` | mean score across samples |
| `score_low` / `score_high` | 5th / 95th percentile score band |
| `rank_median` | median rank (1 = highest risk) |
| `rank_low` / `rank_high` | 5th / 95th percentile rank |
| `prob_top_k` | share of samples in the top-`k` highest risk |
| `rank_uncertain` | True when the 90% rank band is wider than the threshold |

```python
from carbon_transition_duckdb.uncertainty import uncertainty_summary
uncertainty_summary(mart, n_samples=500, top_k=3)
```

## CLI

```bash
poetry run carbon-duckdb uncertainty --samples 500 --top-k 3
poetry run carbon-duckdb uncertainty --group oecd --profile trend_focused --samples 800
```

## Interpretation

- A **narrow band** means the score is robust to the weighting; a **wide band**
  means it is weight-sensitive.
- `rank_uncertain` / overlapping `rank_low`-`rank_high` ranges flag countries
  whose position is an artefact of one weighting rather than a robust signal.
- `prob_top_k` is a calibrated way to ask "how reliably is this country in the
  high-risk group?".

The synthetic sample countries are well-separated, so their ranks are stable;
on real OWID data, where peers are closer, the uncertainty flags do more work.
See `notebooks/09_uncertainty.ipynb` for a charted tour.

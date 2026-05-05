# Methodology

## Transition-risk score

The v0.1 score is a transparent screening metric.

```text
transition_risk_score =
    0.30 * recent_co2_trend_score
  + 0.20 * co2_per_capita_score
  + 0.20 * carbon_intensity_score
  + 0.20 * fossil_share_score
  + 0.10 * renewable_gap_score
```

Each component is min-max scaled to 0–100.

## Components

### Recent CO2 trend

Simple difference between the current CO2 value and the value five observations
before within the same country.

### CO2 per capita

Higher values are treated as higher screening risk.

### Carbon intensity

Computed as:

```text
co2 / primary_energy_consumption
```

This is not a perfect engineering measure. It is an exploratory indicator.

### Fossil-fuel share

Higher fossil share indicates stronger transition pressure.

### Renewable electricity gap

Lower renewable electricity share contributes to the score.

## Limitations

The score does not control for:

- income level
- industrial structure
- geography
- historical responsibility
- trade-embedded emissions
- energy security constraints
- data coverage differences

It should be used as a starting point for analysis.

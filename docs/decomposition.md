# Decomposition & Attribution (v0.3)

The `carbon_transition_duckdb.decomposition` subpackage explains *why* emissions
changed, using transparent, exact methods.

## Kaya identity (LMDI)

The Kaya identity writes CO2 as a product of factors. With GDP available (real
OWID data) the four-factor form is used:

```text
CO2 = Population × (GDP/Population) × (Energy/GDP) × (CO2/Energy)
```

Without GDP (synthetic data) a three-factor form is used:

```text
CO2 = Population × (Energy/Population) × (CO2/Energy)
```

The change between two years is split with the **Log Mean Divisia Index
(LMDI)**, an additive decomposition where the per-factor contributions sum
*exactly* to the total change:

```text
ΔCO2 = Σ_i  L(CO2_end, CO2_start) · ln(factor_i_end / factor_i_start)
```

`L(a, b) = (a − b) / (ln a − ln b)` is the logarithmic mean. Because the method
is exact, the reported `residual` is zero up to floating-point error — the
attribution is fully auditable.

```python
from carbon_transition_duckdb.decomposition import kaya_decomposition_frame
kaya_decomposition_frame(mart, start_year=2010, end_year=2024)
```

## Emissions-intensity decomposition

Splits the change in CO2 *per capita* into a demand factor and a supply factor:

```text
CO2/Population = (Energy/Population) × (CO2/Energy)
```

## Transition indicators

`transition_indicators` derives, per country over a window:

- **Electricity mix**: renewable electricity share start/end/change and annual change.
- **Fossil lock-in**: fossil share, its annual decline, and a `fossil_lockin_index`
  (high when the fossil share is large *and* falling slowly).
- **Industrial proxy**: the carbon intensity of energy (`CO2/Energy`) as a
  transparent proxy for the carbon-heaviness of the energy/industrial mix — no
  industrial-output data is assumed.

## CLI

```bash
poetry run carbon-duckdb decompose --method kaya
poetry run carbon-duckdb decompose --method intensity --start-year 2015 --end-year 2024
poetry run carbon-duckdb decompose --method indicators --output reports/sample_run/indicators.csv
```

See `notebooks/06_decomposition_attribution.ipynb` for a runnable, charted tour.

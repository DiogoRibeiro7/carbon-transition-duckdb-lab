---
title: Carbon Transition Dashboard
---

A local Evidence.dev dashboard over the DuckDB transition marts. Build the
lakehouse with `carbon-duckdb build`, then run `npm run sources` and
`npm run dev` from the `dashboard/` directory.

```sql latest
select * from carbon.latest
```

```sql totals
select
    count(distinct country) as countries,
    max(year) as latest_year,
    round(sum(co2), 1) as total_co2
from carbon.latest
```

<BigValue data={totals} value=total_co2 title="Total CO2 (latest year, Mt)" fmt="#,##0.0"/>
<BigValue data={totals} value=countries title="Countries"/>
<BigValue data={totals} value=latest_year title="Latest year"/>

## Emissions by country (latest year)

<BarChart
    data={latest}
    x=country
    y=co2
    title="CO2 emissions by country"
    yAxisTitle="CO2 (Mt)"
    sort=false
/>

## Energy mix: fossil dependence vs. renewable electricity

<ScatterPlot
    data={latest}
    x=fossil_share_energy
    y=renewables_share_elec
    series=country
    title="Fossil share vs. renewable electricity share (latest year)"
    xAxisTitle="Fossil share of energy (%)"
    yAxisTitle="Renewable electricity share (%)"
/>

## Emissions trajectories

```sql trends
select country, year, co2, fossil_share_energy, renewables_share_elec
from carbon.transition
order by country, year
```

<LineChart
    data={trends}
    x=year
    y=co2
    series=country
    title="CO2 over time"
    yAxisTitle="CO2 (Mt)"
/>

## Latest-year detail

<DataTable data={latest} rows=20>
    <Column id=country/>
    <Column id=year/>
    <Column id=co2 fmt="#,##0.0"/>
    <Column id=co2_per_capita fmt="#,##0.00"/>
    <Column id=fossil_share_energy fmt="#,##0.0"/>
    <Column id=renewables_share_elec fmt="#,##0.0"/>
</DataTable>

<Details title="About this dashboard">

The data is synthetic OWID-like sample data. Swap in real Our World in Data
files with <code>carbon-duckdb download-owid</code> and rebuild. The transition
score is an exploratory screening signal, not a moral ranking.

</Details>

"""Command-line interface for Carbon Transition DuckDB Lab."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from carbon_transition_duckdb.benchmark import benchmark_group
from carbon_transition_duckdb.config import ProjectPaths
from carbon_transition_duckdb.database.duckdb_engine import connect
from carbon_transition_duckdb.decomposition import (
    intensity_decomposition_frame,
    kaya_decomposition_frame,
    transition_indicators,
)
from carbon_transition_duckdb.forecasting import (
    ReductionTarget,
    forecast_frame,
    target_gap_frame,
)
from carbon_transition_duckdb.ingestion.download import download_owid_datasets
from carbon_transition_duckdb.packaging import build_snapshot, default_snapshot_path
from carbon_transition_duckdb.pipeline import (
    build_duckdb_lakehouse,
    compute_transition_scores,
    load_transition_mart,
)
from carbon_transition_duckdb.quality.manifest import verify_manifest, write_manifest
from carbon_transition_duckdb.quality.missingness import (
    missingness_by_metric,
    write_missingness_report,
)
from carbon_transition_duckdb.quality.schema import validate_connection_schemas
from carbon_transition_duckdb.reporting.markdown import write_report
from carbon_transition_duckdb.risk.profiles import get_profile
from carbon_transition_duckdb.risk.scoring import filter_entities
from carbon_transition_duckdb.sample_data import generate_synthetic_owid_data
from carbon_transition_duckdb.version import __version__
from carbon_transition_duckdb.visualization.plots import plot_top_scores

app = typer.Typer(help="Local DuckDB lakehouse for carbon-transition analytics.")
console = Console()


@app.command("sample-data")
def sample_data(
    output_dir: Path = typer.Option(
        Path("data/raw"), help="Directory for synthetic raw CSV files."
    ),
    start_year: int = typer.Option(2010, help="First generated year."),
    end_year: int = typer.Option(2024, help="Last generated year."),
    seed: int = typer.Option(42, help="Random seed."),
) -> None:
    """Generate synthetic OWID-like data."""
    co2_path, energy_path = generate_synthetic_owid_data(
        output_dir=output_dir,
        start_year=start_year,
        end_year=end_year,
        seed=seed,
    )
    console.print(f"[green]Generated:[/] {co2_path}")
    console.print(f"[green]Generated:[/] {energy_path}")


@app.command("download-owid")
def download_owid(
    output_dir: Path = typer.Option(Path("data/raw"), help="Directory for downloaded CSV files."),
    overwrite: bool = typer.Option(False, help="Overwrite existing files."),
) -> None:
    """Download OWID CO2 and energy datasets."""
    files = download_owid_datasets(output_dir=output_dir, overwrite=overwrite)
    table = Table(title="Downloaded files")
    table.add_column("Name")
    table.add_column("Size bytes", justify="right")
    table.add_column("Path")
    for item in files:
        table.add_row(item.name, str(item.size_bytes), str(item.path))
    console.print(table)


@app.command("build")
def build(
    raw_dir: Path = typer.Option(Path("data/raw"), help="Directory containing raw OWID CSV files."),
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    export_dir: Path = typer.Option(
        Path("data/processed/marts"),
        help="Directory for exported Parquet marts.",
    ),
) -> None:
    """Build the DuckDB database and export analytical marts."""
    result = build_duckdb_lakehouse(
        ProjectPaths(raw_dir=raw_dir, database=database, export_dir=export_dir)
    )
    console.print(f"[green]Database:[/] {result.database}")
    console.print(f"[green]Export dir:[/] {result.export_dir}")
    console.print(f"[green]Mart table:[/] {result.mart_table}")
    console.print(f"[green]Rows:[/] {result.row_count}")
    console.print(f"[green]Ingested at:[/] {result.ingested_at}")
    console.print(f"[green]Manifest:[/] {result.manifest_path}")


@app.command("score")
def score(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    output: Path = typer.Option(
        Path("reports/sample_run/transition_scores.csv"),
        help="Output CSV with scores.",
    ),
    include_aggregates: bool = typer.Option(
        False,
        help="Include aggregate entities such as World or Europe.",
    ),
    group: str | None = typer.Option(
        None, help="Peer group to score within (e.g. 'eu', 'oecd', an income tier)."
    ),
    profile: str | None = typer.Option(
        None, help="Scoring profile: a built-in name or a YAML/JSON file path."
    ),
) -> None:
    """Compute transition-risk scores from the DuckDB mart."""
    weights = get_profile(profile).weights if profile else None
    scores = compute_transition_scores(
        database=database,
        exclude_aggregates=not include_aggregates,
        weights=weights,
        group=group,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(output, index=False)
    console.print(f"[green]Wrote scores:[/] {output}")


@app.command("report")
def report(
    scores: Path = typer.Option(
        Path("reports/sample_run/transition_scores.csv"),
        help="Scores CSV generated by the score command.",
    ),
    output: Path = typer.Option(
        Path("reports/sample_run/transition_report.md"),
        help="Markdown report output path.",
    ),
    title: str = typer.Option("Carbon Transition Risk Report", help="Report title."),
    top_n: int = typer.Option(15, help="Number of highest-risk rows to show."),
    chart: Path | None = typer.Option(None, help="Optional path for a top-score chart."),
) -> None:
    """Generate a Markdown report from transition scores."""
    frame = pd.read_csv(scores)
    write_report(frame, output_path=output, title=title, top_n=top_n)
    console.print(f"[green]Wrote report:[/] {output}")

    if chart is not None:
        plot_top_scores(frame, output_path=chart, top_n=top_n)
        console.print(f"[green]Wrote chart:[/] {chart}")


@app.command("validate")
def validate(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    report: Path | None = typer.Option(
        None, help="Optional Markdown completeness report output path."
    ),
) -> None:
    """Validate raw schemas and report data completeness."""
    with connect(database) as connection:
        reports = validate_connection_schemas(connection)

    schema_table = Table(title="Schema validation")
    schema_table.add_column("Table")
    schema_table.add_column("Status")
    schema_table.add_column("Missing columns")
    drift = False
    for item in reports:
        status = "[green]OK[/]" if item.is_valid else "[red]DRIFT[/]"
        drift = drift or not item.is_valid
        schema_table.add_row(item.table, status, ", ".join(item.missing) or "-")
    console.print(schema_table)

    mart = load_transition_mart(database)
    by_metric = missingness_by_metric(mart)
    metric_table = Table(title="Missingness by metric")
    metric_table.add_column("Metric")
    metric_table.add_column("% missing", justify="right")
    for _, row in by_metric.iterrows():
        metric_table.add_row(str(row["metric"]), f"{row['pct_missing']:.2f}")
    console.print(metric_table)

    if report is not None:
        write_missingness_report(mart, report)
        console.print(f"[green]Wrote report:[/] {report}")

    if drift:
        raise typer.Exit(code=1)


@app.command("manifest")
def manifest(
    raw_dir: Path = typer.Option(
        Path("data/raw"), help="Directory containing raw OWID CSV files."
    ),
    output: Path = typer.Option(
        Path("data/processed/data_manifest.json"),
        help="Manifest JSON path.",
    ),
    verify: bool = typer.Option(
        False, help="Verify files against an existing manifest instead of writing one."
    ),
) -> None:
    """Build or verify a checksum manifest of the raw data files."""
    if verify:
        results = verify_manifest(output, raw_dir)
        table = Table(title="Manifest verification")
        table.add_column("File")
        table.add_column("Matches")
        ok = True
        for name, matches in results.items():
            ok = ok and matches
            table.add_row(name, "[green]yes[/]" if matches else "[red]NO[/]")
        console.print(table)
        if not ok:
            raise typer.Exit(code=1)
    else:
        co2 = raw_dir / "owid-co2-data.csv"
        energy = raw_dir / "owid-energy-data.csv"
        path = write_manifest([co2, energy], output)
        console.print(f"[green]Wrote manifest:[/] {path}")


def _print_frame(frame: pd.DataFrame, title: str) -> None:
    """Render a DataFrame as a Rich table."""
    table = Table(title=title)
    for column in frame.columns:
        justify: Literal["left", "right"] = "left" if column == "country" else "right"
        table.add_column(str(column), justify=justify)
    for _, row in frame.iterrows():
        table.add_row(*[str(value) for value in row.tolist()])
    console.print(table)


@app.command("decompose")
def decompose(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    method: str = typer.Option(
        "kaya", help="Decomposition: 'kaya', 'intensity', or 'indicators'."
    ),
    start_year: int | None = typer.Option(
        None, help="Start year (defaults to the earliest available)."
    ),
    end_year: int | None = typer.Option(
        None, help="End year (defaults to the latest available)."
    ),
    output: Path | None = typer.Option(None, help="Optional CSV output path."),
    include_aggregates: bool = typer.Option(
        False, help="Include aggregate entities such as World or Europe."
    ),
) -> None:
    """Decompose emissions change (Kaya / intensity) or compute indicators."""
    mart = load_transition_mart(database)
    if not include_aggregates:
        mart = filter_entities(mart)

    builders = {
        "kaya": (kaya_decomposition_frame, "Kaya identity decomposition"),
        "intensity": (intensity_decomposition_frame, "CO2-per-capita decomposition"),
        "indicators": (transition_indicators, "Transition indicators"),
    }
    if method not in builders:
        raise typer.BadParameter("method must be 'kaya', 'intensity', or 'indicators'.")

    builder, title = builders[method]
    frame = builder(mart, start_year, end_year)

    _print_frame(frame, title)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output, index=False)
        console.print(f"[green]Wrote:[/] {output}")


@app.command("forecast")
def forecast(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    metric: str = typer.Option("co2", help="Metric column to forecast."),
    horizon: int = typer.Option(5, help="Years to project past the last observed year."),
    output: Path | None = typer.Option(None, help="Optional CSV output path."),
    include_aggregates: bool = typer.Option(
        False, help="Include aggregate entities such as World or Europe."
    ),
) -> None:
    """Baseline OLS trend forecast with approximate prediction intervals."""
    mart = load_transition_mart(database)
    if not include_aggregates:
        mart = filter_entities(mart)

    frame = forecast_frame(mart, metric, horizon)
    _print_frame(frame, f"{metric} forecast (+{horizon}y, ~95% interval)")

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output, index=False)
        console.print(f"[green]Wrote:[/] {output}")


@app.command("target-gap")
def target_gap_command(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    metric: str = typer.Option("co2", help="Metric the target applies to."),
    base_year: int = typer.Option(2010, help="Baseline year for the reduction."),
    target_year: int = typer.Option(2030, help="Year the target should be met."),
    reduction: float = typer.Option(
        0.55, help="Reduction fraction vs. base year (0.55 = -55%)."
    ),
    output: Path | None = typer.Option(None, help="Optional CSV output path."),
    include_aggregates: bool = typer.Option(
        False, help="Include aggregate entities such as World or Europe."
    ),
) -> None:
    """Gap between a trend projection and a proportional reduction target."""
    mart = load_transition_mart(database)
    if not include_aggregates:
        mart = filter_entities(mart)

    target = ReductionTarget(
        metric=metric,
        base_year=base_year,
        target_year=target_year,
        reduction=reduction,
    )
    frame = target_gap_frame(mart, target)
    pct = int(round(reduction * 100))
    _print_frame(frame, f"{metric} gap to -{pct}% by {target_year} (base {base_year})")

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output, index=False)
        console.print(f"[green]Wrote:[/] {output}")


@app.command("snapshot")
def snapshot(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    marts_dir: Path = typer.Option(
        Path("data/processed/marts"), help="Directory of Parquet marts."
    ),
    manifest: Path = typer.Option(
        Path("data/processed/data_manifest.json"), help="Data manifest JSON."
    ),
    output_dir: Path = typer.Option(Path("dist"), help="Directory for the snapshot."),
    version: str | None = typer.Option(
        None, help="Snapshot version label (defaults to the package version)."
    ),
) -> None:
    """Package the database, marts, and manifest into a versioned snapshot zip."""
    label = version or __version__
    result = build_snapshot(
        output_path=default_snapshot_path(output_dir, label),
        version=label,
        database=database,
        marts_dir=marts_dir,
        manifest=manifest,
    )
    console.print(f"[green]Wrote snapshot:[/] {result.path}")
    console.print(f"[green]Members:[/] {len(result.members)}")
    for member in result.members:
        console.print(f"  - {member}")


@app.command("benchmark")
def benchmark(
    database: Path = typer.Option(
        Path("data/processed/carbon_transition.duckdb"),
        help="Path to DuckDB database.",
    ),
    group: str | None = typer.Option(
        None, help="Peer group to benchmark within (e.g. 'eu', 'oecd')."
    ),
    profile: str | None = typer.Option(
        None, help="Scoring profile: a built-in name or a YAML/JSON file path."
    ),
    year: int | None = typer.Option(
        None, help="Year to benchmark (defaults to the latest available)."
    ),
    output: Path | None = typer.Option(None, help="Optional CSV output path."),
    include_aggregates: bool = typer.Option(
        False, help="Include aggregate entities such as World or Europe."
    ),
) -> None:
    """Benchmark a peer group: rank, percentile, and gaps to median and leader."""
    mart = load_transition_mart(database)
    if not include_aggregates:
        mart = filter_entities(mart)

    weights = get_profile(profile).weights if profile else None
    frame = benchmark_group(mart, group=group, weights=weights, year=year)

    label = group or "all countries"
    _print_frame(frame, f"Benchmark: {label}")

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output, index=False)
        console.print(f"[green]Wrote:[/] {output}")

"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from carbon_transition_duckdb.risk.scoring import latest_year


def generate_markdown_report(
    scores: pd.DataFrame,
    title: str = "Carbon Transition Risk Report",
    top_n: int = 15,
) -> str:
    """Generate a compact Markdown report from scored rows."""
    if scores.empty:
        raise ValueError("Cannot generate a report from an empty scores table.")

    year = latest_year(scores)
    latest = (
        scores.loc[scores["year"] == year]
        .sort_values("transition_risk_score", ascending=False)
        .head(top_n)
        .copy()
    )

    lines = [
        f"# {title}",
        "",
        f"Latest analysed year: **{year}**.",
        "",
        "This report ranks country-year rows by a transparent transition-risk score.",
        "The score is exploratory and should not be interpreted as a causal judgement.",
        "",
        "## Highest-risk rows",
        "",
        "| Rank | Country | Score | Main drivers |",
        "|---:|---|---:|---|",
    ]

    for rank, (_, row) in enumerate(latest.iterrows(), start=1):
        lines.append(
            f"| {rank} | {row['country']} | {row['transition_risk_score']:.2f} | "
            f"{row.get('risk_drivers', '')} |"
        )

    lines.extend(
        [
            "",
            "## Method summary",
            "",
            "The first version combines recent CO2 trend, CO2 per capita, carbon intensity, "
            "fossil-fuel share of energy, and renewable electricity share.",
            "",
            "Higher scores indicate stronger screening signals for transition-risk review, "
            "not proof of policy failure or future climate outcomes.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    scores: pd.DataFrame,
    output_path: Path,
    title: str = "Carbon Transition Risk Report",
    top_n: int = 15,
) -> Path:
    """Write a Markdown report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        generate_markdown_report(scores=scores, title=title, top_n=top_n),
        encoding="utf-8",
    )
    return output_path

"""Simple Matplotlib visualizations for reports and notebooks."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_top_scores(scores: pd.DataFrame, output_path: Path, top_n: int = 15) -> Path:
    """Create a horizontal bar chart of the highest transition-risk scores."""
    required = {"country", "year", "transition_risk_score"}
    missing = required.difference(scores.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    latest_year = int(pd.to_numeric(scores["year"], errors="coerce").max())
    latest = (
        scores.loc[scores["year"] == latest_year]
        .sort_values("transition_risk_score", ascending=True)
        .tail(top_n)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(latest["country"], latest["transition_risk_score"])
    ax.set_title(f"Top transition-risk scores, {latest_year}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Country")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path

"""Tests for Markdown report generation."""

import pandas as pd

from carbon_transition_duckdb.reporting.markdown import generate_markdown_report


def test_generate_markdown_report_contains_latest_year() -> None:
    """Report should include the latest analysed year."""
    frame = pd.DataFrame(
        {
            "country": ["A", "B"],
            "year": [2024, 2024],
            "transition_risk_score": [20.0, 70.0],
            "risk_drivers": ["low renewable share", "high fossil share"],
        }
    )

    report = generate_markdown_report(frame, title="Test Report")

    assert "# Test Report" in report
    assert "2024" in report
    assert "B" in report

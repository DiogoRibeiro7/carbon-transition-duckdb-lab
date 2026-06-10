"""Tests for snapshot packaging."""

import zipfile
from pathlib import Path

import pytest

from carbon_transition_duckdb.packaging.snapshot import (
    build_snapshot,
    default_snapshot_path,
)


def _lakehouse(tmp_path: Path) -> tuple[Path, Path, Path]:
    database = tmp_path / "carbon.duckdb"
    database.write_bytes(b"duckdb-bytes")
    marts = tmp_path / "marts"
    marts.mkdir()
    (marts / "mart_country_year_transition.parquet").write_bytes(b"parquet-a")
    (marts / "mart_latest_country_transition.parquet").write_bytes(b"parquet-b")
    manifest = tmp_path / "data_manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    return database, marts, manifest


def test_default_snapshot_path() -> None:
    """The snapshot filename embeds the version."""
    path = default_snapshot_path(Path("dist"), "0.5.0")
    assert path.name == "carbon_transition_snapshot_v0.5.0.zip"


def test_build_snapshot_contains_all_members(tmp_path: Path) -> None:
    """A snapshot bundles the database, marts, manifest and a version marker."""
    database, marts, manifest = _lakehouse(tmp_path)
    out = tmp_path / "snap.zip"

    result = build_snapshot(
        out, "0.5.0", database=database, marts_dir=marts, manifest=manifest
    )

    assert result.path == out
    assert out.exists()
    with zipfile.ZipFile(out) as archive:
        names = set(archive.namelist())
        assert archive.read("SNAPSHOT_VERSION").decode().strip() == "0.5.0"
    assert "database/carbon.duckdb" in names
    assert "marts/mart_country_year_transition.parquet" in names
    assert "marts/mart_latest_country_transition.parquet" in names
    assert "data_manifest.json" in names


def test_build_snapshot_skips_missing_inputs(tmp_path: Path) -> None:
    """Inputs that do not exist are silently skipped."""
    database, marts, _ = _lakehouse(tmp_path)
    out = tmp_path / "snap.zip"

    result = build_snapshot(
        out,
        "0.5.0",
        database=database,
        marts_dir=marts,
        manifest=tmp_path / "absent.json",
    )
    assert not any(member == "absent.json" for member in result.members)


def test_build_snapshot_requires_inputs(tmp_path: Path) -> None:
    """Packaging with no existing inputs raises."""
    with pytest.raises(FileNotFoundError):
        build_snapshot(tmp_path / "snap.zip", "0.5.0", database=tmp_path / "nope.duckdb")

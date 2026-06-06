"""Tests for reproducible data manifests."""

from pathlib import Path

from carbon_transition_duckdb.quality.manifest import (
    build_manifest,
    verify_manifest,
    write_manifest,
)


def _write_csv(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_build_manifest_counts_rows(tmp_path: Path) -> None:
    """A CSV manifest entry should record size, row count and checksum."""
    csv = _write_csv(tmp_path / "a.csv", "country,year\nX,2020\nY,2021\n")
    manifest = build_manifest([csv])

    entry = manifest["a.csv"]
    assert entry.n_rows == 2
    assert entry.size_bytes > 0
    assert len(entry.sha256) == 64


def test_manifest_round_trip_and_verify(tmp_path: Path) -> None:
    """Writing then verifying an unchanged file should match."""
    csv = _write_csv(tmp_path / "a.csv", "country,year\nX,2020\n")
    manifest_path = write_manifest([csv], tmp_path / "manifest.json")

    results = verify_manifest(manifest_path, tmp_path)
    assert results == {"a.csv": True}


def test_verify_detects_change(tmp_path: Path) -> None:
    """Editing a file after writing the manifest should fail verification."""
    csv = _write_csv(tmp_path / "a.csv", "country,year\nX,2020\n")
    manifest_path = write_manifest([csv], tmp_path / "manifest.json")

    _write_csv(csv, "country,year\nX,2020\nZ,2099\n")
    results = verify_manifest(manifest_path, tmp_path)
    assert results == {"a.csv": False}


def test_verify_detects_missing_file(tmp_path: Path) -> None:
    """A file referenced by the manifest but absent should fail verification."""
    csv = _write_csv(tmp_path / "a.csv", "country,year\nX,2020\n")
    manifest_path = write_manifest([csv], tmp_path / "manifest.json")

    csv.unlink()
    results = verify_manifest(manifest_path, tmp_path)
    assert results == {"a.csv": False}

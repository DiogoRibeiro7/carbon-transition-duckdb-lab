"""Reproducible data manifests with checksums.

A manifest records the exact raw inputs behind a build: file name, byte size,
row count, and SHA-256 checksum. Committing or archiving the manifest makes a
run reproducible and lets a later run detect whether the inputs changed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB


@dataclass(frozen=True)
class FileChecksum:
    """Checksum and shape metadata for a single raw file."""

    name: str
    size_bytes: int
    n_rows: int
    sha256: str


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_csv_rows(path: Path) -> int:
    """Count data rows in a CSV file (excluding the header)."""
    with path.open("rb") as handle:
        total = sum(1 for _ in handle)
    return max(total - 1, 0)


def checksum_file(path: Path) -> FileChecksum:
    """Build a :class:`FileChecksum` for one file."""
    if not path.exists():
        raise FileNotFoundError(f"Cannot checksum missing file: {path}")
    n_rows = _count_csv_rows(path) if path.suffix.lower() == ".csv" else 0
    return FileChecksum(
        name=path.name,
        size_bytes=path.stat().st_size,
        n_rows=n_rows,
        sha256=sha256_file(path),
    )


def build_manifest(paths: Iterable[Path]) -> dict[str, FileChecksum]:
    """Build a name-keyed manifest for a collection of files."""
    manifest: dict[str, FileChecksum] = {}
    for path in paths:
        checksum = checksum_file(path)
        manifest[checksum.name] = checksum
    return manifest


def write_manifest(paths: Iterable[Path], output_path: Path) -> Path:
    """Write a JSON manifest for ``paths`` to ``output_path``."""
    manifest = build_manifest(paths)
    payload = {name: asdict(checksum) for name, checksum in sorted(manifest.items())}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def verify_manifest(manifest_path: Path, data_dir: Path) -> dict[str, bool]:
    """Re-checksum the files referenced by a manifest.

    Returns a name -> matches mapping. A file that is missing or whose checksum
    differs from the recorded value maps to ``False``.
    """
    recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
    results: dict[str, bool] = {}
    for name, entry in recorded.items():
        candidate = data_dir / name
        results[name] = candidate.exists() and sha256_file(candidate) == entry["sha256"]
    return results

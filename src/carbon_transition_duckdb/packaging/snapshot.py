"""Package a built lakehouse into a versioned snapshot archive."""

from __future__ import annotations

import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SnapshotResult:
    """Metadata about a written snapshot archive."""

    path: Path
    members: tuple[str, ...]
    version: str


def default_snapshot_path(output_dir: Path, version: str) -> Path:
    """Return the conventional snapshot filename for a version."""
    return output_dir / f"carbon_transition_snapshot_v{version}.zip"


def build_snapshot(
    output_path: Path,
    version: str,
    database: Path | None = None,
    marts_dir: Path | None = None,
    manifest: Path | None = None,
    extra_files: Sequence[Path] = (),
) -> SnapshotResult:
    """Bundle the lakehouse artifacts into a single zip archive.

    The archive contains a ``SNAPSHOT_VERSION`` marker plus whichever inputs
    exist: the DuckDB database under ``database/``, the Parquet marts under
    ``marts/``, the data manifest, and any extra files.

    Raises
    ------
    FileNotFoundError
        If none of the requested inputs exist.
    """
    members: list[tuple[Path, str]] = []

    if database is not None and database.exists():
        members.append((database, f"database/{database.name}"))
    if marts_dir is not None and marts_dir.exists():
        for parquet in sorted(marts_dir.glob("*.parquet")):
            members.append((parquet, f"marts/{parquet.name}"))
    if manifest is not None and manifest.exists():
        members.append((manifest, manifest.name))
    for extra in extra_files:
        if extra.exists():
            members.append((extra, extra.name))

    if not members:
        raise FileNotFoundError("No snapshot inputs found to package.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SNAPSHOT_VERSION", f"{version}\n")
        for source, arcname in members:
            archive.write(source, arcname)

    return SnapshotResult(
        path=output_path,
        members=tuple(arcname for _, arcname in members),
        version=version,
    )

"""Download utilities for public OWID datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve

from carbon_transition_duckdb.config import OWID_CO2_URL, OWID_ENERGY_URL


@dataclass(frozen=True)
class DownloadedFile:
    """Metadata for a downloaded file."""

    name: str
    url: str
    path: Path
    size_bytes: int


def download_file(url: str, output_path: Path, overwrite: bool = False) -> DownloadedFile:
    """Download a URL to a local path.

    Parameters
    ----------
    url:
        Remote URL to download.
    output_path:
        Local file destination.
    overwrite:
        Whether to overwrite an existing file.

    Returns
    -------
    DownloadedFile
        Local metadata for the downloaded or reused file.

    Raises
    ------
    RuntimeError
        If the download fails.
    """
    if output_path.exists() and not overwrite:
        return DownloadedFile(
            name=output_path.name,
            url=url,
            path=output_path,
            size_bytes=output_path.stat().st_size,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        urlretrieve(url, output_path)
    except (HTTPError, URLError, OSError) as exc:
        raise RuntimeError(f"Failed to download {url!r} to {output_path!s}: {exc}") from exc

    return DownloadedFile(
        name=output_path.name,
        url=url,
        path=output_path,
        size_bytes=output_path.stat().st_size,
    )


def download_owid_datasets(output_dir: Path, overwrite: bool = False) -> list[DownloadedFile]:
    """Download OWID CO2 and energy datasets.

    Parameters
    ----------
    output_dir:
        Directory where the raw CSV files should be stored.
    overwrite:
        Whether to overwrite existing files.

    Returns
    -------
    list[DownloadedFile]
        Metadata for downloaded files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        download_file(OWID_CO2_URL, output_dir / "owid-co2-data.csv", overwrite=overwrite),
        download_file(OWID_ENERGY_URL, output_dir / "owid-energy-data.csv", overwrite=overwrite),
    ]

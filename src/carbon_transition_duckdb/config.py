"""Configuration objects for local paths and public data URLs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


OWID_CO2_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
OWID_ENERGY_URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"


@dataclass(frozen=True)
class ProjectPaths:
    """Filesystem paths used by the pipeline.

    Parameters
    ----------
    raw_dir:
        Directory where raw CSV files are stored.
    database:
        Path to the local DuckDB database file.
    export_dir:
        Directory where Parquet analytical marts are exported.
    """

    raw_dir: Path
    database: Path
    export_dir: Path

    def ensure(self) -> None:
        """Create all required parent directories."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    @property
    def co2_csv(self) -> Path:
        """Expected path for the CO2 dataset CSV file."""
        return self.raw_dir / "owid-co2-data.csv"

    @property
    def energy_csv(self) -> Path:
        """Expected path for the energy dataset CSV file."""
        return self.raw_dir / "owid-energy-data.csv"

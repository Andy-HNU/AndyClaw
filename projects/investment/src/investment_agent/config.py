from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    data_dir: Path
    db_path: Path
    schema_path: Path
    portfolio_state_path: Path
    target_allocation_path: Path


def discover_paths() -> ProjectPaths:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    return ProjectPaths(
        project_root=project_root,
        data_dir=data_dir,
        db_path=data_dir / "investment.db",
        schema_path=project_root / "src" / "investment_agent" / "db" / "schema.sql",
        portfolio_state_path=project_root / "system" / "portfolio_state.json",
        target_allocation_path=project_root / "system" / "target_allocation.json",
    )

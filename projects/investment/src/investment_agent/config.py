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
    previous_portfolio_state_path: Path
    target_allocation_path: Path
    market_data_primary_path: Path
    market_data_backup_path: Path
    news_data_primary_path: Path
    news_data_backup_path: Path
    asset_research_path: Path


def discover_paths() -> ProjectPaths:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    return ProjectPaths(
        project_root=project_root,
        data_dir=data_dir,
        db_path=data_dir / "investment.db",
        schema_path=project_root / "src" / "investment_agent" / "db" / "schema.sql",
        portfolio_state_path=project_root / "system" / "portfolio_state.json",
        previous_portfolio_state_path=project_root / "system" / "portfolio_state_previous.json",
        target_allocation_path=project_root / "system" / "target_allocation.json",
        market_data_primary_path=project_root / "system" / "market_data_primary.json",
        market_data_backup_path=project_root / "system" / "market_data_backup.json",
        news_data_primary_path=project_root / "system" / "news_primary.json",
        news_data_backup_path=project_root / "system" / "news_backup.json",
        asset_research_path=project_root / "system" / "asset_research.json",
    )

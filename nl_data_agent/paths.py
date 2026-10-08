from __future__ import annotations

from pathlib import Path

from nl_data_agent.config import get_setting


def project_root() -> Path:
    """Return the repository root (parent of the nl_data_agent package)."""
    return Path(__file__).resolve().parent.parent


def resolve_under_root(*parts: str) -> Path:
    """Join path parts under the project root."""
    return project_root().joinpath(*parts)


def default_db_path() -> Path:
    env_path = get_setting("SQLITE_DB_PATH", "data/nl_data_agent.db") or "data/nl_data_agent.db"
    path = Path(env_path)
    if not path.is_absolute():
        path = project_root() / path
    return path

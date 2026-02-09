"""Data retention utilities for collected datasets."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.logging import get_logger

logger = get_logger(__name__)


def prune_old_files(glob_pattern: str, max_age_days: int) -> int:
    """Delete files matching glob_pattern older than max_age_days."""
    if max_age_days <= 0:
        return 0
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)
    removed = 0
    for path in Path(".").glob(glob_pattern):
        if not path.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                path.unlink(missing_ok=True)
                removed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("retention_prune_failed", path=str(path), error=str(exc))
    return removed

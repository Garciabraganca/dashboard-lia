"""Informações de build/deploy para diagnóstico visível no dashboard."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from functools import lru_cache

APP_START_UTC = datetime.now(timezone.utc)


def _run_git_command(args: list[str]) -> str | None:
    try:
        out = subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()
        return out or None
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_build_stamp() -> str:
    """Retorna stamp de build com commit/hash/data para troubleshooting de deploy."""
    explicit_stamp = os.getenv("LIA_BUILD_STAMP")
    if explicit_stamp:
        return explicit_stamp

    commit = _run_git_command(["rev-parse", "--short", "HEAD"]) or "unknown"
    commit_date = _run_git_command(["log", "-1", "--format=%cd", "--date=iso-strict"]) or "unknown-date"
    branch = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown-branch"

    started_at = APP_START_UTC.isoformat(timespec="seconds")
    return (
        f"build commit={commit} branch={branch} commit_date={commit_date} "
        f"app_started_utc={started_at}"
    )

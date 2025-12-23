import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

STATUS_FILE = Path(__file__).resolve().parent.parent / "output" / "status.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def write_status(
    *,
    state: str,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None,
    result_path: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """
    Canonical status writer for Alfred Data Hub.
    This file is the single source of truth for Home Assistant.
    """

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "state": state,
        "started_at": started_at,
        "finished_at": finished_at,
        "stats": stats or {},
        "result_path": result_path,
        "error": error,
    }

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def init_idle_status(result_path: Optional[str] = None) -> None:
    write_status(
        state="idle",
        started_at=None,
        finished_at=None,
        stats={},
        result_path=result_path,
        error=None,
    )


def mark_running(result_path: Optional[str] = None) -> str:
    started_at = _now_iso()
    write_status(
        state="running",
        started_at=started_at,
        finished_at=None,
        stats={},
        result_path=result_path,
        error=None,
    )
    return started_at


def mark_done(
    *,
    started_at: str,
    stats: Dict[str, Any],
    result_path: Optional[str] = None,
) -> None:
    write_status(
        state="done",
        started_at=started_at,
        finished_at=_now_iso(),
        stats=stats,
        result_path=result_path,
        error=None,
    )


def mark_error(
    *,
    started_at: Optional[str],
    stats: Dict[str, Any],
    error: str,
    result_path: Optional[str] = None,
) -> None:
    write_status(
        state="error",
        started_at=started_at,
        finished_at=_now_iso(),
        stats=stats,
        result_path=result_path,
        error=error,
    )

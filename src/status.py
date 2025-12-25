import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

STATUS_FILE = Path(__file__).resolve().parent.parent / "output" / "status.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _json_safe(value):
    """
    Recursively convert values to JSON-serializable types.
    This protects status.json from datetime and other non-JSON objects.
    """
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat() + "Z"
    return value


def write_status(
    *,
    state: str,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None,
    result_path: Optional[str] = None,
    error: Optional[Any] = None,
) -> None:
    """
    Canonical status writer for Alfred Data Hub.
    This file is the single source of truth for Home Assistant.
    Preserves existing 'task' snapshot if present.
    """

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # --- load existing status (to preserve task snapshot) ---
    existing: Dict[str, Any] = {}
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, dict):
                existing = {}
        except Exception:
            existing = {}

    payload = {
        "state": state,
        "started_at": started_at,
        "finished_at": finished_at,
        "stats": stats or {},
        "result_path": result_path,
        "error": error,
    }

    # 🔑 preserve task snapshot across status updates
    if "task" in existing:
        payload["task"] = existing["task"]

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(_json_safe(payload), f, ensure_ascii=False, indent=2)


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


def write_task_snapshot(task: Dict[str, Any]) -> None:
    """
    Write/replace 'task' snapshot inside status.json.
    This is a compact, machine-oriented snapshot of the active task parameters.
    """

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    data: Dict[str, Any] = {}
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

    data["task"] = _json_safe(task)

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

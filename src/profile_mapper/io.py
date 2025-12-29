import json
from pathlib import Path
from typing import Any, Dict

import yaml


class IOErrorMapper(Exception):
    pass


def read_input(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise IOErrorMapper(f"input.json not found: {path}")

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise IOErrorMapper(f"Failed to read input.json: {exc}") from exc

    if not isinstance(data, dict):
        raise IOErrorMapper("input.json root must be an object")

    return data


def write_task_yaml(out_dir: Path, task: Dict[str, Any]) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "task.yaml"

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(task, f, sort_keys=False)

    return str(path)


def write_report(out_dir: Path, report: Dict[str, Any]) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "mapper_report.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return str(path)

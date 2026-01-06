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
    """
    Writes mapper_report.json always.
    Additionally writes output/summary.md if 'summary_md' is present in report.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. mapper_report.json (always)
    report_path = out_dir / "mapper_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 2. summary.md (stream path only)
    summary_md = report.get("summary_md")
    if isinstance(summary_md, str):
        output_dir = out_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        summary_path = output_dir / "summary.md"
        summary_path.write_text(summary_md, encoding="utf-8")

    return str(report_path)

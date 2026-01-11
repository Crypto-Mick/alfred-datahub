import json
import subprocess
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_input_json(data: dict) -> Path:
    root = _repo_root()
    input_path = root / "runtime" / "input" / "input.json"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return input_path


def run_parser() -> None:
    root = _repo_root()
    script_path = root / "smart-parser-ui" / "scripts" / "run_parser.sh"
    subprocess.run([str(script_path)], check=True)


def open_summary() -> str | None:
    root = _repo_root()
    summary_path = root / "runtime" / "output" / "summary.md"
    if not summary_path.exists():
        return None
    return summary_path.read_text(encoding="utf-8")


def show_status() -> dict | None:
    root = _repo_root()
    report_path = root / "runtime" / "output" / "mapper_report.json"
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))

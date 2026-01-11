import json
import subprocess
from pathlib import Path
from typing import Optional


def _smart_parser_root() -> Path:
    """
    Resolve path to smart-parser directory.

    Expected layout:
    /home/micklib/
    ├── smart-parser/
    └── smart-parser-ui/
        └── ui/
            └── actions.py
    """
    return Path(__file__).resolve().parents[2] / "smart-parser"


def write_input_json(data: dict) -> Path:
    """
    Write runtime/input/input.json for smart-parser.
    """
    sp_root = _smart_parser_root()
    input_path = sp_root / "runtime" / "input" / "input.json"
    input_path.parent.mkdir(parents=True, exist_ok=True)

    input_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return input_path


def run_parser() -> None:
    """
    Run smart-parser via shell script.
    """
    sp_root = _smart_parser_root()
    script_path = sp_root.parent / "smart-parser-ui" / "scripts" / "run_parser.sh"

    subprocess.run(
        [str(script_path)],
        check=True,
    )


def open_summary() -> Optional[str]:
    """
    Read result produced by smart-parser.

    Priority:
    1. output/result.md          (successful run)
    2. output/summary.md         (legacy / future)
    3. runtime/output/summary.md (denied / error)
    """
    sp_root = _smart_parser_root()

    candidates = [
        sp_root / "output" / "result.md",
        sp_root / "output" / "summary.md",
        sp_root / "runtime" / "output" / "summary.md",
    ]

    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")

    return None



def show_status() -> Optional[dict]:
    """
    Read runtime/output/mapper_report.json from smart-parser.
    """
    sp_root = _smart_parser_root()
    report_path = sp_root / "runtime" / "output" / "mapper_report.json"

    if not report_path.exists():
        return None

    return json.loads(report_path.read_text(encoding="utf-8"))

# ui/actions.py
import json
import subprocess
from pathlib import Path
from typing import Optional


def _smart_parser_root() -> Path:
    """
    Resolve path to smart-parser directory.

    Expected layout:
    smart-parser/
    ├── runtime/
    ├── src/
    └── smart-parser-ui/
        └── ui/
            └── actions.py
    """
    # actions.py is at: smart-parser/smart-parser-ui/ui/actions.py
    return Path(__file__).resolve().parents[2]


def write_input_json(data: dict) -> Path:
    """
    Write runtime/input/input.json for smart-parser.

    UI contract:
    - UI writes ONLY runtime/input/input.json (human intent).
    - UI does NOT write mapper artifacts or core output.
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

    UI invariant:
    - UI launches a single command.
    - No core imports.
    """
    sp_root = _smart_parser_root()
    script_path = sp_root / "smart-parser-ui" / "scripts" / "run_parser.sh"

    subprocess.run(
        [str(script_path)],
        check=True,
        cwd=str(sp_root),
    )


def open_summary() -> Optional[str]:
    """
    Read result produced by smart-parser.

    Contract v1:
    - Core writes runtime/output/summary.md ALWAYS (success or error).
    """
    sp_root = _smart_parser_root()
    path = sp_root / "runtime" / "output" / "summary.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def show_status() -> Optional[dict]:
    """
    Read mapper report produced by Profile Mapper v1.

    Contract v1:
    - Mapper writes runtime/mapper/mapper_report.json (always, even denied).
    """
    sp_root = _smart_parser_root()
    report_path = sp_root / "runtime" / "mapper" / "mapper_report.json"
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))

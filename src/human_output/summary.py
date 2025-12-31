from pathlib import Path
import json
from datetime import datetime, timezone


def emit_denied_summary(
    mapper_report_path: str,
    output_dir: str = "runtime/output",
) -> None:
    """
    Writes human-readable summary.md for denied / error runs.
    Pure output. No decisions.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "summary.md"
    report_path = Path(mapper_report_path)

    if not report_path.exists():
        summary_path.write_text(
            "# Alfred run failed\n\n"
            "No mapper_report.json found.\n",
            encoding="utf-8",
        )
        return

    with report_path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    status = report.get("status", "unknown")

    lines = []
    lines.append("# Alfred run result\n")
    lines.append(f"**Status:** {status}\n")
    lines.append(f"**Time:** {datetime.now(timezone.utc).isoformat()}\n")

    # human-facing message
    errors = report.get("errors") or []
    if errors:
        err = errors[0]
        msg = err.get("message") or "Request was denied."
        lines.append("\n## Reason\n")
        lines.append(msg + "\n")

    guardrails = report.get("guardrails")
    if guardrails and guardrails.get("applied"):
        lines.append("\n## Details\n")
        lines.append(f"- Policy: {guardrails.get('policy')}\n")
        lines.append(f"- Reason: {guardrails.get('reason')}\n")

    summary_path.write_text("\n".join(lines), encoding="utf-8")

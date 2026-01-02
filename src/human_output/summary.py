from pathlib import Path
import json
from datetime import datetime, timezone


def emit_denied_summary(
    mapper_report_path: str,
    output_dir: str = "runtime/output",
) -> None:
    """
    Writes human-readable summary.md for denied runs.
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


def emit_success_summary(
    result_md_path: str = "output/result.md",
    mapper_report_path: str = "runtime/mapper/mapper_report.json",
    output_dir: str = "runtime/output",
) -> None:
    """
    Writes human-readable summary.md for ok / trimmed runs.
    Pure output. No decisions.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "summary.md"

    status = "ok"
    note = None

    report_path = Path(mapper_report_path)
    if report_path.exists():
        with report_path.open("r", encoding="utf-8") as f:
            report = json.load(f)
        status = report.get("status", status)
        if status == "trimmed":
            note = "⚠️ Request was trimmed by profile guardrails."

    result_path = Path(result_md_path)
    if not result_path.exists():
        summary_path.write_text(
            "# Alfred run result\n\n"
            "Run completed, but result.md was not found.\n",
            encoding="utf-8",
        )
        return

    result_text = result_path.read_text(encoding="utf-8")

    lines = []
    lines.append("# Alfred run result\n")
    lines.append(f"**Status:** {status}\n")
    lines.append(f"**Time:** {datetime.now(timezone.utc).isoformat()}\n")

    if note:
        lines.append(f"\n{note}\n")

    lines.append("\n---\n\n")
    lines.append(result_text)

    summary_path.write_text("\n".join(lines), encoding="utf-8")


def emit_error_summary(
    error: Exception,
    mapper_report_path: str = "runtime/mapper/mapper_report.json",
    output_dir: str = "runtime/output",
) -> None:
    """
    Writes human-readable summary.md for unexpected error runs.
    Must never raise.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "summary.md"

    lines = []
    lines.append("# Alfred run result\n")
    lines.append("**Status:** error\n")
    lines.append(f"**Time:** {datetime.now(timezone.utc).isoformat()}\n")

    lines.append("\n## Reason\n")
    lines.append(str(error) + "\n")

    # Optional mapper diagnostics (best-effort)
    report_path = Path(mapper_report_path)
    if report_path.exists():
        try:
            with report_path.open("r", encoding="utf-8") as f:
                report = json.load(f)
            status = report.get("status")
            if status:
                lines.append("\n## Mapper status\n")
                lines.append(f"- status: {status}\n")
        except Exception:
            pass

    summary_path.write_text("\n".join(lines), encoding="utf-8")

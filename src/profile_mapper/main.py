from pathlib import Path

from .io import read_input, write_task_yaml, write_report
from .profiles import load_profile
from .catalog import load_catalog
from .normalization import normalize_input
from .guardrails import apply_guardrails
from .report import build_report
from .models import MapperResult


def run(input_path: str, output_dir: str) -> None:
    """
    Profile Mapper v1 entrypoint.

    Rules:
    - mapper_report.json is ALWAYS written
    - task.yaml is written ONLY if status in {"ok", "trimmed"}
    """

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        human_input = read_input(input_path)
        profile = load_profile(human_input)
        catalog = load_catalog(profile)
        normalized = normalize_input(human_input, profile)

        result = apply_guardrails(
            normalized=normalized,
            profile=profile,
            catalog=catalog,
        )

    except Exception as exc:
        # last-resort safety net: mapper itself failed
        result = MapperResult.error(
            input_summary={},
            profile=None,
            report_path="output/mapper_report.json",
            message=str(exc),
        )

    report = build_report(result)
    write_report(out_dir, report)

    if result.status in ("ok", "trimmed") and result.task_yaml:
        write_task_yaml(out_dir, result.task_yaml)

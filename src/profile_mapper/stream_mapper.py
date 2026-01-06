from typing import Dict, Any, List
from datetime import datetime

from .models import (
    MapperResult,
    ProfileInfo,
    OutputsInfo,
)


def run_stream_mapper(human_input: Dict[str, Any]) -> MapperResult:
    texts: List[str] = []

    if "text" in human_input and isinstance(human_input["text"], str):
        texts.append(human_input["text"])

    if "messages" in human_input and isinstance(human_input["messages"], list):
        for msg in human_input["messages"]:
            if isinstance(msg, dict) and isinstance(msg.get("text"), str):
                texts.append(msg["text"])

    if not texts:
        return MapperResult.error(
            input_summary={},
            profile=None,
            report_path="output/mapper_report.json",
            message="No text content found for stream intent",
        )

    combined_text = "\n".join(texts)
    preview = combined_text[:500].strip()

    summary_md = (
        "# Stream analysis result\n\n"
        f"**Time:** {datetime.utcnow().isoformat()} UTC\n\n"
        "---\n\n"
        "## Input preview\n\n"
        f"{preview}\n"
    )

    return MapperResult(
        status="ok",
        input_summary={
            "messages_count": len(texts),
        },
        profile=ProfileInfo(
            name="stream",
            version=1,
            hash="",
        ),
        resolution=None,
        guardrails=None,
        task_yaml=None,
        outputs=OutputsInfo(
            generated_task_path=None,
            report_path="output/mapper_report.json",
        ),
        warnings=[],
        errors=[],
        summary_md=summary_md,
    )

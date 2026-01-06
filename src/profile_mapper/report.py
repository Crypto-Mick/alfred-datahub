from typing import Any, Dict

from .models import MapperResult


def build_report(result: MapperResult) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "version": 1,
        "status": result.status,
        "input_summary": result.input_summary,
        "profile": (
            {
                "name": result.profile.name,
                "version": result.profile.version,
                "hash": result.profile.hash,
            }
            if result.profile is not None
            else None
        ),
        "outputs": {
            "generated_task_path": result.outputs.generated_task_path,
            "report_path": result.outputs.report_path,
        },
        "warnings": result.warnings,
        "errors": result.errors,
    }

    if result.resolution:
        out["resolution"] = {
            "counts": {
                "item_ids": result.resolution.counts.item_ids,
                "locations": result.resolution.counts.locations,
                "qualities": result.resolution.counts.qualities,
                "request_units": result.resolution.counts.request_units,
            },
            "item_ids_preview": result.resolution.item_ids_preview,
            "item_ids_preview_truncated": result.resolution.item_ids_preview_truncated,
        }

    if result.guardrails:
        gr = result.guardrails
        out["guardrails"] = {
            "applied": gr.applied,
            "policy": gr.policy,
            "reason": gr.reason,
            "method": gr.method,
            "before": (
                {
                    "item_ids": gr.before.item_ids,
                    "request_units": gr.before.request_units,
                }
                if gr.before
                else None
            ),
            "after": (
                {
                    "item_ids": gr.after.item_ids,
                    "request_units": gr.after.request_units,
                }
                if gr.after
                else None
            ),
        }

    return out

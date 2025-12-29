from typing import Any, Dict, List, Tuple

from .models import (
    MapperResult,
    ProfileInfo,
    ResolutionCounts,
    ResolutionInfo,
    GuardrailInfo,
    GuardrailBeforeAfter,
)
from .profiles import ProfileLoadError


class GuardrailError(Exception):
    pass


# -----------------------------
# Public entry
# -----------------------------

def apply_guardrails(
    *,
    normalized: Dict[str, Any],
    profile: Dict[str, Any],
    catalog: Dict[str, Any],
) -> MapperResult:
    """
    Responsibilities:
    - compute diagnostic item_ids (strings) from catalog
    - compute scale (request_units)
    - apply deterministic guardrails (ok / trimmed / denied)
    - produce declarative task.yaml v1 (KEEP)

    item_ids are diagnostic only and NEVER written to task.yaml.
    """

    profile_info: ProfileInfo = profile["_meta"]["info"]

    # 1) Build input summary (cheap, human-facing)
    input_summary = _build_input_summary(normalized)

    # 2) Extract API params (human-level)
    api_src = _extract_api_source(normalized)

    # 3) Diagnostic expansion to item_ids (strings)
    item_ids = _expand_item_ids(
        api_src=api_src,
        profile=profile,
        catalog=catalog,
    )

    # 4) Compute scale
    locations = api_src.get("params", {}).get("locations", [])
    qualities = api_src.get("params", {}).get("qualities", [])
    request_units = len(item_ids) * max(1, len(locations)) * max(1, len(qualities))

    counts_before = ResolutionCounts(
        item_ids=len(item_ids),
        locations=len(locations),
        qualities=len(qualities),
        request_units=request_units,
    )

    # 5) Apply guardrails
    guardrails_cfg = profile.get("guardrails", {})
    max_item_ids = guardrails_cfg.get("max_item_ids")
    max_request_units = guardrails_cfg.get("max_request_units")
    on_exceed = guardrails_cfg.get("on_exceed", "deny")

    exceeded, policy = _check_exceeded(
        counts_before=counts_before,
        max_item_ids=max_item_ids,
        max_request_units=max_request_units,
    )

    if exceeded:
        if on_exceed == "deny":
            return MapperResult.denied(
                input_summary=input_summary,
                profile=profile_info,
                guardrails=GuardrailInfo(
                    applied=True,
                    policy=policy,
                    reason=f"Exceeded profile {policy}",
                    before=GuardrailBeforeAfter(
                        item_ids=counts_before.item_ids,
                        request_units=counts_before.request_units,
                    ),
                    after=None,
                ),
                report_path="output/mapper_report.json",
                message="Request is too broad. Narrow categories / tiers / locations.",
            )

        if on_exceed != "trim":
            raise GuardrailError(f"Unsupported on_exceed policy: {on_exceed}")

        # deterministic trim
        item_ids_trimmed, method = _trim_item_ids(
            item_ids=item_ids,
            profile=profile,
        )

        # recompute scale after trim
        request_units_after = (
            len(item_ids_trimmed)
            * max(1, len(locations))
            * max(1, len(qualities))
        )

        counts_after = ResolutionCounts(
            item_ids=len(item_ids_trimmed),
            locations=len(locations),
            qualities=len(qualities),
            request_units=request_units_after,
        )

        resolution = ResolutionInfo(
            counts=counts_after,
            item_ids_preview=item_ids_trimmed[:10],
            item_ids_preview_truncated=len(item_ids_trimmed) > 10,
        )

        task_yaml = _build_task_yaml(normalized, profile)

        return MapperResult.trimmed(
            input_summary=input_summary,
            profile=profile_info,
            resolution=resolution,
            guardrails=GuardrailInfo(
                applied=True,
                policy=policy,
                reason=f"Exceeded profile {policy}",
                method=method,
                before=GuardrailBeforeAfter(
                    item_ids=counts_before.item_ids,
                    request_units=counts_before.request_units,
                ),
                after=GuardrailBeforeAfter(
                    item_ids=counts_after.item_ids,
                    request_units=counts_after.request_units,
                ),
            ),
            task_yaml=task_yaml,
            report_path="output/mapper_report.json",
        )

    # 6) OK (no trimming)
    resolution = ResolutionInfo(
        counts=counts_before,
        item_ids_preview=item_ids[:10],
        item_ids_preview_truncated=len(item_ids) > 10,
    )

    task_yaml = _build_task_yaml(normalized, profile)

    return MapperResult.ok(
        input_summary=input_summary,
        profile=profile_info,
        resolution=resolution,
        guardrails=GuardrailInfo(applied=False),
        task_yaml=task_yaml,
        report_path="output/mapper_report.json",
    )


# -----------------------------
# helpers
# -----------------------------

def _build_input_summary(normalized: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "lookback_hours": normalized.get("lookback_hours"),
        "keywords_count": len(normalized.get("keywords", [])),
        "sources": [s.get("type") for s in normalized.get("sources", []) if isinstance(s, dict)],
    }


def _extract_api_source(normalized: Dict[str, Any]) -> Dict[str, Any]:
    for src in normalized.get("sources", []):
        if isinstance(src, dict) and src.get("type") == "api":
            return src
    raise GuardrailError("No API source found in normalized input")


def _expand_item_ids(
    *,
    api_src: Dict[str, Any],
    profile: Dict[str, Any],
    catalog: Dict[str, Any],
) -> List[str]:
    """
    Diagnostic-only expansion using local catalog.

    Expected catalog format (minimal):
    {
      "items": {
        "<ITEM_ID>": {
            "category": "...",
            "tier": 4,
        },
        ...
      }
    }
    """

    items = catalog.get("items")
    if not isinstance(items, dict):
        raise GuardrailError("Catalog missing 'items' mapping")

    params = api_src.get("params", {})
    categories = set(params.get("categories", []))
    tiers = set(params.get("tiers", []))

    out: List[str] = []
    for item_id, meta in items.items():
        if not isinstance(meta, dict):
            continue

        if categories and meta.get("category") not in categories:
            continue
        if tiers and meta.get("tier") not in tiers:
            continue

        out.append(item_id)

    return sorted(out)


def _check_exceeded(
    *,
    counts_before: ResolutionCounts,
    max_item_ids: Any,
    max_request_units: Any,
) -> Tuple[bool, str]:
    if isinstance(max_item_ids, int) and counts_before.item_ids > max_item_ids:
        return True, "max_item_ids"
    if isinstance(max_request_units, int) and counts_before.request_units > max_request_units:
        return True, "max_request_units"
    return False, ""


def _trim_item_ids(
    *,
    item_ids: List[str],
    profile: Dict[str, Any],
) -> Tuple[List[str], str]:
    """
    Deterministic trim based on profile rules.
    """

    trim_cfg = profile.get("guardrails", {}).get("trim", {})
    method = trim_cfg.get("method")

    if method == "priority_item_ids":
        priority = trim_cfg.get("priority_item_ids", [])
        trimmed = [i for i in priority if i in item_ids]
        return trimmed, "priority_item_ids"

    if method == "priority_groups":
        groups = profile.get("groups", {})
        out: List[str] = []
        for group_name in trim_cfg.get("priority_groups", []):
            group = groups.get(group_name, {})
            cats = set(group.get("categories", []))
            for item_id in item_ids:
                if item_id in out:
                    continue
                # category inference via catalog is already done earlier
                # here we only preserve order deterministically
                out.append(item_id)
        return out, "priority_groups"

    raise GuardrailError("Trim requested but no deterministic trim method configured")


def _build_task_yaml(normalized: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build declarative task.yaml v1 (KEEP).
    """

    task = {
        "version": "v1",
        "lookback_hours": normalized["lookback_hours"],
        "keywords": normalized["keywords"],
        "sources": [],
    }

    for src in normalized.get("sources", []):
        if src.get("type") in ("telegram", "web"):
            task["sources"].append(src)
            continue

        if src.get("type") == "api":
            api_cfg = profile["api"]
            params = src.get("params", {})

            api_block = {
                "type": "api",
                "provider": api_cfg["provider"],
                "dataset": api_cfg["dataset"],
            }

            if "server" in api_cfg:
                api_block["server"] = api_cfg["server"]

            if "locations" in params:
                api_block["locations"] = params["locations"]

            items: Dict[str, Any] = {}
            for key in ("categories", "tiers", "qualities"):
                if key in params:
                    items[key] = params[key]

            if items:
                api_block["items"] = items

            task["sources"].append(api_block)

    if "limits" in normalized:
        task["limits"] = normalized["limits"]

    return task

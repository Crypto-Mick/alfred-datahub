"""Alfred Data Hub: task.yaml v1 validation (STRICT).

Contract summary (task.yaml v1):

  version: "v1"                     (required)
  lookback_hours: int                (required, 1..8760)
  keywords: [str]                    (required, non-empty, unique)
  sources: [source_block]            (required, >=1)
  limits:
    max_items: int                   (optional, 1..10000)

Sources are a list of dicts; each source must include "type".
Supported source types in v1: telegram, web, api.

This validator is a GATE:
- no network calls
- no normalization beyond whitespace trimming for string emptiness checks
- no defaulting (except returning normalized copy with trimmed strings)
- unknown fields are rejected (fail-fast)

Raises TaskYamlError("TASK_YAML_INVALID") with details on any error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class TaskYamlError(Exception):
    def __init__(self, details: dict):
        self.details = details
        super().__init__("TASK_YAML_INVALID")


def _err(path: str, kind: str, expected: Any = None, actual: Any = None) -> None:
    err: Dict[str, Any] = {"path": path, "kind": kind}
    if expected is not None:
        err["expected"] = expected
    if actual is not None:
        err["actual"] = actual
    raise TaskYamlError({"errors": [err]})


def _type_name(x: Any) -> str:
    return type(x).__name__


def _require_dict(path: str, v: Any) -> Dict[str, Any]:
    if not isinstance(v, dict):
        _err(path, "type", "dict", _type_name(v))
    return v


def _require_list(path: str, v: Any) -> List[Any]:
    if not isinstance(v, list):
        _err(path, "type", "list", _type_name(v))
    return v


def _require_nonempty_str(path: str, v: Any) -> str:
    if not isinstance(v, str):
        _err(path, "type", "str", _type_name(v))
    s = v.strip()
    if not s:
        _err(path, "empty")
    return s


def _require_int_range(path: str, v: Any, lo: int, hi: int) -> int:
    if not isinstance(v, int):
        _err(path, "type", "int", _type_name(v))
    if not (lo <= v <= hi):
        _err(path, "range", f"{lo}..{hi}", v)
    return v


def _require_unique_list_of_str(path: str, v: Any, *, min_len: int = 1) -> List[str]:
    arr = _require_list(path, v)
    if len(arr) < min_len:
        _err(path, "empty")

    out: List[str] = []
    for i, item in enumerate(arr):
        s = _require_nonempty_str(f"{path}[{i}]", item)
        out.append(s)

    if len(set(out)) != len(out):
        _err(path, "duplicate")

    return out


def _reject_unknown_fields(obj_path: str, obj: Dict[str, Any], allowed: set[str]) -> None:
    for k in obj.keys():
        if k not in allowed:
            _err(f"{obj_path}.{k}" if obj_path else k, "unknown_field")


# -------------------- source validators --------------------

def _validate_source_telegram(src: Dict[str, Any], idx: int) -> Dict[str, Any]:
    base = f"sources[{idx}]"
    allowed = {"type", "channels", "limit_per_channel"}
    _reject_unknown_fields(base, src, allowed)

    channels = _require_unique_list_of_str(f"{base}.channels", src.get("channels"), min_len=1)

    norm: Dict[str, Any] = {
        "type": "telegram",
        "channels": channels,
    }

    if "limit_per_channel" in src:
        norm["limit_per_channel"] = _require_int_range(
            f"{base}.limit_per_channel",
            src.get("limit_per_channel"),
            10,
            1000,
        )

    return norm


def _validate_source_web(src: Dict[str, Any], idx: int) -> Dict[str, Any]:
    base = f"sources[{idx}]"
    allowed = {"type", "sites"}
    _reject_unknown_fields(base, src, allowed)

    sites = _require_unique_list_of_str(f"{base}.sites", src.get("sites"), min_len=1)

    return {
        "type": "web",
        "sites": sites,
    }


def _validate_api_items(items: Any, base: str) -> Dict[str, Any]:
    items_dict = _require_dict(base, items)
    allowed = {"categories", "tiers", "qualities"}
    _reject_unknown_fields(base, items_dict, allowed)

    out: Dict[str, Any] = {}

    if "categories" in items_dict:
        out["categories"] = _require_unique_list_of_str(f"{base}.categories", items_dict.get("categories"), min_len=1)

    if "tiers" in items_dict:
        tiers = _require_list(f"{base}.tiers", items_dict.get("tiers"))
        if not tiers:
            _err(f"{base}.tiers", "empty")
        norm_tiers: List[int] = []
        for i, t in enumerate(tiers):
            norm_tiers.append(_require_int_range(f"{base}.tiers[{i}]", t, 4, 8))
        if len(set(norm_tiers)) != len(norm_tiers):
            _err(f"{base}.tiers", "duplicate")
        out["tiers"] = norm_tiers

    if "qualities" in items_dict:
        quals = _require_list(f"{base}.qualities", items_dict.get("qualities"))
        if not quals:
            _err(f"{base}.qualities", "empty")
        norm_q: List[int] = []
        for i, q in enumerate(quals):
            norm_q.append(_require_int_range(f"{base}.qualities[{i}]", q, 1, 5))
        if len(set(norm_q)) != len(norm_q):
            _err(f"{base}.qualities", "duplicate")
        out["qualities"] = norm_q

    return out


def _validate_source_api(src: Dict[str, Any], idx: int) -> Dict[str, Any]:
    base = f"sources[{idx}]"
    allowed = {"type", "provider", "dataset", "server", "items", "locations"}
    _reject_unknown_fields(base, src, allowed)

    provider = _require_nonempty_str(f"{base}.provider", src.get("provider"))
    dataset = _require_nonempty_str(f"{base}.dataset", src.get("dataset"))

    out: Dict[str, Any] = {
        "type": "api",
        "provider": provider,
        "dataset": dataset,
    }

    if "server" in src:
        out["server"] = _require_nonempty_str(f"{base}.server", src.get("server"))

    if "locations" in src:
        out["locations"] = _require_unique_list_of_str(f"{base}.locations", src.get("locations"), min_len=1)

    if "items" in src:
        out_items = _validate_api_items(src.get("items"), f"{base}.items")
        out["items"] = out_items

    return out


# -------------------- main validator --------------------

def validate_task_yaml_v1(cfg: Any) -> Dict[str, Any]:
    """Validate task.yaml against v1 contract.

    Returns a normalized copy (trimmed strings, same semantic content).
    Raises TaskYamlError with {"errors": [{path, kind, expected?, actual?}]} on failure.
    """

    # Phase 0: basic
    if not isinstance(cfg, dict):
        _err("$", "type", "dict", _type_name(cfg))

    # Phase 1: root strict fields
    allowed_root = {"version", "lookback_hours", "keywords", "sources", "limits"}
    _reject_unknown_fields("", cfg, allowed_root)

    # required
    for k in ("version", "lookback_hours", "keywords", "sources"):
        if k not in cfg:
            _err(k, "missing_field")

    # version
    version = cfg.get("version")
    if version != "v1":
        _err("version", "version_not_supported", "v1", version)

    # lookback_hours
    lookback_hours = _require_int_range("lookback_hours", cfg.get("lookback_hours"), 1, 8760)

    # keywords
    keywords = _require_unique_list_of_str("keywords", cfg.get("keywords"), min_len=1)

    # sources
    sources_any = cfg.get("sources")
    sources_list = _require_list("sources", sources_any)
    if not sources_list:
        _err("sources", "empty")

    normalized_sources: List[Dict[str, Any]] = []

    for i, src_any in enumerate(sources_list):
        src = _require_dict(f"sources[{i}]", src_any)
        # type required
        if "type" not in src:
            _err(f"sources[{i}].type", "missing_field")
        stype_raw = src.get("type")
        stype = _require_nonempty_str(f"sources[{i}].type", stype_raw)

        if stype == "telegram":
            normalized_sources.append(_validate_source_telegram(src, i))
        elif stype == "web":
            normalized_sources.append(_validate_source_web(src, i))
        elif stype == "api":
            normalized_sources.append(_validate_source_api(src, i))
        else:
            _err(f"sources[{i}].type", "enum", "telegram|web|api", stype_raw)

    # limits (optional)
    normalized_limits: Optional[Dict[str, Any]] = None
    if "limits" in cfg:
        limits_any = cfg.get("limits")
        limits = _require_dict("limits", limits_any)
        allowed_limits = {"max_items"}
        _reject_unknown_fields("limits", limits, allowed_limits)

        if "max_items" not in limits:
            _err("limits.max_items", "missing_field")
        max_items = _require_int_range("limits.max_items", limits.get("max_items"), 1, 10_000)
        normalized_limits = {"max_items": max_items}

    out: Dict[str, Any] = {
        "version": "v1",
        "lookback_hours": lookback_hours,
        "keywords": keywords,
        "sources": normalized_sources,
    }
    if normalized_limits is not None:
        out["limits"] = normalized_limits

    return out

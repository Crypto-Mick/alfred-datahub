from copy import deepcopy
from typing import Any, Dict, List


class NormalizationError(Exception):
    pass


def normalize_input(human_input: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize human input using profile rules.

    Responsibilities:
    - deep-copy input (no mutation)
    - trim all strings
    - normalize locations using profile aliases
    - keep structure intact (no expansion, no reduction)

    Does NOT:
    - validate scale
    - apply guardrails
    - resolve item_ids
    """

    if not isinstance(human_input, dict):
        raise NormalizationError("human_input must be a dict")

    normalized = deepcopy(human_input)

    _trim_strings(normalized)
    _normalize_api_locations(normalized, profile)

    return normalized


# -----------------------------
# helpers
# -----------------------------

def _trim_strings(obj: Any) -> None:
    """
    Recursively trim strings in-place.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                obj[k] = v.strip()
            else:
                _trim_strings(v)

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                obj[i] = v.strip()
            else:
                _trim_strings(v)


def _normalize_api_locations(normalized: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """
    Normalize API source locations using profile normalization rules.
    """

    aliases = (
        profile
        .get("normalization", {})
        .get("location_aliases", {})
    )

    if not aliases:
        return

    sources = normalized.get("sources")
    if not isinstance(sources, list):
        return

    for src in sources:
        if not isinstance(src, dict):
            continue
        if src.get("type") != "api":
            continue

        params = src.get("params")
        if not isinstance(params, dict):
            continue

        locations = params.get("locations")
        if not isinstance(locations, list):
            continue

        normalized_locations: List[str] = []
        for loc in locations:
            if not isinstance(loc, str):
                continue

            key = loc.lower()
            normalized_locations.append(
                aliases.get(key, loc)
            )

        params["locations"] = normalized_locations

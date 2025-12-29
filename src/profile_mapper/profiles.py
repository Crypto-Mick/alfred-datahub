from pathlib import Path
from typing import Any, Dict

import yaml

from .hashing import sha1_of_file
from .models import ProfileInfo


class ProfileLoadError(Exception):
    pass


def load_profile(human_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load API profile specified in human input.
    Responsibilities:
    - find profile name in input.json
    - load profile YAML from profiles/
    - compute profile_hash
    - perform minimal structural validation
    - attach ProfileInfo into profile meta
    """

    profile_name = _extract_profile_name(human_input)
    profile_path = Path("profiles") / f"{profile_name}.yaml"

    if not profile_path.exists():
        raise ProfileLoadError(f"Profile not found: {profile_name}")

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    if not isinstance(profile, dict):
        raise ProfileLoadError("Profile file must contain a YAML mapping")

    _validate_profile_minimal(profile)

    profile_hash = sha1_of_file(profile_path)

    profile_info = ProfileInfo(
        name=profile["name"],
        version=profile["version"],
        hash=profile_hash,
    )

    # Attach meta (internal, not written to task.yaml)
    profile["_meta"] = {
        "info": profile_info,
        "path": str(profile_path),
    }

    return profile


# -----------------------------
# helpers
# -----------------------------

def _extract_profile_name(human_input: Dict[str, Any]) -> str:
    sources = human_input.get("sources")
    if not isinstance(sources, list):
        raise ProfileLoadError("human_input.sources must be a list")

    for src in sources:
        if not isinstance(src, dict):
            continue
        if src.get("type") == "api":
            profile = src.get("profile")
            if not isinstance(profile, str) or not profile.strip():
                raise ProfileLoadError("API source must include non-empty 'profile'")
            return profile.strip()

    raise ProfileLoadError("No API source with 'profile' found in input.json")


def _validate_profile_minimal(profile: Dict[str, Any]) -> None:
    """
    Minimal structural validation.
    We intentionally do NOT validate guardrails logic here.
    """

    required_fields = {
        "name": str,
        "version": int,
        "api": dict,
        "catalog": dict,
    }

    for key, expected_type in required_fields.items():
        if key not in profile:
            raise ProfileLoadError(f"Profile missing required field: {key}")
        if not isinstance(profile[key], expected_type):
            raise ProfileLoadError(
                f"Profile field '{key}' must be {expected_type.__name__}"
            )

    # api block (only presence + basic structure)
    api = profile["api"]
    for k in ("provider", "dataset"):
        if k not in api or not isinstance(api[k], str) or not api[k].strip():
            raise ProfileLoadError(f"profile.api.{k} must be a non-empty string")

    # catalog block (path must exist later; here only structure)
    catalog = profile["catalog"]
    if "path" not in catalog or not isinstance(catalog["path"], str):
        raise ProfileLoadError("profile.catalog.path must be a string")

    # version sanity
    if profile["version"] <= 0:
        raise ProfileLoadError("profile.version must be positive integer")

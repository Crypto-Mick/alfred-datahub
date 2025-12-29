from pathlib import Path
from typing import Any, Dict

import json


class CatalogLoadError(Exception):
    pass


def load_catalog(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load local catalog defined by profile.catalog.path.

    Responsibilities:
    - read catalog file from disk
    - ensure it is a JSON object (dict)
    - return raw catalog data

    No normalization.
    No validation of content semantics.
    No mutation.
    """

    catalog_cfg = profile.get("catalog")
    if not isinstance(catalog_cfg, dict):
        raise CatalogLoadError("profile.catalog must be a mapping")

    path_value = catalog_cfg.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        raise CatalogLoadError("profile.catalog.path must be a non-empty string")

    path = Path(path_value)
    if not path.exists():
        raise CatalogLoadError(f"Catalog file not found: {path}")

    if not path.is_file():
        raise CatalogLoadError(f"Catalog path is not a file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise CatalogLoadError(f"Failed to load catalog JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise CatalogLoadError("Catalog root must be a JSON object")

    return data

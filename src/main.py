from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import yaml

from src.extractor import extract
from src.matcher import match
from src.status import mark_done, mark_error, mark_running, write_task_snapshot
from src.storage import save
from src.tg_reader import read_messages
from src.web_reader import read_site_items
from src.api_reader import read_price_snapshots
from src.validation_v1 import validate_task_yaml_v1, TaskYamlError


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Missing config file: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise RuntimeError("Invalid YAML: root must be a mapping")

    return data


def _collect_items_from_sources(sources: list, since: datetime, lookback_hours: int) -> list:
    """
    v1 contract:
      sources: list of blocks
        - {type: telegram, channels: [...], limit_per_channel?: int}
        - {type: web, sites: [...]}
        - {type: api, provider: str, dataset: str, server?: str, items?: {...}, locations?: [...]}
    """
    items: list = []

    for src in sources:
        stype = src["type"]

        # --- telegram ---
        if stype == "telegram":
            tg_messages = read_messages(
                channels=src["channels"],
                since=since,
                until=None,
                limit_per_channel=src.get("limit_per_channel", 200),
            )
            items.extend(tg_messages)
            continue

        # --- web ---
        if stype == "web":
            # v1: sites are strings (URLs). Reader decides RSS/HTML internally.
            for site in src["sites"]:
                site_items = read_site_items(
                    site=site,
                    lookback_hours=lookback_hours,
                )
                items.extend(site_items)
            continue

        # --- api ---
        if stype == "api":
            provider = src["provider"]
            dataset = src["dataset"]
            server = src.get("server", "west")

            # v1: api is profile-driven. We dispatch by provider+dataset.
            # Albion snapshot v1: provider=albion, dataset=market_snapshot
            if provider == "albion" and dataset == "market_snapshot":
                # NOTE: This assumes api_reader has been updated to accept the v1 shape.
                # If it is still legacy (expects item_ids), it will raise TypeError/KeyError,
                # which is correct until we migrate api_reader.
                api_items = read_price_snapshots(
                    server=server,
                    items=src.get("items", {}),
                    locations=src.get("locations", []),
                )
                items.extend(api_items)
                continue

            raise RuntimeError(f"Unsupported API source: provider={provider}, dataset={dataset}")

        # If validation_v1 is correct, we should never get here.
        raise RuntimeError(f"Unsupported source type: {stype}")

    return items


def main() -> None:
    started_at = None
    result_path = "output/result.md"

    try:
        # --- load + validate config (gate) ---
        task_file = os.getenv("TASK_FILE", "config/task.yaml")
        config_path = Path(task_file).resolve()

        raw_cfg = _load_yaml(config_path)
        cfg = validate_task_yaml_v1(raw_cfg)

        # --- unpack common config (v1) ---
        keywords = cfg["keywords"]
        lookback_hours = cfg["lookback_hours"]

        limits = cfg.get("limits", {})
        max_items = limits.get("max_items")

        sources = cfg["sources"]  # v1: list[dict]

        # --- mark running ---
        started_at = mark_running(result_path=result_path)

        # --- snapshot (observability only; NOT part of task.yaml contract) ---
        write_task_snapshot(
            {
                "name": "manual-task",
                "version": cfg["version"],
                "sources": [s["type"] for s in sources],
                "lookback_hours": lookback_hours,
                "keywords_count": len(keywords),
                "max_items": max_items,
            }
        )

        # --- collect items ---
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=lookback_hours)

        items = _collect_items_from_sources(
            sources=sources,
            since=since,
            lookback_hours=lookback_hours,
        )

        # --- pipeline ---
        matched = match(items, keywords)
        extracted = extract(matched, keywords)

        save(
            extracted,
            output_dir="output",
            lookback_hours=lookback_hours,
            max_items=max_items,
        )

        mark_done(
            started_at=started_at,
            stats={
                "items_read": len(items),
                "matched": len(matched),
                "snippets": len(extracted),
            },
            result_path=result_path,
        )

    except TaskYamlError as e:
        mark_error(
            started_at=started_at,
            stats={},
            error={
                "code": "TASK_YAML_INVALID",
                "message": "task.yaml validation failed",
                "details": e.details,
            },
            result_path=result_path,
        )

    except Exception as e:
        mark_error(
            started_at=started_at,
            stats={},
            error=str(e),
            result_path=result_path,
        )


if __name__ == "__main__":
    main()

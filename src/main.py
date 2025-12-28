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


def main() -> None:
    started_at = None
    result_path = "output/result.md"

    try:
        # --- load + validate config (gate) ---
        task_file = os.getenv("TASK_FILE", "config/task.yaml")
        config_path = Path(task_file).resolve()

        raw_cfg = _load_yaml(config_path)
        cfg = validate_task_yaml_v1(raw_cfg)

        # --- unpack common config ---
        keywords = cfg["filters"]["include_keywords"]
        lookback_hours = cfg["time"]["lookback_hours"]
        max_items = cfg["output"]["max_items"]

        sources = cfg["sources"]

        # --- mark running ---
        started_at = mark_running(result_path=result_path)

        # --- snapshot ---
        write_task_snapshot({
            "name": cfg["task"]["name"],
            "version": cfg["version"],
            "sources": list(sources.keys()),
            "lookback_hours": lookback_hours,
            "keywords_count": len(keywords),
            "max_items": max_items,
        })

        # --- collect items ---
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=lookback_hours)

        items = []

        # --- telegram ---
        if "telegram" in sources:
            tg_cfg = sources["telegram"]
            tg_messages = read_messages(
                channels=tg_cfg["channels"],
                since=since,
                until=None,
                limit_per_channel=tg_cfg["limit_per_channel"],
            )
            items.extend(tg_messages)

        # --- web ---
        if "web" in sources:
            for site in sources["web"]["sites"]:
                site_items = read_site_items(
                    site=site["site"],
                    feed_url=site["feed_url"],
                    lookback_hours=lookback_hours,
                )
                items.extend(site_items)

        # --- api ---
        if "api" in sources:
            api_cfg = sources["api"]

            api_items = read_price_snapshots(
                server=api_cfg.get("server", "west"),
                item_ids=api_cfg["item_ids"],
                locations=api_cfg["locations"],
                qualities=api_cfg["qualities"],
            )
            items.extend(api_items)

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

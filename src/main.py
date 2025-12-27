from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from src.extractor import extract
from src.matcher import match
from src.status import mark_done, mark_error, mark_running, write_task_snapshot
from src.storage import save
from src.tg_reader import read_messages
from src.web_reader import read_site_items
from src.validation import validate_task_yaml_v1, TaskYamlError


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
        config_path = Path(__file__).resolve().parents[1] / "config" / "task.yaml"
        raw_cfg = _load_yaml(config_path)

        cfg = validate_task_yaml_v1(raw_cfg)

        # --- unpack validated config ---
        channels = cfg["sources"]["telegram"]["channels"]
        keywords = cfg["filters"]["include_keywords"]
        lookback_hours = cfg["time"]["lookback_hours"]
        limit_per_channel = cfg["sources"]["telegram"]["limit_per_channel"]
        max_items = cfg["output"]["max_items"]

        # --- mark running ---
        started_at = mark_running(result_path=result_path)

        # --- snapshot active task (status.json) ---
        write_task_snapshot({
            "name": cfg["task"]["name"],
            "version": cfg["version"],
            "source": "telegram",
            "channels_count": len(channels),
            "lookback_hours": lookback_hours,
            "keywords_count": len(keywords),
            "limit_per_channel": limit_per_channel,
            "max_items": max_items,
        })

        # --- run pipeline ---
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=lookback_hours)

        messages = read_messages(
            channels=channels,
            since=since,
            until=None,  # until intentionally not part of v1
            limit_per_channel=limit_per_channel,
        )

        matched = match(messages, keywords)
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
                "messages_read": len(messages),
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

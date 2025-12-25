from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from src.extractor import extract
from src.matcher import match
from src.status import mark_done, mark_error, mark_running
from src.storage import save
from src.tg_reader import read_messages


def _load_config(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Missing config file: {path}")

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise RuntimeError("Invalid config: root must be a mapping")

    try:
        _ = config["version"]
        _ = config["task"]["name"]
        _ = config["time"]["lookback_hours"]
        _ = config["sources"]["telegram"]["channels"]
        _ = config["filters"]["include_keywords"]
        _ = config["output"]["max_items"]
    except KeyError as e:
        raise RuntimeError(f"Missing required config field: {e}")

    return config


def main() -> None:
    started_at = None
    result_path = "output/result.md"

    try:
        config_path = Path(__file__).resolve().parents[1] / "config" / "task.yaml"
        config = _load_config(config_path)

        channels = config["sources"]["telegram"]["channels"]
        keywords = config["filters"]["include_keywords"]
        lookback_hours = config["time"]["lookback_hours"]
        limit_per_channel = config["sources"]["telegram"].get("limit_per_channel", 200)
        max_items = config["output"]["max_items"]

        started_at = mark_running(result_path=result_path)

        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=lookback_hours)

        messages = read_messages(
            channels=channels,
            since=since,
            until=None,
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

    except Exception as e:
        mark_error(
            started_at=started_at,
            stats={},
            error=str(e),
            result_path=result_path,
        )


if __name__ == "__main__":
    main()

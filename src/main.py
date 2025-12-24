import os
from datetime import datetime, timedelta, timezone

from src.tg_reader import read_messages
from src.matcher import match
from src.extractor import extract
from src.storage import save
from src.status import mark_running, mark_done, mark_error


def _get_channels_from_env() -> list[str]:
    raw = os.environ.get("TG_CHANNELS", "")
    return [c.strip() for c in raw.split(",") if c.strip()]


def _get_keywords_from_env() -> list[str]:
    raw = os.environ.get("KEYWORDS", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def main():
    started_at = None
    result_path = "output/result.md"

    try:
        channels = _get_channels_from_env()
        if not channels:
            raise RuntimeError("TG_CHANNELS is empty or not set")

        keywords = _get_keywords_from_env()

        started_at = mark_running(result_path=result_path)

        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=24)

        messages = read_messages(
            channels=channels,
            since=since,
            until=None,
            limit_per_channel=100,
        )

        matched = match(messages, keywords)
        extracted = extract(matched, keywords)

        save(extracted, output_dir="output")

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
        raise


if __name__ == "__main__":
    main()

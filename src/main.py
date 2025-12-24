import os
from datetime import datetime, timedelta, timezone

from src.tg_reader import read_messages
from src.matcher import match
from src.extractor import extract
from src.storage import save
from src.notifier import notify
from src.status import StatusWriter


def _get_channels_from_env() -> list[str]:
    raw = os.environ.get("TG_CHANNELS", "")
    return [c.strip() for c in raw.split(",") if c.strip()]


def main():
    status = StatusWriter()
    status.start()

    try:
        channels = _get_channels_from_env()
        if not channels:
            raise RuntimeError("TG_CHANNELS is empty or not set")

        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=24)

        messages = read_messages(
            channels=channels,
            since=since,
            until=None,
            limit_per_channel=100,
        )

        
        matched = match(messages)
        extracted = extract(matched)
        save(extracted, output_dir="output")

        notify({
            "messages_read": len(messages),
            "matched": len(matched),
            "snippets": len(extracted),
        })

        status.done({
            "messages_read": len(messages),
            "matched": len(matched),
            "snippets": len(extracted),
        })

    except Exception as e:
        status.error(str(e))
        raise


if __name__ == "__main__":
    main()

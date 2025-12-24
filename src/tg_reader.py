from typing import List, Dict
from datetime import datetime
import os

from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest


SESSION_PATH = "/home/micklib/smart-parser/alfred_test"


def _get_client() -> TelegramClient:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    return TelegramClient(
        SESSION_PATH,
        api_id,
        api_hash,
    )


def read_messages(
    channels: List[str],
    since: datetime,
    until: datetime | None = None,
    limit_per_channel: int = 100
) -> List[Dict]:
    """
    Reads raw messages from multiple Telegram channels.

    Contract (MVP v0.1):
    Returns a list of message dicts with at least:
    {
        "id": int,
        "date": datetime,
        "text": str,
        "url": str
    }

    - No keyword filtering
    - No storage
    - Pure data fetch
    """

    results: List[Dict] = []

    client = _get_client()
    client.connect()

    if not client.is_user_authorized():
        raise RuntimeError("Telegram client is not authorized (session invalid)")

    for channel in channels:
        history = client(
            GetHistoryRequest(
                peer=channel,
                offset_id=0,
                offset_date=until,
                add_offset=0,
                limit=limit_per_channel,
                max_id=0,
                min_id=0,
                hash=0,
            )
        )

        for msg in history.messages:
            if not msg.date or msg.date < since:
                continue

            results.append({
                "id": msg.id,
                "date": msg.date,
                "text": msg.message or "",
                "url": f"https://t.me/{channel.lstrip('@')}/{msg.id}",
            })

    client.disconnect()
    return results

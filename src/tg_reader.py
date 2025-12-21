from typing import List, Dict
from datetime import datetime


def read_messages(
    channel: str,
    since: datetime,
    until: datetime | None = None
) -> List[Dict]:
    """
    Reads raw messages from a Telegram channel.

    Contract (MVP v0.1):
    Returns a list of message dicts with at least:
    {
        "id": int,
        "date": datetime,
        "text": str,
        "url": str
    }

    - Does NOT filter by keywords
    - Does NOT modify text
    - Does NOT save anything
    - Stub implementation (returns empty list)
    """
    return []

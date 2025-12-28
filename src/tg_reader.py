from __future__ import annotations

from typing import List, Dict
from datetime import datetime, timezone
import os

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import RPCError, FloodWaitError
from urllib.parse import urlparse


# ============================================================
# Configuration
# ============================================================

SESSION_PATH = os.getenv(
    "TG_SESSION_PATH",
    "/home/micklib/smart-parser/alfred_test"
)


# ============================================================
# Helpers
# ============================================================

def _normalize_channel(ch: str) -> str:
    ch = ch.strip()
    if ch.startswith("http"):
        parsed = urlparse(ch)
        return parsed.path.lstrip("/").split("/")[0]
    return ch.lstrip("@").strip()


def _as_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _get_client() -> TelegramClient:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    return TelegramClient(
        SESSION_PATH,
        api_id,
        api_hash,
    )


# ============================================================
# Public API (task.yaml v1)
# ============================================================

def read_messages(
    *,
    channels: List[str],
    since: datetime,
    until: datetime | None = None,
    limit_per_channel: int = 200,
) -> List[Dict]:
    """
    tg_reader v1

    - Stateless
    - No keyword filtering
    - Graceful degradation per channel
    """

    results: List[Dict] = []

    if limit_per_channel <= 0:
        return results

    since_dt = _as_aware_utc(since)
    until_dt = _as_aware_utc(until) if until else None

    client = _get_client()

    with client:
        for raw_channel in channels:
            channel = _normalize_channel(raw_channel)

            try:
                history = client(
                    GetHistoryRequest(
                        peer=channel,
                        offset_id=0,
                        offset_date=until_dt,
                        add_offset=0,
                        limit=limit_per_channel,
                        max_id=0,
                        min_id=0,
                        hash=0,
                    )
                )

                for msg in history.messages:
                    if not msg.date:
                        continue

                    msg_date = _as_aware_utc(msg.date)
                    if msg_date < since_dt:
                        continue

                    results.append(
                        {
                            "source": "telegram",
                            "channel": channel,
                            "date": msg_date,
                            "text": msg.message or "",
                            "url": f"https://t.me/{channel}/{msg.id}",
                        }
                    )

            except FloodWaitError:
                # Telegram rate limit — skip channel, continue
                continue

            except RPCError:
                # Private / banned / inaccessible channel
                continue

            except Exception:
                # Absolute safety net — never crash pipeline
                continue

    return results

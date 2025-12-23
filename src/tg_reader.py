from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except Exception as e:  # pragma: no cover
    TelegramClient = None  # type: ignore
    StringSession = None  # type: ignore
    _telethon_import_error = e
else:
    _telethon_import_error = None


def _iso_z(dt: datetime) -> str:
    """Return ISO 8601 in UTC with trailing Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    s = dt.isoformat(timespec="seconds")
    return s.replace("+00:00", "Z")


def _normalize_channel(channel: str) -> str:
    # Accept "@name" or "name"
    ch = channel.strip()
    if ch.startswith("@"):
        ch = ch[1:]
    return ch


async def _read_messages_async(channel: str, since: Optional[datetime]) -> List[Dict[str, Any]]:
    if _telethon_import_error is not None:
        raise RuntimeError(
            "Telethon is not installed (or failed to import). "
            "Install it and retry. Original error: "
            f"{_telethon_import_error}"
        )

    api_id_raw = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    session_str = os.getenv("TG_SESSION")

    if not api_id_raw or not api_hash or not session_str:
        raise RuntimeError(
            "Missing Telegram credentials. Expected env vars: "
            "TG_API_ID, TG_API_HASH, TG_SESSION (Telethon StringSession)."
        )

    try:
        api_id = int(api_id_raw)
    except ValueError as e:
        raise RuntimeError("TG_API_ID must be an integer.") from e

    ch = _normalize_channel(channel)

    # since=None means: no date filter (fetch recent window and return all)
    since_utc: Optional[datetime] = None
    if since is not None:
        if since.tzinfo is None:
            since_utc = since.replace(tzinfo=timezone.utc)
        else:
            since_utc = since.astimezone(timezone.utc)

    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    messages: List[Dict[str, Any]] = []
    async with client:
        # We iterate from newest to oldest; stop once below since (if provided).
        async for m in client.iter_messages(ch, limit=None):
            # Skip non-text messages
            text = getattr(m, "message", None)
            if not text or not isinstance(text, str) or not text.strip():
                continue

            msg_dt = m.date
            if since_utc is not None and msg_dt < since_utc:
                break

            messages.append(
                {
                    "id": int(m.id),
                    "date": _iso_z(msg_dt),
                    "text": text,
                    "url": f"https://t.me/{ch}/{int(m.id)}",
                }
            )

    # We fetched newest->oldest; keep deterministic order oldest->newest for downstream.
    messages.reverse()
    return messages


def read_messages(channel: str, since: Optional[datetime]) -> list[dict]:
    """
    Fetch raw Telegram messages since date (no keyword filtering).
    Contract:
      returns list of dicts with keys: id, date, text, url
    Credentials:
      TG_API_ID (int), TG_API_HASH (str), TG_SESSION (Telethon StringSession)
    """
    return asyncio.run(_read_messages_async(channel=channel, since=since))

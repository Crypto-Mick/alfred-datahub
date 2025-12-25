from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _json_safe(value):
    """
    Recursively convert values to JSON-serializable types.
    """
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat() + "Z"
    return value


def _get_field(item: dict, key: str) -> str:
    value = item.get(key, "")
    return "" if value is None else str(value)


def _headline(text: str, max_len: int = 140) -> str:
    for sep in (". ", "! ", "? "):
        if sep in text:
            text = text.split(sep, 1)[0]
            break
    return text.strip()[:max_len] or "Event"


def _channel_from_url(url: str) -> str:
    parts = [p for p in url.split("/") if p]
    return f"@{parts[-2]}" if len(parts) >= 2 else "@unknown"


def save(
    snippets: list[dict],
    output_dir: str,
    *,
    lookback_hours: int,
    max_items: int,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # --- raw.json (machine-readable, JSON-safe) ---
    (output_path / "raw.json").write_text(
        json.dumps(_json_safe(snippets), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # --- result.md (human-readable) ---
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    lines: list[str] = [
        f"# Crypto Risk Summary — Last {lookback_hours} Hours",
        "",
        f"Period: last {lookback_hours} hours  ",
        "Sources: Telegram  ",
        f"Generated: {generated_at}",
        "",
        "---",
        "",
    ]

    if not snippets:
        lines.extend(
            [
                "## ⚠️ Key Events (0)",
                "",
                f"No significant events were detected in the last {lookback_hours} hours.",
            ]
        )
    else:
        events = snippets[:max_items]
        lines.append(f"## ⚠️ Key Events ({len(events)})")
        lines.append("")

        for idx, item in enumerate(events, start=1):
            text = _get_field(item, "snippet")
            url = _get_field(item, "url")
            keyword = _get_field(item, "keyword")

            lines.extend(
                [
                    f"### {idx}. {_headline(text)}",
                    f"**Source:** {_channel_from_url(url)}  ",
                    f"**Detected keywords:** {keyword}",
                    "",
                    text,
                    "",
                    f"🔗 {url}",
                    "",
                    "---",
                    "",
                ]
            )

    (output_path / "result.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

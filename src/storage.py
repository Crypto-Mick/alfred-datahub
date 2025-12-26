from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path


# =========================
# helpers (existing)
# =========================

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


# =========================
# result.md v1 helpers
# =========================

_URL_RE = re.compile(r"https?://\S+")


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = _URL_RE.sub("", text)
    text = " ".join(text.split())
    return text.strip()


def _text_fingerprint(text: str) -> str:
    norm = _normalize_text(text)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def _compute_importance(item: dict, include_keywords: list[str], now: datetime) -> int:
    score = 0
    text = item["snippet"].lower()

    # 1. keyword matches (full text)
    for kw in include_keywords:
        score += text.count(kw.lower())

    # 2. keyword in first line
    first_line = item["snippet"].splitlines()[0].lower() if item["snippet"] else ""
    for kw in include_keywords:
        if kw.lower() in first_line:
            score += 2

    # 3. length heuristic
    l = len(item["snippet"])
    if l > 500:
        score += 1
    if l > 1000:
        score += 2

    # 4. freshness
    age_hours = (now - item["date"]).total_seconds() / 3600
    if age_hours < 6:
        score += 2
    elif age_hours < 12:
        score += 1

    return score


def _prepare_items(
    snippets: list[dict],
    *,
    include_keywords: list[str],
    max_items: int,
) -> list[dict]:
    now = datetime.now(timezone.utc)

    # --- URL dedup ---
    seen_urls: set[str] = set()
    tmp: list[dict] = []
    for item in snippets:
        url = item.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        tmp.append(item)

    # --- text dedup ---
    seen_fp: set[str] = set()
    deduped: list[dict] = []
    for item in tmp:
        fp = _text_fingerprint(item.get("snippet", ""))
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        deduped.append(item)

    # --- compute importance_score ---
    for item in deduped:
        item["importance_score"] = _compute_importance(
            item,
            include_keywords=include_keywords,
            now=now,
        )

    # --- sort ---
    deduped.sort(
        key=lambda x: (x["importance_score"], x["date"]),
        reverse=True,
    )

    # --- limit ---
    return deduped[:max_items]


# =========================
# main entry
# =========================

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

    # --- prepare result items ---
    include_keywords = sorted(
        {item.get("keyword", "").lower() for item in snippets if item.get("keyword")}
    )

    items = _prepare_items(
        snippets,
        include_keywords=include_keywords,
        max_items=max_items,
    )

    # --- result.md (human-readable) ---
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    lines: list[str] = [
        "# Result",
        "",
        f"Task: crypto-risk-last-24h",
        f"Lookback: {lookback_hours} hours",
        f"Generated: {generated_at} UTC",
        "",
        "---",
        "",
        f"## Items ({len(items)})",
        "",
    ]

    if not items:
        lines.extend(
            [
                f"No significant events were detected in the last {lookback_hours} hours.",
                "",
            ]
        )
    else:
        for idx, item in enumerate(items, start=1):
            text = _get_field(item, "snippet")
            url = _get_field(item, "url")
            source = _channel_from_url(url)
            date = item.get("date")
            date_str = date.isoformat() + "Z" if isinstance(date, datetime) else ""

            lines.extend(
                [
                    f"{idx}. {_headline(text)}",
                    "",
                    f"   Source: {source}",
                    f"   Date: {date_str}",
                    f"   URL: {url}",
                    "",
                    f"   {text}",
                    "",
                    "---",
                    "",
                ]
            )

    (output_path / "result.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

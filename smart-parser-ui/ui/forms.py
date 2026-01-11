# ui/forms.py
import streamlit as st

DAY_OPTIONS = {
    "1 day": 1,
    "3 days": 3,
    "7 days": 7,
    "30 days": 30,
    "90 days": 90,
}


def _parse_csv(value: str) -> list[str]:
    # split by comma, trim, drop empties, dedup (preserve order)
    items: list[str] = []
    seen = set()
    for raw in value.split(","):
        item = raw.strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def _parse_lines(value: str) -> list[str]:
    # one per line, trim, drop empties, dedup (preserve order)
    items: list[str] = []
    seen = set()
    for raw in value.splitlines():
        item = raw.strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def render_telegram_form() -> dict:
    channels_raw = st.text_input(
        "Channels (comma-separated)",
        help='Example: cryptokogan, @some_channel, https://t.me/some_channel',
        key="tg_channels",
    )

    keywords_raw = st.text_input(
        "Keywords (comma-separated)",
        help="Required. Case-insensitive match in text.",
        key="tg_keywords",
    )

    days_label = st.selectbox(
        "Lookback (days)",
        list(DAY_OPTIONS.keys()),
        index=0,
        key="tg_days",
    )

    channels = _parse_csv(channels_raw)
    keywords = _parse_csv(keywords_raw)
    days = int(DAY_OPTIONS[days_label])

    # event_text_v1 human-input контракт:
    # top-level: keywords + telegram/web + days (optional)
    return {
        "keywords": keywords,
        "telegram": {"channels": channels},
        "days": days,
    }


def render_web_form() -> dict:
    urls_raw = st.text_area(
        "URLs / RSS (one per line)",
        help="Example: https://example.com/rss.xml",
        key="web_urls",
    )

    keywords_raw = st.text_input(
        "Keywords (comma-separated)",
        help="Required. Case-insensitive match in text.",
        key="web_keywords",
    )

    days_label = st.selectbox(
        "Lookback (days)",
        list(DAY_OPTIONS.keys()),
        index=0,
        key="web_days",
    )

    urls = _parse_lines(urls_raw)
    keywords = _parse_csv(keywords_raw)
    days = int(DAY_OPTIONS[days_label])

    return {
        "keywords": keywords,
        "web": {"urls": urls},
        "days": days,
    }

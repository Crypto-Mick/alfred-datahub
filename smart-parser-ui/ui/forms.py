import streamlit as st

LOOKBACK_OPTIONS = {
    "6h": 6,
    "24h": 24,
    "3 days": 72,
    "7 days": 168,
    "3 months": 2160,
}


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def render_telegram_form() -> dict:
    channels = st.text_input(
        "Channels (comma-separated)",
        key="tg_channels",
    )

    keywords = st.text_input(
        "Keywords (comma-separated)",
        help="Required",
        key="tg_keywords",
    )

    lookback_label = st.selectbox(
        "Lookback",
        list(LOOKBACK_OPTIONS.keys()),
        key="tg_lookback",
    )

    max_items = st.number_input("Max items", min_value=1, value=20, step=1)

    return {
        "sources": {
            "telegram": {
                "channels": _parse_csv(channels),
            },
            "web": {
                "sites": [],
            },
        },
        "keywords": _parse_csv(keywords),
        "lookback_hours": LOOKBACK_OPTIONS[lookback_label],
        "max_items": int(max_items),
    }


def render_web_form() -> dict:
    sites = st.text_area(
        "Sites/RSS (one per line)",
        key="web_sites",
    )

    keywords = st.text_input(
        "Keywords (comma-separated)",
        help="Required",
        key="web_keywords",
    )

    lookback_label = st.selectbox(
        "Lookback",
        list(LOOKBACK_OPTIONS.keys()),
        key="web_lookback",
    )

    max_items = st.number_input("Max items", min_value=1, value=20, step=1)

    sites_list = [line.strip() for line in sites.splitlines() if line.strip()]

    return {
        "sources": {
            "telegram": {
                "channels": [],
            },
            "web": {
                "sites": sites_list,
            },
        },
        "keywords": _parse_csv(keywords),
        "lookback_hours": LOOKBACK_OPTIONS[lookback_label],
        "max_items": int(max_items),
    }

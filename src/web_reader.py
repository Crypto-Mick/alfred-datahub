from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


# ============================================================
# Helpers
# ============================================================

class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(" ".join(self._parts).split())


def _strip_html(s: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(s or "")
    return stripper.get_text().strip()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_rfc822_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return _as_aware_datetime(parsedate_to_datetime(value))
    except Exception:
        return None


def fetch_url(url: str, timeout_seconds: int = 20) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "alfred-datahub/1.0",
            "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urlopen(req, timeout=timeout_seconds) as resp:
        raw = resp.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _normalize_site(site: str) -> str:
    site = site.strip()
    if "://" in site:
        parsed = urlparse(site)
        return parsed.netloc.lower()
    return site.lower()


# ============================================================
# RSS parsing (internal discovery)
# ============================================================

def _first_text(elem: ET.Element, paths: list[str]) -> str:
    for p in paths:
        child = elem.find(p)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def parse_rss(xml_text: str, site: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []

    for it in root.findall("./channel/item"):
        title = _first_text(it, ["title"])
        link = _first_text(it, ["link"])
        pub_date_raw = _first_text(it, ["pubDate"])
        dt = _parse_rfc822_date(pub_date_raw)

        desc = _first_text(it, ["description"])
        content = _first_text(it, ["{http://purl.org/rss/1.0/modules/content/}encoded"])
        summary = _strip_html(content or desc)

        if not link:
            continue

        items.append(
            {
                "source": "web",
                "site": site,
                "title": title or "",
                "date": dt,
                "text": summary or "",
                "url": link,
            }
        )

    return items


# ============================================================
# Site → RSS routing
# ============================================================

_SITE_FEEDS: dict[str, str] = {
    "3dnews.ru": "https://3dnews.ru/rss",
}


def _get_feed_url(site: str) -> str:
    key = _normalize_site(site)
    if key in _SITE_FEEDS:
        return _SITE_FEEDS[key]
    raise RuntimeError(f"No RSS feed configured for site: {site}")


# ============================================================
# Site-specific article extraction
# ============================================================

class _ArticleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self._depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "div":
            attrs_dict = dict(attrs)
            if attrs_dict.get("class") == "article-content":
                self._capture = True
                self._depth = 1
                return
        if self._capture:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._capture:
            self._depth -= 1
            if self._depth <= 0:
                self._capture = False

    def handle_data(self, data: str) -> None:
        if self._capture and data:
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(" ".join(self._parts).split())


def extract_3dnews_article_text(html: str) -> str:
    parser = _ArticleTextExtractor()
    parser.feed(html)
    return parser.get_text().strip()


# ============================================================
# Public API (task.yaml v1)
# ============================================================

def read_site_items(
    *,
    site: str,
    lookback_hours: int,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Public v1 API.

    site            - URL or hostname from task.yaml
    lookback_hours  - common lookback window
    now             - optional override (for testing)
    """

    if lookback_hours <= 0:
        raise ValueError("lookback_hours must be positive")

    now_dt = _as_aware_datetime(now) if now else _now_utc()
    since = now_dt - timedelta(hours=lookback_hours)

    feed_url = _get_feed_url(site)
    rss_xml = fetch_url(feed_url)
    
    try:
        discovered = parse_rss(rss_xml, site)
    except Exception:
        # Broken RSS / HTML instead of XML / transient error
        return []
    out: list[dict[str, Any]] = []

    for it in discovered:
        dt = it.get("date")
        if not isinstance(dt, datetime):
            continue

        dt = _as_aware_datetime(dt)
        if dt < since:
            continue

        full_text = ""
        try:
            html = fetch_url(it["url"])
            if _normalize_site(site) == "3dnews.ru":
                full_text = extract_3dnews_article_text(html)
        except Exception:
            full_text = ""

        text = full_text or it.get("text", "")

        out.append(
            {
                "source": "web",
                "site": site,
                "title": str(it.get("title", "")),
                "date": dt,
                "text": text,
                "url": str(it.get("url", "")),
            }
        )

    return out

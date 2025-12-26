from datetime import datetime, timezone

import src.web_reader as wr


RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>3DNews</title>
    <item>
      <title>DDR5 prices drop</title>
      <link>https://3dnews.ru/111111/</link>
      <pubDate>Fri, 26 Dec 2025 10:00:00 +0000</pubDate>
      <description><![CDATA[<p>Short RSS summary</p>]]></description>
    </item>
    <item>
      <title>Old item</title>
      <link>https://3dnews.ru/000000/</link>
      <pubDate>Fri, 01 Jan 2021 10:00:00 +0000</pubDate>
      <description>old</description>
    </item>
  </channel>
</rss>
"""


ARTICLE_HTML = """
<html>
  <body>
    <div class="article-content">
      <p>DDR5 memory price dropped significantly due to market changes.</p>
      <p>This affects RAM costs worldwide.</p>
    </div>
  </body>
</html>
"""


ARTICLE_HTML_NO_CONTENT = """
<html>
  <body>
    <div class="other-content">
      <p>No article body here</p>
    </div>
  </body>
</html>
"""


def test_parse_rss_discovery_layer_only():
    items = wr.parse_rss(RSS_SAMPLE, "3dnews.ru")

    assert len(items) == 2

    item = items[0]
    assert item["source"] == "web"
    assert item["site"] == "3dnews.ru"
    assert item["title"] == "DDR5 prices drop"
    assert item["url"] == "https://3dnews.ru/111111/"
    assert isinstance(item["text"], str)
    assert item["text"] == "Short RSS summary"


def test_read_site_items_uses_full_article_text(monkeypatch):
    def fake_fetch(url: str, timeout_seconds: int = 20) -> str:
        if url.endswith("/rss"):
            return RSS_SAMPLE
        return ARTICLE_HTML

    monkeypatch.setattr(wr, "fetch_url", fake_fetch)

    now = datetime(2025, 12, 26, 12, 0, tzinfo=timezone.utc)

    items = wr.read_site_items(
        site="3dnews.ru",
        feed_url="https://3dnews.ru/rss",
        lookback_hours=168,
        now=now,
    )

    assert len(items) == 1
    text = items[0]["text"]
    assert "DDR5 memory price dropped significantly" in text
    assert "Short RSS summary" not in text


def test_read_site_items_fallback_to_rss_on_parse_failure(monkeypatch):
    def fake_fetch(url: str, timeout_seconds: int = 20) -> str:
        if url.endswith("/rss"):
            return RSS_SAMPLE
        return ARTICLE_HTML_NO_CONTENT

    monkeypatch.setattr(wr, "fetch_url", fake_fetch)

    now = datetime(2025, 12, 26, 12, 0, tzinfo=timezone.utc)

    items = wr.read_site_items(
        site="3dnews.ru",
        feed_url="https://3dnews.ru/rss",
        lookback_hours=168,
        now=now,
    )

    assert len(items) == 1
    assert items[0]["text"] == "Short RSS summary"


def test_read_site_items_filters_by_lookback(monkeypatch):
    def fake_fetch(url: str, timeout_seconds: int = 20) -> str:
        return RSS_SAMPLE

    monkeypatch.setattr(wr, "fetch_url", fake_fetch)

    now = datetime(2025, 12, 26, 12, 0, tzinfo=timezone.utc)

    items = wr.read_site_items(
        site="3dnews.ru",
        feed_url="https://3dnews.ru/rss",
        lookback_hours=24,
        now=now,
    )

    assert len(items) == 1
    assert items[0]["url"] == "https://3dnews.ru/111111/"

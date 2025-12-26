from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src import storage


LOOKBACK_HOURS = 24
MAX_ITEMS = 10


def _dt():
    return datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_save_creates_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    storage.save(
        [],
        str(output_dir),
        lookback_hours=LOOKBACK_HOURS,
        max_items=MAX_ITEMS,
    )
    assert output_dir.exists()


def test_save_creates_files_when_empty(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    storage.save(
        [],
        str(output_dir),
        lookback_hours=LOOKBACK_HOURS,
        max_items=MAX_ITEMS,
    )
    assert (output_dir / "raw.json").exists()
    assert (output_dir / "result.md").exists()


def test_save_raw_json_contains_normalized_items(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    snippets = [
        {
            "date": _dt(),
            "keyword": "alpha",
            "url": "u",
            "snippet": "s",
        }
    ]

    storage.save(
        snippets,
        str(output_dir),
        lookback_hours=LOOKBACK_HOURS,
        max_items=MAX_ITEMS,
    )

    raw_data = json.loads(
        (output_dir / "raw.json").read_text(encoding="utf-8")
    )

    assert len(raw_data) == 1
    item = raw_data[0]

    # semantic checks
    assert item["url"] == "u"
    assert item["snippet"] == "s"
    assert item["keyword"] == "alpha"

    # date normalized to ISO string
    assert isinstance(item["date"], str)
    assert item["date"].startswith("2024-01-01T")


def test_save_result_md_empty(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    storage.save(
        [],
        str(output_dir),
        lookback_hours=LOOKBACK_HOURS,
        max_items=MAX_ITEMS,
    )
    content = (output_dir / "result.md").read_text(encoding="utf-8")

    assert "No significant events" in content
    assert "last 24 hours" in content


def test_save_result_md_contains_core_fields(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    snippets = [
        {
            "date": _dt(),
            "keyword": "alpha",
            "url": "https://example.com",
            "snippet": "Some text",
        }
    ]

    storage.save(
        snippets,
        str(output_dir),
        lookback_hours=LOOKBACK_HOURS,
        max_items=MAX_ITEMS,
    )

    content = (output_dir / "result.md").read_text(encoding="utf-8")

    assert "2024-01-01" in content
    assert "https://example.com" in content
    assert "Some text" in content

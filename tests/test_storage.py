from __future__ import annotations

import copy
import json
from pathlib import Path

from src import storage


def test_save_creates_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    storage.save([], str(output_dir))
    assert output_dir.exists()


def test_save_creates_files_when_empty(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    storage.save([], str(output_dir))
    assert (output_dir / "raw.json").exists()
    assert (output_dir / "result.md").exists()


def test_save_raw_json_round_trip(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    snippets = [{"date": "2024-01-01", "keyword": "alpha", "url": "u", "snippet": "s"}]
    storage.save(snippets, str(output_dir))
    raw_data = json.loads((output_dir / "raw.json").read_text(encoding="utf-8"))
    assert raw_data == snippets


def test_save_result_md_empty(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    storage.save([], str(output_dir))
    content = (output_dir / "result.md").read_text(encoding="utf-8")
    assert "No matches found." in content


def test_save_result_md_fields(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    snippets = [
        {
            "date": "2024-01-01",
            "keyword": "alpha",
            "url": "https://example.com",
            "snippet": "Some text",
        }
    ]
    storage.save(snippets, str(output_dir))
    content = (output_dir / "result.md").read_text(encoding="utf-8")
    assert "## 2024-01-01 — alpha" in content
    assert "https://example.com" in content
    assert "Some text" in content


def test_save_does_not_mutate_snippets(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    snippets = [{"date": "2024-01-01", "keyword": "alpha", "url": "u", "snippet": "s"}]
    original = copy.deepcopy(snippets)
    storage.save(snippets, str(output_dir))
    assert snippets == original

"""Storage module for Alfred Data Hub."""
from __future__ import annotations

import json
from pathlib import Path


def _get_field(value: dict, key: str) -> str:
    field = value.get(key, "")
    return "" if field is None else str(field)


def save(snippets: list[dict], output_dir: str) -> None:
    """
    Saves:
    - raw.json (machine source of truth)
    - result.md (human-readable)
    Always creates both files even if snippets is empty.
    Must create output_dir if missing.
    No other side effects.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_path = output_path / "raw.json"
    result_path = output_path / "result.md"

    raw_path.write_text(json.dumps(snippets, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = ["# Alfred Data Hub — Results"]
    if not snippets:
        lines.append("No matches found.")
    else:
        for snippet in snippets:
            date = _get_field(snippet, "date")
            keyword = _get_field(snippet, "keyword")
            url = _get_field(snippet, "url")
            snippet_text = _get_field(snippet, "snippet")
            lines.append(f"## {date} — {keyword}")
            lines.append(url)
            lines.append("")
            lines.append(snippet_text)
            lines.append("")

    result_path.write_text("\n".join(lines), encoding="utf-8")

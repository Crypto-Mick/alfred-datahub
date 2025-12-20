from __future__ import annotations

import re
from typing import Dict, List


def _find_paragraph(text: str, keyword: str) -> str | None:
    paragraphs = re.split(r"\n\s*\n+", text)
    keyword_lower = keyword.lower()
    for paragraph in paragraphs:
        if keyword_lower in paragraph.lower():
            return paragraph
    return None


def _find_sentence_window(text: str, keyword: str) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    keyword_lower = keyword.lower()
    for index, sentence in enumerate(sentences):
        if keyword_lower in sentence.lower():
            start = max(index - 1, 0)
            end = min(index + 1, len(sentences) - 1)
            return " ".join(sentences[start : end + 1])
    return None


def extract(messages: List[Dict], keywords: List[str]) -> List[Dict]:
    """
    Extracts paragraph or 1–2 sentences around keyword occurrence.

    - Does NOT filter messages
    - Does NOT perform any I/O
    - Returns list of snippet objects
    """
    if not messages or not keywords:
        return []

    snippets: List[Dict] = []
    for message in messages:
        text = message.get("text")
        if not text:
            continue
        for keyword in keywords:
            if keyword.lower() not in text.lower():
                continue
            snippet = _find_paragraph(text, keyword)
            if snippet is None:
                snippet = _find_sentence_window(text, keyword)
            if snippet is None:
                snippet = text
            snippets.append(
                {
                    "post_id": message.get("id"),
                    "date": message.get("date"),
                    "url": message.get("url"),
                    "keyword": keyword,
                    "snippet": snippet,
                }
            )
    return snippets

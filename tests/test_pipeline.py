import inspect
from datetime import datetime, timezone
from pathlib import Path

from src import extractor, main, matcher, notifier, status, storage, tg_reader


def test_pipeline_imports() -> None:
    assert extractor is not None
    assert main is not None
    assert matcher is not None
    assert notifier is not None
    assert status is not None
    assert storage is not None
    assert tg_reader is not None


def test_function_signatures_match_call_sites() -> None:
    match_params = list(inspect.signature(matcher.match).parameters)
    assert match_params[:2] == ["messages", "keywords"]

    extract_params = list(inspect.signature(extractor.extract).parameters)
    assert extract_params[:2] == ["messages", "keywords"]

    read_params = list(inspect.signature(tg_reader.read_messages).parameters)
    assert read_params[:2] == ["channels", "since"]


def test_main_smoke(tmp_path: Path, monkeypatch) -> None:
    """
    Smoke test for main pipeline with task.yaml v1 as single source of truth.
    No ENV usage. No network. No storage side effects.
    """

    calls = {}

    # --- telegram reader mock ---
    def fake_read_messages(*, channels, since, until, limit_per_channel):
        calls["read_messages"] = {
            "channels": channels,
            "since": since,
            "until": until,
            "limit": limit_per_channel,
        }
        return [
            {
                "id": 1,
                "date": datetime.now(timezone.utc),
                "text": "alpha security breach",
                "url": "https://t.me/test/1",
            }
        ]

    # --- matcher mock ---
    def fake_match(messages, keywords):
        calls["match"] = {
            "messages": messages,
            "keywords": keywords,
        }
        return messages

    # --- extractor mock ---
    def fake_extract(messages, keywords):
        calls["extract"] = {
            "messages": messages,
            "keywords": keywords,
        }
        return [
            {
                "post_id": 1,
                "date": "2025-01-01",
                "url": "https://t.me/test/1",
                "keyword": keywords[0],
                "snippet": "alpha security breach",
            }
        ]

    # --- storage mock (new contract) ---
    def fake_save(*, snippets, output_dir, lookback_hours, max_items):
        calls["save"] = {
            "snippets": snippets,
            "output_dir": output_dir,
            "lookback_hours": lookback_hours,
            "max_items": max_items,
        }

    # --- status mocks ---
    def fake_mark_running(*, result_path=None):
        return "started"

    def fake_mark_done(*, started_at, stats, result_path=None):
        calls["done"] = stats

    def fake_mark_error(*, started_at, stats, error, result_path=None):
        raise AssertionError(f"Pipeline errored: {error}")

    # --- patch ---
    monkeypatch.setattr(main, "read_messages", fake_read_messages)
    monkeypatch.setattr(main, "match", fake_match)
    monkeypatch.setattr(main, "extract", fake_extract)
    monkeypatch.setattr(main, "save", fake_save)
    monkeypatch.setattr(main, "mark_running", fake_mark_running)
    monkeypatch.setattr(main, "mark_done", fake_mark_done)
    monkeypatch.setattr(main, "mark_error", fake_mark_error)

    # redirect output dir
    monkeypatch.setattr(main, "OUTPUT_DIR", str(tmp_path))

    # --- run ---
    main.main()

    # --- assertions ---
    assert "read_messages" in calls
    assert calls["read_messages"]["channels"], "channels must come from task.yaml"

    assert "match" in calls
    assert "extract" in calls
    assert "save" in calls

    assert calls["save"]["lookback_hours"] > 0
    assert calls["save"]["max_items"] > 0

    assert calls["done"]["matched"] == 1

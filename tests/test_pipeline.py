import inspect
from datetime import datetime, timezone

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


def test_main_smoke(monkeypatch) -> None:
    monkeypatch.setenv("TG_CHANNELS", "test_channel")
    monkeypatch.setenv("KEYWORDS", "alpha,beta")

    calls = {}

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
                "text": "alpha message",
                "url": "https://t.me/test_channel/1",
            }
        ]

    def fake_match(messages, keywords):
        calls["match"] = {"keywords": keywords, "messages": messages}
        return messages

    def fake_extract(messages, keywords):
        calls["extract"] = {"keywords": keywords, "messages": messages}
        return [
            {
                "post_id": 1,
                "date": "2025-01-01",
                "url": "https://t.me/test_channel/1",
                "keyword": keywords[0],
                "snippet": "alpha message",
            }
        ]

    def fake_save(snippets, output_dir):
        calls["save"] = {"snippets": snippets, "output_dir": output_dir}

    def fake_mark_running(*, result_path=None):
        calls["mark_running"] = {"result_path": result_path}
        return "started"

    def fake_mark_done(*, started_at, stats, result_path=None):
        calls["mark_done"] = {
            "started_at": started_at,
            "stats": stats,
            "result_path": result_path,
        }

    def fake_mark_error(*, started_at, stats, error, result_path=None):
        calls["mark_error"] = {
            "started_at": started_at,
            "stats": stats,
            "error": error,
            "result_path": result_path,
        }

    monkeypatch.setattr(main, "read_messages", fake_read_messages)
    monkeypatch.setattr(main, "match", fake_match)
    monkeypatch.setattr(main, "extract", fake_extract)
    monkeypatch.setattr(main, "save", fake_save)
    monkeypatch.setattr(main, "mark_running", fake_mark_running)
    monkeypatch.setattr(main, "mark_done", fake_mark_done)
    monkeypatch.setattr(main, "mark_error", fake_mark_error)

    main.main()

    assert calls["read_messages"]["channels"] == ["test_channel"]
    assert calls["match"]["keywords"] == ["alpha", "beta"]
    assert calls["extract"]["keywords"] == ["alpha", "beta"]
    assert calls["mark_done"]["stats"]["matched"] == 1

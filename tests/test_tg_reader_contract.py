import pytest
from datetime import datetime

from src import tg_reader


def test_read_messages_contract_without_env(monkeypatch):
    """
    tg_reader must fail fast when Telegram credentials are missing.

    Contract:
    - no network calls
    - deterministic KeyError
    - explicit missing credential
    """

    # гарантируем отсутствие переменных окружения
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.delenv("TG_API_HASH", raising=False)
    monkeypatch.delenv("TG_SESSION", raising=False)

    with pytest.raises(KeyError) as exc:
        tg_reader.read_messages(
            channels=["test_channel"],
            since=datetime.utcnow(),
            until=None,
            limit_per_channel=10,
        )

    msg = str(exc.value)
    assert "TG_API_ID" in msg or "TG_API_HASH" in msg

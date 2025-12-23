import pytest
from datetime import datetime

from src import tg_reader


def test_read_messages_contract_without_env():
    """
    tg_reader must fail with a clear error if Telegram credentials are missing.
    This validates:
      - module imports
      - function exists
      - error is explicit and deterministic
    """
    with pytest.raises(RuntimeError) as exc:
        tg_reader.read_messages(channel="test_channel", since=datetime.utcnow())

    msg = str(exc.value)
    assert "TG_API_ID" in msg
    assert "TG_API_HASH" in msg
    assert "TG_SESSION" in msg

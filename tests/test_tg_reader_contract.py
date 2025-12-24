import pytest
from datetime import datetime

from src import tg_reader


def test_read_messages_contract_without_env():
    """
    tg_reader must fail when Telegram credentials are missing.
    This validates:
      - module imports
      - function exists
      - error is deterministic
    """
    with pytest.raises(KeyError) as exc:
        tg_reader.read_messages(channels=["test_channel"], since=datetime.utcnow())

    assert "TG_API_ID" in str(exc.value)

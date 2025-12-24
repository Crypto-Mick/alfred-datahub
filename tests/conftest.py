from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import telethon  # noqa: F401
except ModuleNotFoundError:
    import types

    telethon_stub = types.ModuleType("telethon")
    telethon_sync_stub = types.ModuleType("telethon.sync")
    telethon_tl_stub = types.ModuleType("telethon.tl")
    telethon_tl_functions_stub = types.ModuleType("telethon.tl.functions")
    telethon_tl_messages_stub = types.ModuleType("telethon.tl.functions.messages")

    class TelegramClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __call__(self, *args, **kwargs):
            raise RuntimeError("TelegramClient stub called in tests")

    class GetHistoryRequest:
        def __init__(self, *args, **kwargs):
            pass

    telethon_sync_stub.TelegramClient = TelegramClient
    telethon_tl_messages_stub.GetHistoryRequest = GetHistoryRequest

    sys.modules["telethon"] = telethon_stub
    sys.modules["telethon.sync"] = telethon_sync_stub
    sys.modules["telethon.tl"] = telethon_tl_stub
    sys.modules["telethon.tl.functions"] = telethon_tl_functions_stub
    sys.modules["telethon.tl.functions.messages"] = telethon_tl_messages_stub

# ui/state.py
from dataclasses import dataclass, field


@dataclass
class UiState:
    # event_text_v1-aligned state (kept minimal; may be unused by current UI)
    keywords: list[str] = field(default_factory=list)
    days: int = 1
    telegram_channels: list[str] = field(default_factory=list)
    web_urls: list[str] = field(default_factory=list)

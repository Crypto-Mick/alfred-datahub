from dataclasses import dataclass, field


@dataclass
class UiState:
    keywords: list[str] = field(default_factory=list)
    lookback_hours: int = 72
    max_items: int = 20

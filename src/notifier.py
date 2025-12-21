"""Notification module for Alfred Data Hub."""
from __future__ import annotations

import json


def notify(task_name: str, output_dir: str, stats: dict) -> None:
    """
    Sends completion notification. v0.1: stdout only.
    """
    message = (
        f"Task '{task_name}' completed. Output: {output_dir}. "
        f"Stats: {json.dumps(stats, ensure_ascii=False)}"
    )
    print(message)

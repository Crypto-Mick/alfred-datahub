from __future__ import annotations

import json

from src import notifier


def test_notify_prints_single_line(capsys) -> None:
    notifier.notify("task", "/tmp/output", {"count": 1})
    captured = capsys.readouterr()
    output_lines = captured.out.strip().splitlines()
    assert len(output_lines) == 1


def test_notify_includes_task_and_output_dir(capsys) -> None:
    notifier.notify("my-task", "/path/out", {"count": 2})
    captured = capsys.readouterr()
    assert "my-task" in captured.out
    assert "/path/out" in captured.out


def test_notify_includes_stats(capsys) -> None:
    stats = {"count": 3, "errors": 0}
    notifier.notify("task", "/out", stats)
    captured = capsys.readouterr()
    assert json.dumps(stats, ensure_ascii=False) in captured.out

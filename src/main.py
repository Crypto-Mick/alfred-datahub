from pathlib import Path

from src.tg_reader import read_messages
from src.matcher import match
from src.extractor import extract
from src.storage import save
from src.notifier import notify
from src.status import init_idle_status, mark_running, mark_done, mark_error


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
RESULT_MD = OUTPUT_DIR / "result.md"


def main() -> None:
    # ensure idle status exists before run
    init_idle_status(result_path=str(RESULT_MD))

    started_at = None
    stats = {
        "messages_read": 0,
        "matched": 0,
        "snippets": 0,
    }

    try:
        started_at = mark_running(result_path=str(RESULT_MD))

        # === pipeline ===
        messages = read_messages(
            channel="stub",
            since=None,
        )
        stats["messages_read"] = len(messages)

        matched = match(
            messages=messages,
            keywords=["Funding Rate", "Open Interest"],
        )
        stats["matched"] = len(matched)

        snippets = extract(
            messages=matched,
            keywords=["Funding Rate", "Open Interest"],
        )
        stats["snippets"] = len(snippets)

        save(
            snippets=snippets,
            output_dir=str(OUTPUT_DIR),
        )

        notify(
            task_name="alfred-datahub-manual",
            output_dir=str(OUTPUT_DIR),
            stats=stats,
        )

        mark_done(
            started_at=started_at,
            stats=stats,
            result_path=str(RESULT_MD),
        )

    except Exception as e:
        mark_error(
            started_at=started_at,
            stats=stats,
            error=str(e),
            result_path=str(RESULT_MD),
        )
        raise


if __name__ == "__main__":
    main()

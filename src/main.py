from datetime import datetime, timedelta

from src.tg_reader import read_messages
from src.matcher import match
from src.extractor import extract
from src.storage import save
from src.notifier import notify


def main() -> None:
    """
    Main orchestration function for Alfred Data Hub (MVP v0.1).

    This function:
    - defines input parameters
    - runs the processing pipeline step by step
    - saves results
    - sends a completion notification
    """

    # ===== 1. Parameters (MVP v0.1: defined directly in code) =====

    channel = "example_channel"
    keywords = ["example", "keyword"]

    # Time window: last 7 days
    until = datetime.utcnow()
    since = until - timedelta(days=7)

    output_dir = "output"

    # ===== 2. Read raw messages =====

    messages = read_messages(
        channel=channel,
        since=since,
        until=until,
    )

    # ===== 3. Filter messages by keywords =====

    matched_messages = match(messages, keywords)

    # ===== 4. Extract human-readable snippets =====

    snippets = extract(matched_messages, keywords)

    # ===== 5. Save results =====

    save(snippets, output_dir)

    # ===== 6. Notify completion =====

    stats = {
        "messages_read": len(messages),
        "messages_matched": len(matched_messages),
        "snippets_created": len(snippets),
    }

    notify(
        task_name="alfred-datahub-mvp",
        output_dir=output_dir,
        stats=stats,
    )


if __name__ == "__main__":
    main()

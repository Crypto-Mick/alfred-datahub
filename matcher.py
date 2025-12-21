from typing import List, Dict


def match(messages: List[Dict], keywords: List[str]) -> List[Dict]:
    """
    Returns messages containing at least one keyword (case-insensitive).

    Rules:
    - messages: list of message dictionaries
    - keywords: list of strings
    - return only messages where message["text"] contains at least one keyword
    - keyword matching must be case-insensitive
    - message objects must be returned unchanged
    - no snippet extraction
    - no filtering by date or any other field
    - no I/O of any kind

    Behavior:
    - If messages is empty or keywords is empty, return an empty list.
    - If a message has no "text" field or empty text, it should not match.
    - Matching stops on the first keyword match per message.

    Constraints:
    - One responsibility only.
    - No extra helper functions unless strictly necessary.
    - No logging, printing, or comments outside the docstring.
    - No additional features or "improvements".
    """
    if not messages or not keywords:
        return []

    lowered_keywords = [keyword.lower() for keyword in keywords]
    matched_messages = []

    for message in messages:
        text = message.get("text")
        if not text:
            continue
        lowered_text = text.lower()
        for keyword in lowered_keywords:
            if keyword in lowered_text:
                matched_messages.append(message)
                break

    return matched_messages

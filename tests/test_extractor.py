import copy

from src.extractor import extract


def test_empty_inputs_return_empty_list():
    assert extract([], ["alpha"]) == []
    assert extract([{"id": 1, "text": "alpha"}], []) == []


def test_paragraph_extraction_prefers_blank_lines():
    messages = [
        {
            "id": 1,
            "date": "2025-12-01T12:34:56",
            "text": "First paragraph.\n\nSecond paragraph with keyword.",
            "url": "https://t.me/test/1",
        }
    ]
    result = extract(messages, ["keyword"])
    assert result[0]["snippet"] == "Second paragraph with keyword."


def test_sentence_fallback_extracts_window():
    text = "First sentence. Second sentence has keyword. Third sentence."
    messages = [
        {
            "id": 2,
            "date": "2025-12-02T00:00:00",
            "text": text,
            "url": "https://t.me/test/2",
        }
    ]
    result = extract(messages, ["keyword"])
    assert (
        result[0]["snippet"]
        == "First sentence. Second sentence has keyword. Third sentence."
    )


def test_case_insensitive_matching_and_output_fields():
    messages = [
        {
            "id": 3,
            "date": "2025-12-03T00:00:00",
            "text": "Alpha appears here.",
            "url": "https://t.me/test/3",
        }
    ]
    result = extract(messages, ["alpha"])
    assert result == [
        {
            "post_id": 3,
            "date": "2025-12-03T00:00:00",
            "url": "https://t.me/test/3",
            "keyword": "alpha",
            "snippet": "Alpha appears here.",
        }
    ]


def test_input_messages_not_modified():
    messages = [
        {
            "id": 4,
            "date": "2025-12-04T00:00:00",
            "text": "Keyword present.",
            "url": "https://t.me/test/4",
        }
    ]
    original = copy.deepcopy(messages)
    extract(messages, ["keyword"])
    assert messages == original

# src/api_reader.py

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Sequence


# ----------------------------
# Public config / constants
# ----------------------------

DEFAULT_SERVER: str = "west"

BASE_URL_BY_SERVER: Dict[str, str] = {
    "west": "https://west.albion-online-data.com",
    "east": "https://east.albion-online-data.com",
    "europe": "https://europe.albion-online-data.com",
}

API_PREFIX: str = "/api/v2/stats"
PRICES_ENDPOINT_FMT: str = API_PREFIX + "/prices/{item_id}"


# ----------------------------
# Errors
# ----------------------------

class ApiReaderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        url: str,
        status_code: Optional[int] = None,
        response_snippet: Optional[str] = None,
    ):
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.response_snippet = response_snippet


# ----------------------------
# Public API
# ----------------------------

def read_price_snapshots(
    *,
    server: str,
    item_ids: Sequence[str],
    locations: Sequence[str],
    qualities: Sequence[int],
    timeout_s: float = 10.0,
    user_agent: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch price snapshots from Albion Data Project (/stats/prices).

    Returns list of api-item v1 dicts (price_snapshot).
    """

    _validate_inputs(
        server=server,
        item_ids=item_ids,
        locations=locations,
        qualities=qualities,
    )

    results: List[Dict[str, Any]] = []

    for item_id in item_ids:
        url = _build_prices_url(
            server=server,
            item_id=item_id,
            locations=locations,
            qualities=qualities,
        )

        payload = _http_get_json(
            url=url,
            timeout_s=timeout_s,
            user_agent=user_agent,
        )

        if not isinstance(payload, list):
            raise ApiReaderError(
                "Unexpected API response shape (expected list)",
                url=url,
                response_snippet=str(payload)[:300],
            )

        for record in payload:
            if not isinstance(record, dict):
                continue

            normalized = _normalize_price_record(
                record=record,
                server=server,
                url=url,
            )
            results.append(normalized)

    return results


# ----------------------------
# Internal helpers
# ----------------------------

def _validate_inputs(
    *,
    server: str,
    item_ids: Sequence[str],
    locations: Sequence[str],
    qualities: Sequence[int],
) -> None:
    if server not in BASE_URL_BY_SERVER:
        raise ValueError(f"Unknown server '{server}'")

    if not item_ids:
        raise ValueError("item_ids must not be empty")

    if not locations:
        raise ValueError("locations must not be empty")

    if not qualities:
        raise ValueError("qualities must not be empty")

    for q in qualities:
        if not isinstance(q, int) or q < 1 or q > 5:
            raise ValueError(f"Invalid quality '{q}' (expected int 1..5)")


def _build_prices_url(
    *,
    server: str,
    item_id: str,
    locations: Sequence[str],
    qualities: Sequence[int],
) -> str:
    base = BASE_URL_BY_SERVER[server]
    path = PRICES_ENDPOINT_FMT.format(item_id=item_id)

    query = {
        "locations": ",".join(locations),
        "qualities": ",".join(str(q) for q in qualities),
    }

    return f"{base}{path}?{urllib.parse.urlencode(query, safe=',')}"


def _http_get_json(
    *,
    url: str,
    timeout_s: float,
    user_agent: Optional[str],
) -> Any:
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")

    except urllib.error.HTTPError as e:
        snippet = e.read().decode("utf-8", errors="ignore")[:300]
        raise ApiReaderError(
            f"HTTP error {e.code}",
            url=url,
            status_code=e.code,
            response_snippet=snippet,
        )

    except Exception as e:
        raise ApiReaderError(
            f"Network error: {e}",
            url=url,
        )

    if status < 200 or status >= 300:
        raise ApiReaderError(
            f"Non-2xx HTTP status {status}",
            url=url,
            status_code=status,
            response_snippet=body[:300],
        )

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise ApiReaderError(
            "Failed to decode JSON",
            url=url,
            response_snippet=body[:300],
        )


def _normalize_price_record(
    *,
    record: Dict[str, Any],
    server: str,
    url: str,
) -> Dict[str, Any]:
    """
    1:1 mapping from Albion Data API record to api-item v1.
    No calculations, no interpretation.
    """

    return {
        "source": "api",
        "provider": "albion-data",
        "type": "price_snapshot",

        "server": server,

        "item_id": record.get("item_id"),
        "city": record.get("city"),
        "quality": record.get("quality"),

        "sell_price_min": record.get("sell_price_min"),
        "sell_price_min_date": record.get("sell_price_min_date"),
        "sell_price_max": record.get("sell_price_max"),
        "sell_price_max_date": record.get("sell_price_max_date"),

        "buy_price_min": record.get("buy_price_min"),
        "buy_price_min_date": record.get("buy_price_min_date"),
        "buy_price_max": record.get("buy_price_max"),
        "buy_price_max_date": record.get("buy_price_max_date"),

        "url": url,
    }


def _chunked(seq: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

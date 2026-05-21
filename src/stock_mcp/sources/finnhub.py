"""Finnhub adapter — real-time US stock quotes (free tier: 60 req/min).

Unlike Yahoo's delayed feed, Finnhub's /quote endpoint is genuinely
real-time on the free tier. Needs a free key (FINNHUB_API_KEY).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from ..config import load as load_config

_BASE = "https://finnhub.io/api/v1"
_TIMEOUT = 30


def _get(path: str, params: dict[str, str]) -> Any:
    cfg = load_config()
    if not cfg.finnhub_key:
        raise RuntimeError(
            "FINNHUB_API_KEY is not set on the MCP server. "
            "Get a free key at https://finnhub.io/register, set it in the "
            "environment file, and restart the service."
        )
    params = {**params, "token": cfg.finnhub_key}
    resp = requests.get(f"{_BASE}{path}", params=params, timeout=_TIMEOUT)
    if resp.status_code == 401:
        raise RuntimeError("Finnhub rejected the API key (401). Check FINNHUB_API_KEY.")
    if resp.status_code == 429:
        raise RuntimeError("Finnhub rate limit hit (429 — free tier is 60 req/min).")
    resp.raise_for_status()
    return resp.json()


def quote(symbol: str) -> dict[str, Any]:
    """Real-time quote for a US-listed symbol.

    Finnhub returns {c,d,dp,h,l,o,pc,t}; an unknown symbol comes back
    all-zero, which is mapped to a clear error.
    """
    raw = _get("/quote", {"symbol": symbol.upper()})
    if not raw.get("c") and not raw.get("pc"):
        raise RuntimeError(f"Finnhub returned no quote for '{symbol}' (unknown symbol?)")
    ts = raw.get("t")
    return {
        "symbol": symbol.upper(),
        "last_price": raw.get("c"),
        "change": raw.get("d"),
        "change_percent": raw.get("dp"),
        "day_high": raw.get("h"),
        "day_low": raw.get("l"),
        "open": raw.get("o"),
        "previous_close": raw.get("pc"),
        "quote_time": (
            datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None
        ),
    }

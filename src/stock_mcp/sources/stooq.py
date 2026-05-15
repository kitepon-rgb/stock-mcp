"""Stooq adapter — free daily OHLCV CSV.

Useful for Japanese stocks (e.g. '7203.jp' for Toyota) and global indices.
No API key required.
"""

from __future__ import annotations

import csv
import io
import os
from typing import Any

import requests

_BASE = "https://stooq.com/q/d/l/"
_TIMEOUT = 30


def history(symbol: str, interval: str = "d") -> list[dict[str, Any]]:
    """Fetch daily/weekly/monthly OHLCV history.

    Args:
        symbol: Stooq ticker (e.g. 'aapl.us', '7203.jp', '^spx', '^n225').
        interval: 'd' (daily), 'w' (weekly), 'm' (monthly), 'q', 'y'.
    """
    if interval not in {"d", "w", "m", "q", "y"}:
        raise ValueError("interval must be one of d, w, m, q, y")
    params: dict[str, str] = {"s": symbol, "i": interval}
    apikey = os.environ.get("STOOQ_API_KEY")
    if apikey:
        params["apikey"] = apikey
    resp = requests.get(_BASE, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    text = resp.text
    lowered = text.strip().lower()
    if "get your apikey" in lowered:
        raise RuntimeError(
            "Stooq now requires an API key. Set STOOQ_API_KEY in the server env "
            "(get one at https://stooq.com/q/d/?s=aapl.us&get_apikey)."
        )
    if lowered.startswith("no data"):
        raise RuntimeError(f"Stooq returned no data for '{symbol}'")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, Any]] = []
    for row in reader:
        out: dict[str, Any] = {"date": row.get("Date")}
        for k in ("Open", "High", "Low", "Close", "Volume"):
            v = row.get(k)
            try:
                out[k.lower()] = float(v) if v not in (None, "", "-") else None
            except ValueError:
                out[k.lower()] = None
        rows.append(out)
    return rows

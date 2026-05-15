"""Higher-level analytics that build on indicators and OHLCV history."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def detect_support_resistance(
    df: pd.DataFrame,
    window: int = 5,
    min_touches: int = 2,
    tolerance_pct: float = 1.0,
) -> dict[str, Any]:
    """Detect support and resistance levels from swing highs / lows.

    df: OHLCV DataFrame with columns 'high','low','close' (lowercase) sorted by time.
    window: distance parameter for find_peaks (bars between swings).
    min_touches: minimum number of swings clustering into the same level.
    tolerance_pct: percent-of-price tolerance for grouping swings into one level.
    """
    if df.empty:
        return {"supports": [], "resistances": []}

    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    last_price = float(df["close"].iloc[-1])

    peak_idx, _ = find_peaks(high, distance=window)
    trough_idx, _ = find_peaks(-low, distance=window)

    resistances = _cluster_levels(high[peak_idx], tolerance_pct, min_touches)
    supports = _cluster_levels(low[trough_idx], tolerance_pct, min_touches)

    return {
        "last_price": last_price,
        "supports": [s for s in supports if s["price"] <= last_price * 1.01],
        "resistances": [r for r in resistances if r["price"] >= last_price * 0.99],
        "all_supports": supports,
        "all_resistances": resistances,
    }


_FIB_RETRACE = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
_FIB_EXTEND = [1.272, 1.618, 2.0, 2.618]


def fibonacci_retracement(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    swing_high = float(df["high"].max())
    swing_low = float(df["low"].min())
    high_pos = df["high"].reset_index(drop=True).idxmax()
    low_pos = df["low"].reset_index(drop=True).idxmin()
    uptrend = high_pos > low_pos
    span = swing_high - swing_low
    levels: dict[str, float] = {}
    for r in _FIB_RETRACE:
        if uptrend:
            price = swing_high - span * r
        else:
            price = swing_low + span * r
        levels[f"{r*100:.1f}%"] = round(price, 4)
    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "trend": "uptrend" if uptrend else "downtrend",
        "levels": levels,
    }


def fibonacci_extension(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    swing_high = float(df["high"].max())
    swing_low = float(df["low"].min())
    span = swing_high - swing_low
    high_pos = df["high"].reset_index(drop=True).idxmax()
    low_pos = df["low"].reset_index(drop=True).idxmin()
    uptrend = high_pos > low_pos
    base = swing_high if uptrend else swing_low
    sign = 1 if uptrend else -1
    levels: dict[str, float] = {}
    for r in _FIB_EXTEND:
        price = base + sign * span * (r - 1)
        levels[f"{r*100:.1f}%"] = round(price, 4)
    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "trend": "uptrend" if uptrend else "downtrend",
        "levels": levels,
    }


def detect_chart_patterns(df: pd.DataFrame, window: int = 5, tolerance_pct: float = 2.0) -> list[dict[str, Any]]:
    """Heuristic chart-pattern detection: double top/bottom and triangles.

    Returns an empty list when no high-confidence pattern is found.
    """
    if df.empty or len(df) < 4 * window:
        return []
    out: list[dict[str, Any]] = []
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()

    peak_idx, _ = find_peaks(high, distance=window)
    trough_idx, _ = find_peaks(-low, distance=window)
    tol = tolerance_pct / 100.0

    if len(peak_idx) >= 2:
        p1, p2 = int(peak_idx[-2]), int(peak_idx[-1])
        h1, h2 = float(high[p1]), float(high[p2])
        if h1 > 0 and abs(h1 - h2) / h1 <= tol:
            mid_lows = low[p1:p2]
            if mid_lows.size:
                neckline = float(mid_lows.min())
                target = round(2 * neckline - max(h1, h2), 4)
                out.append({
                    "type": "double_top",
                    "confidence": 0.6,
                    "peak1_index": p1,
                    "peak2_index": p2,
                    "neckline": neckline,
                    "target_price": target,
                })

    if len(trough_idx) >= 2:
        t1, t2 = int(trough_idx[-2]), int(trough_idx[-1])
        l1, l2 = float(low[t1]), float(low[t2])
        if l1 > 0 and abs(l1 - l2) / l1 <= tol:
            mid_highs = high[t1:t2]
            if mid_highs.size:
                neckline = float(mid_highs.max())
                target = round(2 * neckline - min(l1, l2), 4)
                out.append({
                    "type": "double_bottom",
                    "confidence": 0.6,
                    "trough1_index": t1,
                    "trough2_index": t2,
                    "neckline": neckline,
                    "target_price": target,
                })

    if len(peak_idx) >= 3 and len(trough_idx) >= 3:
        peaks_seq = high[peak_idx[-3:]]
        troughs_seq = low[trough_idx[-3:]]
        peaks_desc = bool(peaks_seq[0] > peaks_seq[1] > peaks_seq[2])
        troughs_asc = bool(troughs_seq[0] < troughs_seq[1] < troughs_seq[2])
        peaks_flat = bool(abs(peaks_seq.max() - peaks_seq.min()) / peaks_seq.mean() <= tol)
        troughs_flat = bool(abs(troughs_seq.max() - troughs_seq.min()) / troughs_seq.mean() <= tol)
        if peaks_desc and troughs_asc:
            out.append({"type": "symmetric_triangle", "confidence": 0.5})
        elif peaks_flat and troughs_asc:
            out.append({"type": "ascending_triangle", "confidence": 0.5})
        elif peaks_desc and troughs_flat:
            out.append({"type": "descending_triangle", "confidence": 0.5})

    return out


def _cluster_levels(prices: np.ndarray, tolerance_pct: float, min_touches: int) -> list[dict[str, Any]]:
    if prices.size == 0:
        return []
    sorted_prices = np.sort(prices)
    tol = tolerance_pct / 100.0
    clusters: list[list[float]] = [[float(sorted_prices[0])]]
    for p in sorted_prices[1:]:
        ref = clusters[-1][0]
        if abs(p - ref) / ref <= tol:
            clusters[-1].append(float(p))
        else:
            clusters.append([float(p)])
    out: list[dict[str, Any]] = []
    for c in clusters:
        if len(c) < min_touches:
            continue
        out.append({
            "price": round(float(np.mean(c)), 4),
            "touches": len(c),
            "strength": len(c),
            "range_low": round(float(min(c)), 4),
            "range_high": round(float(max(c)), 4),
        })
    out.sort(key=lambda x: x["strength"], reverse=True)
    return out

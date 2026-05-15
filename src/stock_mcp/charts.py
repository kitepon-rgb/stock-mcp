"""Chart image generation: local (mplfinance) and remote (chart-img.com)."""

from __future__ import annotations

import base64
import io
import os
from typing import Any

import pandas as pd
import requests


def generate_local(
    df: pd.DataFrame,
    symbol: str,
    interval: str,
    period: str,
    indicators: list[str] | None = None,
) -> dict[str, Any]:
    """Render an OHLCV DataFrame to a candlestick PNG (base64-encoded) via mplfinance.

    df: OHLCV DataFrame indexed by datetime with lower-case columns.
    indicators: subset of ['ma20','ma50','ma200','bollinger','volume'].
    """
    import matplotlib  # noqa: F401  (mplfinance pulls this in)
    import mplfinance as mpf

    inds = set(indicators or ["ma20", "ma50", "ma200", "volume"])
    plot_df = df.rename(columns={
        "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume",
    })
    for c in ["Open", "High", "Low", "Close"]:
        if c not in plot_df.columns:
            raise ValueError(f"OHLCV DataFrame missing column: {c}")
    if "Volume" not in plot_df.columns:
        plot_df["Volume"] = 0

    addplots = []
    if "ma20" in inds and len(plot_df) > 20:
        addplots.append(mpf.make_addplot(plot_df["Close"].rolling(20).mean(), color="#2980b9", width=0.9))
    if "ma50" in inds and len(plot_df) > 50:
        addplots.append(mpf.make_addplot(plot_df["Close"].rolling(50).mean(), color="#27ae60", width=0.9))
    if "ma200" in inds and len(plot_df) > 200:
        addplots.append(mpf.make_addplot(plot_df["Close"].rolling(200).mean(), color="#c0392b", width=0.9))
    if "bollinger" in inds and len(plot_df) > 20:
        mid = plot_df["Close"].rolling(20).mean()
        std = plot_df["Close"].rolling(20).std(ddof=0)
        addplots.append(mpf.make_addplot(mid + 2 * std, color="#7f8c8d", width=0.7, linestyle="--"))
        addplots.append(mpf.make_addplot(mid - 2 * std, color="#7f8c8d", width=0.7, linestyle="--"))

    buf = io.BytesIO()
    title = f"{symbol}  ({interval} / {period})"
    mpf.plot(
        plot_df,
        type="candle",
        style="yahoo",
        title=title,
        ylabel="Price",
        volume=("volume" in inds),
        addplot=addplots if addplots else None,
        figsize=(12, 7),
        savefig=dict(fname=buf, format="png", dpi=110, bbox_inches="tight"),
    )
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return {
        "symbol": symbol,
        "interval_label": interval,
        "period_label": period,
        "image_base64": b64,
        "mime": "image/png",
    }


_CHART_IMG_URL = "https://api.chart-img.com/v2/tradingview/advanced-chart"


def generate_remote(
    symbol: str,
    interval: str = "1D",
    range_: str = "3M",
    studies: list[str] | None = None,
    theme: str = "light",
) -> dict[str, Any]:
    """Call chart-img.com advanced-chart API. Returns base64 PNG.

    Requires CHART_IMG_API_KEY env on the server.
    """
    key = os.environ.get("CHART_IMG_API_KEY")
    if not key:
        raise RuntimeError("CHART_IMG_API_KEY env var not set on the server")
    payload: dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "range": range_,
        "theme": theme,
        "width": 1200,
        "height": 700,
    }
    if studies:
        payload["studies"] = [{"name": s} for s in studies]
    r = requests.post(
        _CHART_IMG_URL,
        headers={"x-api-key": key, "content-type": "application/json"},
        json=payload,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"chart-img.com error {r.status_code}: {r.text[:300]}")
    b64 = base64.b64encode(r.content).decode("ascii")
    return {
        "symbol": symbol,
        "interval_label": interval,
        "period_label": range_,
        "image_base64": b64,
        "mime": "image/png",
    }

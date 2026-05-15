"""Alpha Vantage adapter (free tier — 25 req/day, 5/min on free key)."""

from __future__ import annotations

from typing import Any

import requests

from ..config import load as load_config

_BASE = "https://www.alphavantage.co/query"
_TIMEOUT = 30


def _get(params: dict[str, str]) -> dict[str, Any]:
    cfg = load_config()
    if not cfg.alpha_vantage_key:
        raise RuntimeError(
            "ALPHA_VANTAGE_API_KEY is not set on the MCP server. "
            "Set it in the environment file and restart the service."
        )
    params = {**params, "apikey": cfg.alpha_vantage_key}
    resp = requests.get(_BASE, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage rate limit: {data['Note']}")
    if "Information" in data and len(data) <= 1:
        raise RuntimeError(f"Alpha Vantage info: {data['Information']}")
    return data


def quote(symbol: str) -> dict[str, Any]:
    return _get({"function": "GLOBAL_QUOTE", "symbol": symbol})


def intraday(symbol: str, interval: str = "5min", outputsize: str = "compact") -> dict[str, Any]:
    if interval not in {"1min", "5min", "15min", "30min", "60min"}:
        raise ValueError("interval must be one of 1min,5min,15min,30min,60min")
    if outputsize not in {"compact", "full"}:
        raise ValueError("outputsize must be 'compact' or 'full'")
    return _get({
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
    })


def daily(symbol: str, outputsize: str = "compact") -> dict[str, Any]:
    if outputsize not in {"compact", "full"}:
        raise ValueError("outputsize must be 'compact' or 'full'")
    return _get({
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
    })


_INDICATOR_FUNCS = {
    "SMA", "EMA", "WMA", "DEMA", "TEMA", "TRIMA", "KAMA", "MAMA",
    "VWAP", "T3", "MACD", "MACDEXT", "STOCH", "STOCHF", "RSI",
    "STOCHRSI", "WILLR", "ADX", "ADXR", "APO", "PPO", "MOM", "BOP",
    "CCI", "CMO", "ROC", "ROCR", "AROON", "AROONOSC", "MFI", "TRIX",
    "ULTOSC", "DX", "MINUS_DI", "PLUS_DI", "MINUS_DM", "PLUS_DM",
    "BBANDS", "MIDPOINT", "MIDPRICE", "SAR", "TRANGE", "ATR", "NATR",
    "AD", "ADOSC", "OBV", "HT_TRENDLINE", "HT_SINE", "HT_TRENDMODE",
    "HT_DCPERIOD", "HT_DCPHASE", "HT_PHASOR",
}


def indicator(
    symbol: str,
    indicator: str,
    interval: str = "daily",
    time_period: int | None = 14,
    series_type: str = "close",
    extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    func = indicator.upper()
    if func not in _INDICATOR_FUNCS:
        raise ValueError(
            f"Unsupported indicator '{indicator}'. Some supported: "
            "SMA, EMA, RSI, MACD, BBANDS, ATR, ADX, STOCH, OBV, AROON, CCI."
        )
    params: dict[str, str] = {
        "function": func,
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
    }
    if time_period is not None:
        params["time_period"] = str(time_period)
    if extra:
        params.update(extra)
    return _get(params)

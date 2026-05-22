"""stock-mcp MCP server entrypoint.

Exposes market-data and technical-analysis tools over Streamable HTTP transport.
NO trade-execution tools are exposed.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal

import pandas as pd
from mcp.server.fastmcp import FastMCP

from . import analysis as ana
from . import charts as ch
from . import indicators as ind
from . import orders as ord_safety
from . import risk as rk
from .config import load as load_config
from .sources import alpha_vantage as av
from .sources import finnhub
from .sources import kabu
from .sources import marketspeed as ms2
from .sources import stooq
from .sources import yahoo

log = logging.getLogger("stock_mcp")


def _build_mcp() -> FastMCP:
    """Construct the FastMCP instance, enabling OAuth 2.1 when env vars are set.

    OAuth is enabled when BOTH ``MCP_OAUTH_ISSUER_URL`` and
    ``MCP_OAUTH_MASTER_PASSWORD`` are present (matches the ip-mcp pattern). When
    either is missing, the server runs without authentication (LAN-only mode).
    """
    issuer_url = os.environ.get("MCP_OAUTH_ISSUER_URL", "").strip()
    master_pw = os.environ.get("MCP_OAUTH_MASTER_PASSWORD", "").strip()
    db_path = os.environ.get("MCP_OAUTH_DB_PATH", "").strip() or "data/oauth.db"

    mcp_kwargs: dict[str, Any] = {}
    auth_provider = None
    if issuer_url and master_pw:
        from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions

        from .auth.provider import SqliteOAuthProvider

        consent_url = f"{issuer_url.rstrip('/')}/consent"
        auth_provider = SqliteOAuthProvider(
            master_password=master_pw,
            consent_url=consent_url,
            db_path=db_path,
        )
        auth_settings = AuthSettings(
            issuer_url=issuer_url,
            resource_server_url=issuer_url,
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )
        mcp_kwargs["auth_server_provider"] = auth_provider
        mcp_kwargs["auth"] = auth_settings
        log.info("OAuth 2.1 enabled, issuer=%s, db=%s", issuer_url, db_path)
    else:
        log.info(
            "OAuth disabled (set MCP_OAUTH_ISSUER_URL and MCP_OAUTH_MASTER_PASSWORD to enable). "
            "Running without authentication."
        )

    server = FastMCP(
        "stock-mcp",
        instructions=_INSTRUCTIONS,
        **mcp_kwargs,
    )

    if auth_provider is not None:
        from .auth.pages import make_consent_handlers

        consent_get, consent_post = make_consent_handlers(auth_provider)
        server.custom_route("/consent", methods=["GET"])(consent_get)
        server.custom_route("/consent", methods=["POST"])(consent_post)

    return server


_INSTRUCTIONS = """
# stock-mcp

Stock market data, local technical-analysis math, and Marketspeed2 (Rakuten
Securities) order execution. A deliberately lean tool set -- more tool code
exists in the server but is disabled via _DISABLED_TOOLS to keep context small.

## Market data
- yahoo_quote / yahoo_history -- Yahoo Finance quote and OHLCV history (global,
  free, no key). yahoo_history records always carry `interval` and `period` so
  the time axis cannot be misread.
- finnhub_quote -- real-time US stock quote; genuinely real-time, unlike
  Yahoo's ~15min-delayed feed (needs FINNHUB_API_KEY).

## Technical analysis (local math)
- calc_rsi / calc_moving_average / calc_bollinger_bands / calc_atr
- detect_support_resistance
- calc_fibonacci_retracement / calc_fibonacci_extension
- calc_volume_surge_realtime -- intraday volume-surge detection
- calc_position_sizing / calc_risk_reward -- position sizing and R:R math

## Marketspeed2 (Rakuten Securities, via the Windows bridge)
- Read-only: ms2_quote, ms2_board, ms2_margin, ms2_positions, ms2_orders,
  ms2_trades.
- Order execution -- two-step preview -> confirm, guarded by HMAC short-lived
  tokens and per-order quantity/notional limits. Always preview first:
    ms2_place_order_preview  -> ms2_place_order_confirm(confirm_token)
    ms2_modify_order_preview -> ms2_modify_order_confirm(confirm_token)
    ms2_cancel_order_preview -> ms2_cancel_order_confirm(confirm_token)
"""


mcp = _build_mcp()


# --- Context-reduction denylist ----------------------------------------------
# Tool names listed here are NOT registered with the MCP server, so their
# schemas never reach the client's context. The Python functions below still
# exist (and stay callable internally); only @mcp.tool registration is skipped.
# Edit this set and redeploy to change what is exposed.
_DISABLED_TOOLS = {
    "av_daily", "av_indicator", "av_intraday", "av_quote",
    "calc_dow_theory_phase", "calc_macd", "calc_option_greeks",
    "calc_portfolio_correlation", "calc_scenario_analysis",
    "calc_spread_compression", "calc_stochastic", "calc_value_at_risk",
    "detect_chart_patterns", "generate_chart_image", "generate_chart_local",
    "get_analyst_targets", "get_dividend_history", "get_earnings_calendar",
    "get_etf_holdings", "get_financial_statements", "get_fundamentals",
    "get_insider_transactions", "get_institutional_holders", "get_options_chain",
    "get_related_tickers", "get_sector_performance", "get_short_interest",
    "get_stock_history", "get_stock_news", "get_stock_price", "get_ticker_info",
    "kabu_board", "kabu_orders", "kabu_positions", "kabu_symbol_info",
    "search_ticker", "simulate_trade_outcome", "stooq_history",
    "yahoo_actions", "yahoo_financials", "yahoo_info", "yahoo_news",
    "analyze_ticker", "get_leveraged_etf_info",
}

_mcp_tool_decorator = mcp.tool


def _tool(*args, **kwargs):
    """mcp.tool wrapper: skip registration for names in _DISABLED_TOOLS."""
    decorator = _mcp_tool_decorator(*args, **kwargs)

    def register(fn):
        if fn.__name__ in _DISABLED_TOOLS:
            return fn
        return decorator(fn)

    return register


mcp.tool = _tool


# ---------- Yahoo Finance ----------

@mcp.tool(description="Yahoo Finance: latest quote snapshot (last price, prev close, day range, volume, market cap).")
def yahoo_quote(symbol: str) -> dict[str, Any]:
    return yahoo.quote(symbol)


@mcp.tool(description=(
    "Yahoo Finance: OHLCV history as JSON records. "
    "period in [1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max]; "
    "interval in [1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo] (intraday <=60 days)."
))
def yahoo_history(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    return yahoo.history(symbol, period=period, interval=interval)


@mcp.tool(description="Yahoo Finance: full company info dict (sector, industry, summary, ratios, etc.).")
def yahoo_info(symbol: str) -> dict[str, Any]:
    return yahoo.info(symbol)


@mcp.tool(description="Yahoo Finance: recent news stories for a ticker.")
def yahoo_news(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    return yahoo.news(symbol, limit=limit)


@mcp.tool(description="Yahoo Finance: dividend and split history.")
def yahoo_actions(symbol: str) -> str:
    return yahoo.actions(symbol)


@mcp.tool(description=(
    "Yahoo Finance: financial statement. "
    "statement in [income_stmt, quarterly_income_stmt, balance_sheet, "
    "quarterly_balance_sheet, cashflow, quarterly_cashflow]."
))
def yahoo_financials(symbol: str, statement: str) -> str:
    return yahoo.financials(symbol, statement)


# ---------- Alpha Vantage ----------

@mcp.tool(description="Alpha Vantage: global quote. Requires ALPHA_VANTAGE_API_KEY env on server.")
def av_quote(symbol: str) -> dict[str, Any]:
    return av.quote(symbol)


@mcp.tool(description=(
    "Alpha Vantage: intraday time series. "
    "interval in [1min,5min,15min,30min,60min]; outputsize in [compact,full]."
))
def av_intraday(symbol: str, interval: str = "5min", outputsize: str = "compact") -> dict[str, Any]:
    return av.intraday(symbol, interval=interval, outputsize=outputsize)


@mcp.tool(description="Alpha Vantage: daily adjusted time series. outputsize in [compact,full].")
def av_daily(symbol: str, outputsize: str = "compact") -> dict[str, Any]:
    return av.daily(symbol, outputsize=outputsize)


@mcp.tool(description=(
    "Alpha Vantage: technical indicator. "
    "Common indicator names: SMA, EMA, RSI, MACD, BBANDS, ATR, ADX, STOCH, OBV, AROON, CCI, MFI. "
    "interval in [1min,5min,15min,30min,60min,daily,weekly,monthly]. "
    "extra: dict of additional indicator-specific params (e.g. {'fastperiod':'12'} for MACD)."
))
def av_indicator(
    symbol: str,
    indicator: str,
    interval: str = "daily",
    time_period: int = 14,
    series_type: str = "close",
    extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    return av.indicator(
        symbol,
        indicator=indicator,
        interval=interval,
        time_period=time_period,
        series_type=series_type,
        extra=extra,
    )


# ---------- Finnhub ----------

@mcp.tool(description=(
    "Finnhub: real-time quote for a US-listed symbol — current price, change, "
    "percent change, day high/low, open, previous close, and quote timestamp. "
    "Genuinely real-time on the free tier, unlike Yahoo's ~15min delayed feed. "
    "Requires FINNHUB_API_KEY env on the server."
))
def finnhub_quote(symbol: str) -> dict[str, Any]:
    return finnhub.quote(symbol)


# ---------- Stooq ----------

@mcp.tool(description=(
    "Stooq: free OHLCV history. "
    "Use suffixes like '.us' (US), '.jp' (Japan), '.de' (Germany). "
    "Indices use '^' prefix (e.g. '^spx','^n225','^djia'). "
    "interval in [d,w,m,q,y]."
))
def stooq_history(symbol: str, interval: str = "d") -> list[dict[str, Any]]:
    return stooq.history(symbol, interval=interval)


# ---------- kabu.com ----------

@mcp.tool(description=(
    "kabu.com Station API: board (quote + depth) snapshot for a JP listed symbol. "
    "exchange: 1=Tokyo (default), 3=Nagoya, 5=Fukuoka, 6=Sapporo. "
    "Requires KABU_BASE_URL and KABU_API_PASSWORD env on the MCP server, "
    "and kabu Station must be running and reachable from the server."
))
def kabu_board(symbol: str, exchange: int = 1) -> dict[str, Any]:
    return kabu.board(symbol, exchange=exchange)


@mcp.tool(description="kabu.com Station API: symbol master info (designations, lot size, etc.).")
def kabu_symbol_info(symbol: str, exchange: int = 1) -> dict[str, Any]:
    return kabu.symbol_info(symbol, exchange=exchange)


@mcp.tool(description=(
    "kabu.com Station API: current positions (read-only). "
    "product: 0=all, 1=cash, 2=margin, 3=futures, 4=options."
))
def kabu_positions(product: int | None = None) -> Any:
    return kabu.positions(product=product)


@mcp.tool(description=(
    "kabu.com Station API: list orders (read-only). "
    "product as above; state: 1=pending, 2=processing, 3=processed, 4=cancel/correct in-flight, 5=final."
))
def kabu_orders(product: int | None = None, state: int | None = None) -> Any:
    return kabu.orders(product=product, state=state)


# ---------- OHLCV helpers (shared by spec tools and analyze_ticker) ----------

_FetchSource = Literal["yahoo", "stooq"]


def _fetch_ohlcv(source: _FetchSource, symbol: str, period: str, interval: str) -> pd.DataFrame:
    if source == "yahoo":
        raw = yahoo.history(symbol, period=period, interval=interval)
        df = pd.DataFrame(json.loads(raw))
        if df.empty:
            return df
        df = df.rename(columns=str.lower)
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
    if source == "stooq":
        rows = stooq.history(symbol, interval="d" if interval.startswith("1d") else interval[:1])
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
    raise ValueError(f"Unknown source '{source}' (use 'yahoo' or 'stooq')")


# ---------- Spec-named Tier 1 tools (stock-mcp-spec.md §3.1) ----------
#
# These mirror the names in docs/stock-mcp-spec.md so Claude can call tools
# exactly as documented in the spec. They wrap the same Yahoo / Stooq / local
# indicator code paths as the lower-level `yahoo_*` / `analyze_ticker` tools.


@mcp.tool(description=(
    "Spec 3.1.1 get_stock_price: latest quote snapshot for a symbol. "
    "Returns last_price, change vs prev_close, day high/low, 52w high/low, volume, market_cap."
))
def get_stock_price(symbol: str) -> dict[str, Any]:
    q = yahoo.quote(symbol)
    last = q.get("last_price")
    prev = q.get("previous_close")
    change = (last - prev) if (last is not None and prev is not None) else None
    change_pct = (change / prev * 100) if (change is not None and prev) else None
    return {
        **q,
        "change": change,
        "change_percent": change_pct,
    }


@mcp.tool(description=(
    "Spec 3.1.2 get_stock_history (CORE): OHLCV history with EXPLICIT time-axis labels. "
    "Every record includes 'interval' and 'period' so Claude cannot misread the time axis. "
    "period in [1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max]; "
    "interval in [1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo] (intraday <=60 days)."
))
def get_stock_history(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
) -> dict[str, Any]:
    raw = yahoo.history(symbol, period=period, interval=interval)
    records = json.loads(raw)
    for r in records:
        r["interval"] = interval
        r["period"] = period
    return {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "count": len(records),
        "records": records,
    }


@mcp.tool(description=(
    "Spec 3.1.3 get_ticker_info: structured company profile "
    "(name, sector, industry, country, exchange, 52w range, beta, employees, business summary)."
))
def get_ticker_info(symbol: str) -> dict[str, Any]:
    i = yahoo.info(symbol) or {}
    return {
        "symbol": symbol,
        "name": i.get("longName") or i.get("shortName"),
        "sector": i.get("sector"),
        "industry": i.get("industry"),
        "country": i.get("country"),
        "exchange": i.get("exchange") or i.get("fullExchangeName"),
        "currency": i.get("currency"),
        "website": i.get("website"),
        "year_high": i.get("fiftyTwoWeekHigh"),
        "year_low": i.get("fiftyTwoWeekLow"),
        "beta": i.get("beta"),
        "employees": i.get("fullTimeEmployees"),
        "business_summary": i.get("longBusinessSummary"),
    }


@mcp.tool(description=(
    "Spec 3.1.4 search_ticker: search Yahoo Finance for symbols matching a company name or keyword."
))
def search_ticker(query: str, limit: int = 10) -> list[dict[str, Any]]:
    return yahoo.search(query, limit=limit)


def _fetch_close_hlc(
    symbol: str,
    source: str,
    period: str,
    interval: str,
) -> pd.DataFrame:
    if source not in ("yahoo", "stooq"):
        raise ValueError("source must be 'yahoo' or 'stooq'")
    return _fetch_ohlcv(source, symbol, period=period, interval=interval)


def _indicator_records(df: pd.DataFrame, lookback: int) -> list[dict[str, Any]]:
    df = df.reset_index().tail(lookback)
    return json.loads(df.to_json(orient="records", date_format="iso"))


@mcp.tool(description=(
    "Spec 3.1.5 calc_rsi: Relative Strength Index. "
    "period=14, interval=1d, lookback=60 (most recent N records returned). "
    "Each record includes overbought (>70) / oversold (<30) flags."
))
def calc_rsi(
    symbol: str,
    period: int = 14,
    interval: str = "1d",
    lookback: int = 60,
    source: str = "yahoo",
    history_period: str = "6mo",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "interval": interval, "records": []}
    df = df.copy()
    df["rsi"] = ind.rsi(df["close"], period=period)
    df["overbought"] = df["rsi"] > 70
    df["oversold"] = df["rsi"] < 30
    return {
        "symbol": symbol,
        "interval": interval,
        "period_param": period,
        "records": _indicator_records(df[["close", "rsi", "overbought", "oversold"]], lookback),
    }


@mcp.tool(description=(
    "Spec 3.1.6 calc_macd: Moving Average Convergence Divergence. "
    "fast=12, slow=26, signal=9. Each record: macd, signal, histogram, cross."
))
def calc_macd(
    symbol: str,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    interval: str = "1d",
    lookback: int = 60,
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "interval": interval, "records": []}
    m = ind.macd(df["close"], fast=fast, slow=slow, signal=signal)
    df = df.join(m)
    hist_sign = (df["hist"] > 0).astype(int)
    df["cross"] = hist_sign.diff().fillna(0).map({1: "golden", -1: "death", 0: None})
    return {
        "symbol": symbol,
        "interval": interval,
        "params": {"fast": fast, "slow": slow, "signal": signal},
        "records": _indicator_records(df[["close", "macd", "signal", "hist", "cross"]], lookback),
    }


@mcp.tool(description=(
    "Spec 3.1.7 calc_moving_average: SMA or EMA with multiple periods. "
    "type in ['sma','ema']. periods defaults to [20,50,200]. "
    "perfect_order is True when ma_short > ma_mid > ma_long (uptrend stack)."
))
def calc_moving_average(
    symbol: str,
    type: str = "sma",
    periods: list[int] | None = None,
    interval: str = "1d",
    lookback: int = 60,
    source: str = "yahoo",
    history_period: str = "2y",
) -> dict[str, Any]:
    if type not in ("sma", "ema"):
        raise ValueError("type must be 'sma' or 'ema'")
    ps = periods or [20, 50, 200]
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "interval": interval, "records": []}
    fn = ind.sma if type == "sma" else ind.ema
    cols = ["close"]
    for n in ps:
        col = f"ma_{n}"
        df[col] = fn(df["close"], int(n))
        cols.append(col)
    if len(ps) >= 2:
        ordered = sorted(ps)
        ma_cols = [f"ma_{n}" for n in ordered]
        po = df[ma_cols[0]] > df[ma_cols[1]]
        for prev_col, next_col in zip(ma_cols[1:-1], ma_cols[2:]):
            po &= df[prev_col] > df[next_col]
        df["perfect_order"] = po.fillna(False)
        cols.append("perfect_order")
    return {
        "symbol": symbol,
        "interval": interval,
        "type": type,
        "periods": ps,
        "records": _indicator_records(df[cols], lookback),
    }


@mcp.tool(description=(
    "Spec 3.1.8 calc_bollinger_bands: middle SMA + upper/lower bands. "
    "period=20, std_dev=2.0. Records include upper, middle, lower, percent_b, bandwidth."
))
def calc_bollinger_bands(
    symbol: str,
    period: int = 20,
    std_dev: float = 2.0,
    interval: str = "1d",
    lookback: int = 60,
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "interval": interval, "records": []}
    bb = ind.bollinger(df["close"], period=period, num_std=std_dev)
    df = df.join(bb)
    band_range = (df["upper"] - df["lower"]).replace(0, pd.NA)
    df["percent_b"] = (df["close"] - df["lower"]) / band_range
    df["bandwidth"] = (df["upper"] - df["lower"]) / df["middle"]
    return {
        "symbol": symbol,
        "interval": interval,
        "params": {"period": period, "std_dev": std_dev},
        "records": _indicator_records(
            df[["close", "upper", "middle", "lower", "percent_b", "bandwidth"]], lookback
        ),
    }


@mcp.tool(description=(
    "Spec 3.1.9 calc_atr: Average True Range volatility. "
    "Records: atr (absolute), atr_percent (as % of close)."
))
def calc_atr(
    symbol: str,
    period: int = 14,
    interval: str = "1d",
    lookback: int = 60,
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "interval": interval, "records": []}
    df["atr"] = ind.atr(df["high"], df["low"], df["close"], period=period)
    df["atr_percent"] = df["atr"] / df["close"] * 100
    return {
        "symbol": symbol,
        "interval": interval,
        "params": {"period": period},
        "records": _indicator_records(df[["close", "atr", "atr_percent"]], lookback),
    }


@mcp.tool(description=(
    "Spec 3.1.10 calc_stochastic: Stochastic oscillator (%K / %D). "
    "k_period=14, d_period=3, smooth_k=3."
))
def calc_stochastic(
    symbol: str,
    k_period: int = 14,
    d_period: int = 3,
    smooth_k: int = 3,
    interval: str = "1d",
    lookback: int = 60,
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "interval": interval, "records": []}
    s = ind.stochastic(df["high"], df["low"], df["close"], k_period=k_period, d_period=d_period, smooth_k=smooth_k)
    df = df.join(s)
    df["overbought"] = df["k"] > 80
    df["oversold"] = df["k"] < 20
    return {
        "symbol": symbol,
        "interval": interval,
        "params": {"k_period": k_period, "d_period": d_period, "smooth_k": smooth_k},
        "records": _indicator_records(df[["close", "k", "d", "overbought", "oversold"]], lookback),
    }


@mcp.tool(description=(
    "Spec 3.1.11 detect_support_resistance: pivot-based support/resistance levels. "
    "Detects swing highs/lows via scipy peaks then clusters nearby prices. "
    "min_touches: minimum swings clustering into one level. "
    "tolerance_pct: percent-of-price tolerance for clustering."
))
def detect_support_resistance(
    symbol: str,
    interval: str = "1d",
    lookback: int = 180,
    min_touches: int = 2,
    tolerance_pct: float = 1.0,
    window: int = 5,
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "supports": [], "resistances": []}
    df = df.tail(lookback)
    out = ana.detect_support_resistance(
        df, window=window, min_touches=min_touches, tolerance_pct=tolerance_pct
    )
    return {"symbol": symbol, "interval": interval, "lookback": lookback, **out}


@mcp.tool(description=(
    "Spec 3.1.12 get_fundamentals: structured fundamental ratios "
    "(P/E, PEG, EPS, dividend yield, market cap, revenue, debt/equity, ROE/ROA, margins)."
))
def get_fundamentals(symbol: str) -> dict[str, Any]:
    return yahoo.fundamentals(symbol)


@mcp.tool(description=(
    "Spec 3.1.13 get_analyst_targets: analyst price targets and consensus rating distribution."
))
def get_analyst_targets(symbol: str) -> dict[str, Any]:
    return yahoo.analyst_targets(symbol)


@mcp.tool(description=(
    "Spec 3.1.14 get_financial_statements: income / balance / cashflow statements. "
    "statement_type in ['income','balance','cashflow']. period in ['annual','quarterly']."
))
def get_financial_statements(
    symbol: str,
    statement_type: str = "income",
    period: str = "annual",
) -> dict[str, Any]:
    mapping = {
        ("income", "annual"): "income_stmt",
        ("income", "quarterly"): "quarterly_income_stmt",
        ("balance", "annual"): "balance_sheet",
        ("balance", "quarterly"): "quarterly_balance_sheet",
        ("cashflow", "annual"): "cashflow",
        ("cashflow", "quarterly"): "quarterly_cashflow",
    }
    key = (statement_type, period)
    if key not in mapping:
        raise ValueError(
            f"Invalid combination ({statement_type}, {period}). "
            "statement_type in ['income','balance','cashflow']; period in ['annual','quarterly']."
        )
    raw = yahoo.financials(symbol, mapping[key])
    return {
        "symbol": symbol,
        "statement_type": statement_type,
        "period": period,
        "data": json.loads(raw),
    }


# ---------- Local technical analysis (legacy composite) ----------


@mcp.tool(description=(
    "Pull OHLCV history from the chosen source and compute requested indicators locally. "
    "source: 'yahoo' (default) or 'stooq'. "
    "indicators: subset of ['sma','ema','rsi','macd','bollinger','atr','adx']. "
    "Returns a JSON record list with original OHLCV plus indicator columns. "
    "params override defaults: e.g. {'sma':[5,20],'ema':[12,26],'rsi':14,'bollinger':[20,2.0]}."
))
def analyze_ticker(
    symbol: str,
    source: str = "yahoo",
    period: str = "6mo",
    interval: str = "1d",
    indicators: list[str] | None = None,
    params: dict[str, Any] | None = None,
) -> str:
    if source not in ("yahoo", "stooq"):
        raise ValueError("source must be 'yahoo' or 'stooq'")
    inds = indicators or ["sma", "ema", "rsi", "macd", "bollinger", "atr", "adx"]
    p = params or {}
    df = _fetch_ohlcv(source, symbol, period=period, interval=interval)
    if df.empty:
        return "[]"
    close = df["close"]
    high = df["high"]
    low = df["low"]

    if "sma" in inds:
        for n in p.get("sma", [20, 50]):
            df[f"sma_{n}"] = ind.sma(close, int(n))
    if "ema" in inds:
        for n in p.get("ema", [12, 26]):
            df[f"ema_{n}"] = ind.ema(close, int(n))
    if "rsi" in inds:
        df["rsi"] = ind.rsi(close, period=int(p.get("rsi", 14)))
    if "macd" in inds:
        fast, slow, sig = p.get("macd", [12, 26, 9])
        m = ind.macd(close, fast=int(fast), slow=int(slow), signal=int(sig))
        df = df.join(m)
    if "bollinger" in inds:
        period_bb, std_bb = p.get("bollinger", [20, 2.0])
        bb = ind.bollinger(close, period=int(period_bb), num_std=float(std_bb))
        df = df.join(bb.rename(columns={"middle": "bb_mid", "upper": "bb_upper", "lower": "bb_lower"}))
    if "atr" in inds:
        df["atr"] = ind.atr(high, low, close, period=int(p.get("atr", 14)))
    if "adx" in inds:
        a = ind.adx(high, low, close, period=int(p.get("adx", 14)))
        df = df.join(a)

    df = df.reset_index()
    return df.to_json(orient="records", date_format="iso")


# ---------- Spec Tier 2: news, events, holders, charts ----------


@mcp.tool(description=(
    "Spec 3.2.1 get_stock_news: ticker-related news with sentiment classification (positive/negative/neutral). "
    "lookback_days currently has no Yahoo cutoff; returned items are already date-ordered by Yahoo."
))
def get_stock_news(symbol: str, limit: int = 10, lookback_days: int = 7) -> list[dict[str, Any]]:
    items = yahoo.news_structured(symbol, limit=limit)
    if lookback_days and items:
        cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=lookback_days)
        filtered = []
        for it in items:
            dt = it.get("datetime")
            if dt is None:
                filtered.append(it)
                continue
            try:
                ts = pd.to_datetime(dt, errors="coerce")
                if ts is None or pd.isna(ts):
                    filtered.append(it)
                    continue
                ts_naive = ts.tz_localize(None) if getattr(ts, "tzinfo", None) is not None else ts
                if ts_naive >= cutoff:
                    filtered.append(it)
            except Exception:
                filtered.append(it)
        return filtered
    return items


@mcp.tool(description=(
    "Spec 3.2.2 get_earnings_calendar: next earnings date, EPS estimate / actual, surprise %."
))
def get_earnings_calendar(symbol: str) -> dict[str, Any]:
    return yahoo.earnings_calendar(symbol)


@mcp.tool(description=(
    "Spec 3.2.3 get_institutional_holders: top institutional holders with shares, value, and percent of float."
))
def get_institutional_holders(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    return yahoo.institutional_holders(symbol, limit=limit)


@mcp.tool(description=(
    "Spec 3.2.4 get_insider_transactions: insider buys/sells in the last `lookback_days` days."
))
def get_insider_transactions(symbol: str, lookback_days: int = 90) -> list[dict[str, Any]]:
    return yahoo.insider_transactions(symbol, lookback_days=lookback_days)


@mcp.tool(description=(
    "Spec 3.2.5 generate_chart_image: TradingView-style chart via chart-img.com. "
    "Requires CHART_IMG_API_KEY env on the server. "
    "interval examples: 1m,5m,15m,1h,1D,1W,1M. range examples: 1D,5D,1M,3M,6M,1Y,5Y,ALL. "
    "studies: TradingView indicator names like 'RSI@tv-basicstudies'."
))
def generate_chart_image(
    symbol: str,
    interval: str = "1D",
    range_: str = "3M",
    studies: list[str] | None = None,
    theme: str = "light",
) -> dict[str, Any]:
    return ch.generate_remote(symbol, interval=interval, range_=range_, studies=studies, theme=theme)


@mcp.tool(description=(
    "Spec 3.2.6 generate_chart_local: candlestick PNG via mplfinance (no API key needed). "
    "indicators subset of ['ma20','ma50','ma200','bollinger','volume']. "
    "Returns image_base64 + explicit interval_label/period_label so Claude cannot misread the axis."
))
def generate_chart_local(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
    indicators: list[str] | None = None,
    source: str = "yahoo",
) -> dict[str, Any]:
    df = _fetch_ohlcv(source, symbol, period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No OHLCV data for {symbol} ({source}, {period}/{interval})")
    return ch.generate_local(df, symbol=symbol, interval=interval, period=period, indicators=indicators)


@mcp.tool(description=(
    "Spec 3.2.7 calc_fibonacci_retracement: standard Fibonacci retracement levels "
    "(0, 23.6, 38.2, 50, 61.8, 78.6, 100) based on detected swing high/low."
))
def calc_fibonacci_retracement(
    symbol: str,
    lookback: int = 180,
    interval: str = "1d",
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol}
    return {"symbol": symbol, "interval": interval, "lookback": lookback, **ana.fibonacci_retracement(df.tail(lookback))}


@mcp.tool(description=(
    "Spec 3.2.8 calc_fibonacci_extension: extension levels (127.2, 161.8, 200, 261.8) "
    "projected above the swing high (uptrend) or below the swing low (downtrend)."
))
def calc_fibonacci_extension(
    symbol: str,
    lookback: int = 180,
    interval: str = "1d",
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol}
    return {"symbol": symbol, "interval": interval, "lookback": lookback, **ana.fibonacci_extension(df.tail(lookback))}


@mcp.tool(description=(
    "Spec 3.2.9 get_sector_performance: sector overview and top constituents (yfinance Sector). "
    "sector keys: technology, healthcare, energy, financial-services, consumer-cyclical, communication-services, "
    "industrials, utilities, real-estate, basic-materials, consumer-defensive."
))
def get_sector_performance(sector: str) -> dict[str, Any]:
    return yahoo.sector_performance(sector)


@mcp.tool(description=(
    "Spec 3.2.10 get_related_tickers: top sector-mates by market cap (used as a proxy for competitors)."
))
def get_related_tickers(symbol: str, count: int = 10) -> list[dict[str, Any]]:
    return yahoo.related_tickers(symbol, count=count)


@mcp.tool(description=(
    "Spec 3.2.11 get_etf_holdings: ETF top holdings, asset classes, and sector weightings (e.g. SOXX, SMH, QQQ)."
))
def get_etf_holdings(etf_symbol: str) -> dict[str, Any]:
    return yahoo.etf_holdings(etf_symbol)


@mcp.tool(description=(
    "Spec 3.2.12 get_leveraged_etf_info: leveraged-ETF metadata "
    "(inferred leverage factor, AUM, expense ratio, daily-reset note for volatility drag). "
    "Best-effort: leverage_factor is inferred from the fund name."
))
def get_leveraged_etf_info(etf_symbol: str) -> dict[str, Any]:
    return yahoo.leveraged_etf_info(etf_symbol)


# ---------- Spec Tier 3: options, short interest, dividends ----------


@mcp.tool(description=(
    "Spec 3.3.1 get_options_chain: option chain for a given expiration date (YYYY-MM-DD). "
    "If expiration is omitted, returns the list of available expirations only."
))
def get_options_chain(symbol: str, expiration: str | None = None) -> dict[str, Any]:
    if expiration is None:
        return {"symbol": symbol, "expirations": yahoo.options_expirations(symbol)}
    return yahoo.options_chain(symbol, expiration)


@mcp.tool(description=(
    "Spec 3.3.2 calc_option_greeks: Black-Scholes Greeks (delta, gamma, theta, vega, rho) and theoretical price. "
    "rate is annualized risk-free rate (e.g. 0.045 = 4.5%). volatility is annualized IV (e.g. 0.30 = 30%)."
))
def calc_option_greeks(
    spot: float,
    strike: float,
    days_to_expiration: int,
    option_type: str = "call",
    rate: float = 0.045,
    volatility: float = 0.30,
    dividend_yield: float = 0.0,
) -> dict[str, Any]:
    return rk.black_scholes_greeks(
        spot=spot,
        strike=strike,
        days_to_expiration=days_to_expiration,
        rate=rate,
        volatility=volatility,
        option_type=option_type,
        dividend_yield=dividend_yield,
    )


@mcp.tool(description=(
    "Spec 3.3.3 get_short_interest: short interest, days-to-cover, percent of float."
))
def get_short_interest(symbol: str) -> dict[str, Any]:
    return yahoo.short_interest(symbol)


@mcp.tool(description=(
    "Spec 3.3.4 get_dividend_history: ex-date dividend amounts over the last `lookback_years` years."
))
def get_dividend_history(symbol: str, lookback_years: int = 5) -> list[dict[str, Any]]:
    return yahoo.dividend_history(symbol, lookback_years=lookback_years)


# ---------- Spec Tier 4: pure-math strategy/risk tools ----------


@mcp.tool(description=(
    "Spec 3.4.1 calc_scenario_analysis: expected value, std dev, Sharpe proxy, Kelly fraction "
    "for a set of (name, probability, target_price) scenarios. Probabilities must sum to 1.0."
))
def calc_scenario_analysis(current_price: float, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return rk.scenario_analysis(current_price, scenarios)


@mcp.tool(description=(
    "Spec 3.4.2 calc_position_sizing: recommended share count for fixed-risk-per-trade "
    "(risk_per_trade_percent of account_size between entry and stop_loss)."
))
def calc_position_sizing(
    account_size: float,
    risk_per_trade_percent: float,
    entry: float,
    stop_loss: float,
) -> dict[str, Any]:
    return rk.position_sizing(account_size, risk_per_trade_percent, entry, stop_loss)


@mcp.tool(description=(
    "Spec 3.4.3 calc_risk_reward: risk-reward ratio and break-even win rate for one or more targets."
))
def calc_risk_reward(entry: float, stop_loss: float, targets: list[float]) -> dict[str, Any]:
    return rk.risk_reward(entry, stop_loss, targets)


@mcp.tool(description=(
    "Spec 3.4.4 calc_dow_theory_phase: rough 1/2/3-phase classifier (accumulation / markup / mania) "
    "using RSI proxy, volume surge, MA stack, and rate of change. "
    "media_heat is an OPTIONAL caller-supplied 0..1 score (e.g. how hot the stock is in the news)."
))
def calc_dow_theory_phase(
    symbol: str,
    lookback: str = "1y",
    interval: str = "1d",
    source: str = "yahoo",
    media_heat: float | None = None,
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, lookback, interval)
    if df.empty:
        return {"symbol": symbol, "phase": None, "confidence": 0.0, "reason": "no data"}
    out = rk.dow_theory_phase(df, media_heat=media_heat)
    return {"symbol": symbol, "interval": interval, "lookback": lookback, **out}


@mcp.tool(description=(
    "Spec 3.4.5 detect_chart_patterns: heuristic detection of double top / double bottom / triangle patterns."
))
def detect_chart_patterns(
    symbol: str,
    interval: str = "1d",
    lookback: int = 180,
    window: int = 5,
    tolerance_pct: float = 2.0,
    source: str = "yahoo",
    history_period: str = "1y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        return {"symbol": symbol, "patterns": []}
    patterns = ana.detect_chart_patterns(df.tail(lookback), window=window, tolerance_pct=tolerance_pct)
    return {"symbol": symbol, "interval": interval, "lookback": lookback, "patterns": patterns}


@mcp.tool(description=(
    "Spec 3.4.6 calc_portfolio_correlation: correlation matrix, average pairwise correlation, "
    "diversification score (1 - avg corr), and concentration HHI for a holdings list. "
    "holdings: [{symbol, weight}, ...]. "
    "history_period sets how far back daily returns are pulled (default 1y)."
))
def calc_portfolio_correlation(
    holdings: list[dict[str, Any]],
    history_period: str = "1y",
    interval: str = "1d",
    source: str = "yahoo",
) -> dict[str, Any]:
    symbols = [h["symbol"] for h in holdings]
    series: dict[str, pd.Series] = {}
    for sym in symbols:
        df = _fetch_close_hlc(sym, source, history_period, interval)
        if df.empty:
            continue
        series[sym] = df["close"].pct_change().rename(sym)
    if not series:
        raise ValueError("no price data available for any holding")
    returns_df = pd.concat(series.values(), axis=1)
    out = rk.portfolio_correlation(returns_df, holdings)
    out["history_period"] = history_period
    out["interval"] = interval
    return out


@mcp.tool(description=(
    "Spec 3.4.7 calc_value_at_risk: historical VaR and expected shortfall for a single symbol position. "
    "confidence default 0.95; time_horizon_days default 1 (uses sqrt-time scaling)."
))
def calc_value_at_risk(
    symbol: str,
    position_value: float,
    confidence: float = 0.95,
    time_horizon_days: int = 1,
    history_period: str = "1y",
    interval: str = "1d",
    source: str = "yahoo",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        raise ValueError(f"No history for {symbol}")
    returns = df["close"].pct_change().dropna()
    out = rk.value_at_risk(
        returns,
        confidence=confidence,
        time_horizon_days=time_horizon_days,
        position_value=position_value,
    )
    return {"symbol": symbol, **out}


@mcp.tool(description=(
    "Spec 3.4.8 simulate_trade_outcome: replay a trade against historical bars. "
    "entry_date / exit_date in YYYY-MM-DD. Reports PnL, max drawdown, max unrealized gain."
))
def simulate_trade_outcome(
    symbol: str,
    entry_date: str,
    exit_date: str,
    shares: float,
    interval: str = "1d",
    source: str = "yahoo",
    history_period: str = "5y",
) -> dict[str, Any]:
    df = _fetch_close_hlc(symbol, source, history_period, interval)
    if df.empty:
        raise ValueError(f"No history for {symbol}")
    out = rk.simulate_trade(df, entry_date, exit_date, shares)
    return {"symbol": symbol, "interval": interval, **out}


# ---------- Marketspeed2 (Rakuten Securities) via Windows bridge ----------
#
# All MS2 tools go through ``sources/marketspeed.py`` which is an HTTP client
# to a small FastAPI service running on the Windows host where Marketspeed2
# + Excel + RSS are installed (see ``tools/ms2-bridge/``).
#
# Read-only tools are always registered when MS2_BRIDGE_URL is set.
# Order-mutating tools require STOCK_MCP_ENABLE_ORDERS=true and follow the
# preview -> confirm two-step flow guarded by ``orders.py``.


@mcp.tool(description=(
    "Marketspeed2: latest quote snapshot for a JP listed symbol via the RSS "
    "bridge. Returns name/market/timestamp/last_price/previous_close/change*/"
    "open/high/low/best bid+ask (price&size)/volume/value/vwap/market_cap/"
    "lot_size/over+under qty/market buy+sell qty/base_price (当日基準値)/"
    "day_limit_upper/day_limit_lower (JPX 制限値幅 derived from base_price). "
    "exchange: 'T' (東証, default), 'JAX', 'JNX'."
))
def ms2_quote(symbol: str, exchange: str = "T") -> dict[str, Any]:
    out = ms2.quote(symbol, exchange=exchange)
    _enrich_with_price_band(out)
    return out


def _enrich_with_price_band(quote: dict[str, Any]) -> None:
    """Add day_limit_upper/lower derived from base_price (=当日基準値).

    Idempotent — leaves the dict unchanged if base_price is missing or
    non-positive (e.g. unsupported instrument, pre-market with no basis yet).
    """
    bp = quote.get("base_price")
    if not isinstance(bp, (int, float)) or bp <= 0:
        return
    from .jp_price_limits import band_for_basis_price
    band = band_for_basis_price(float(bp))
    quote["day_limit_upper"] = band.upper
    quote["day_limit_lower"] = band.lower
    quote["day_limit_half_width"] = band.half_width


def _validate_market_constraints(
    symbol: str,
    exchange: str,
    order_type: str,
    price: float | None,
    trigger_price: float | None,
    quantity: int,
) -> dict[str, Any] | None:
    """Pre-flight checks against the live quote: price-band + lot-size.

    Rejects the preview with ``OrderGuardError`` when:
      * limit/trigger price is outside the daily 値幅; or
      * quantity is not a positive multiple of the symbol's 単位株数
        (= かぶミニ regime, which MS2 RSS does NOT support — only
        iSPEED/web allow 1〜99 株).

    Returns a dict with ``price_band`` and ``lot_size`` for the preview to
    surface to the caller. Returns ``None`` when nothing could be fetched
    (off-hours, bridge down, unsupported instrument).
    """
    try:
        q = ms2.quote(symbol, exchange=exchange)
    except Exception as exc:
        log.warning("quote probe failed for %s: %s", symbol, exc)
        return None
    out: dict[str, Any] = {}
    # ----- lot-size check (kabu-mini guard) -----
    lot = q.get("lot_size")
    if isinstance(lot, (int, float)) and lot > 0:
        lot_int = int(lot)
        out["lot_size"] = lot_int
        if quantity < lot_int or quantity % lot_int != 0:
            raise ord_safety.OrderGuardError(
                f"quantity={quantity} is not a positive multiple of lot_size={lot_int} "
                f"for {symbol}. Rakuten Marketspeed2 RSS only accepts unit-multiple "
                f"orders; sub-unit (= かぶミニ / 単元未満株) trading is not exposed "
                f"through the RSS surface. To trade {quantity} share(s), use the "
                f"iSPEED app or PC web on rakuten-sec.co.jp directly."
            )
    # ----- price-band check -----
    candidates: list[tuple[str, float]] = []
    if price is not None and order_type in ("limit", "stop_limit"):
        candidates.append(("price", float(price)))
    if trigger_price is not None and order_type in ("stop", "stop_limit"):
        candidates.append(("trigger_price", float(trigger_price)))
    bp = q.get("base_price")
    if candidates and isinstance(bp, (int, float)) and bp > 0:
        from .jp_price_limits import band_for_basis_price
        band = band_for_basis_price(float(bp))
        for name, value in candidates:
            if value < band.lower or value > band.upper:
                raise ord_safety.OrderGuardError(
                    f"{name}={value:g} is outside the daily price band "
                    f"({band.lower:g}-{band.upper:g}; basis={band.basis_price:g}, "
                    f"±{band.half_width:g}). Rakuten would reject this. "
                    f"Adjust to within the band and retry."
                )
        out["price_band"] = {
            "basis_price": band.basis_price,
            "upper": band.upper,
            "lower": band.lower,
            "half_width": band.half_width,
        }
    return out or None


def _resolve_effective_tif(tif: str) -> tuple[str, str | None]:
    """Map our tif label to (Japanese 執行条件 label, effective expiry YYYY-MM-DD).

    Rakuten interprets:
      day  -> 本日中 — expires at today's close.
      gtc  -> 今週中 — expires at the upcoming Friday's close (or today if Friday).
    Other future tif values may be added when the upstream surface is extended.
    """
    import datetime as _dt
    today = _dt.date.today()
    if tif == "day":
        return "本日中", today.isoformat()
    if tif == "gtc":
        # weekday(): Mon=0 ... Fri=4 ... Sun=6
        days_to_friday = (4 - today.weekday()) % 7
        friday = today + _dt.timedelta(days=days_to_friday)
        return "今週中", friday.isoformat()
    return tif, None


@mcp.tool(description=(
    "Marketspeed2: full 10-level depth (板). Returns {bids, asks} each as "
    "[{level, price, size}, ...]."
))
def ms2_board(symbol: str, exchange: str = "T") -> dict[str, Any]:
    return ms2.board(symbol, exchange=exchange)


@mcp.tool(description=(
    "Marketspeed2: current 現物 holdings (RssPositionList). "
    "account filter: 'specific'|'general'|'nisa'|'old_nisa'|'all' (default)."
))
def ms2_positions(account: str | None = None) -> list[dict[str, Any]]:
    return ms2.positions(account=account)


@mcp.tool(description=(
    "Marketspeed2: 余力・保証金率 (RssCapacityList). Returns cash_buying_power, "
    "margin_room, margin_buying_power, margin_ratio_new, and 自動振替 variants. "
    "Margin fields are '-' string if 信用 account is not open."
))
def ms2_margin(account: str | None = None) -> dict[str, Any]:
    return ms2.margin(account=account)


@mcp.tool(description=(
    "Marketspeed2: 注文一覧 (RssOrderList). "
    "status filter: 'all'|'active'|'waiting'|'executing'|'partial'|'filled'|"
    "'cancelled'|'rejected' or the raw RSS code 0-13. "
    "account filter: 'specific'|'general'|'nisa'|'old_nisa'|'all' (default)."
))
def ms2_orders(account: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    return ms2.orders(account=account, status=status)


@mcp.tool(description=(
    "Marketspeed2: 約定一覧 (RssExecutionList). "
    "from_date / to_date in YYYY-MM-DD filter by 約定日 client-side. "
    "account filter: 'specific'|'general'|'nisa'|'old_nisa'|'all' (default)."
))
def ms2_trades(
    account: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    return ms2.trades(account=account, from_date=from_date, to_date=to_date)


# --- realtime intraday signals ----------------------------------------------

def _spread_sampler(symbol: str, exchange: str) -> dict[str, Any] | None:
    """Sampler for the spread Stream: read top-of-book, compute spread."""
    try:
        b = ms2.board(symbol, exchange=exchange)
    except Exception as exc:
        log.warning("spread sampler: board(%s/%s) failed: %s", symbol, exchange, exc)
        return None
    bids = b.get("bids") or []
    asks = b.get("asks") or []
    if not bids or not asks:
        return None
    best_bid = bids[0].get("price") if isinstance(bids[0], dict) else None
    best_ask = asks[0].get("price") if isinstance(asks[0], dict) else None
    if not isinstance(best_bid, (int, float)) or not isinstance(best_ask, (int, float)):
        return None
    return {
        "best_bid": float(best_bid),
        "best_ask": float(best_ask),
        "spread": float(best_ask) - float(best_bid),
    }


from .realtime_state import Stream as _Stream  # noqa: E402

_SPREAD_STREAM = _Stream(
    "spread",
    sampler=_spread_sampler,
    poll_interval_seconds=30.0,
    window_seconds=900.0,     # keep up to 15 min in the deque
    max_samples=120,
    idle_ttl_seconds=600.0,
    max_subscriptions=20,
)


def _classify_compression(ratio: float) -> str:
    if ratio >= 0.8:
        return "none"
    if ratio >= 0.5:
        return "watch"
    if ratio >= 0.3:
        return "warning"
    return "critical"


@mcp.tool(description=(
    "Detect spread compression (board narrowing) for a JP listed symbol via the "
    "MS2 RSS bridge. Subscribes the symbol to a background poller (30s interval, "
    "max 20 symbols, 10 min idle TTL) and returns whatever history is in the "
    "rolling window plus a compression_ratio = current_spread / avg_spread_lookback. "
    "First call: warming_up=true. Meaningful results after ~5 min. "
    "lookback_minutes: window over which the average is taken (default 5)."
))
def calc_spread_compression(
    symbol: str,
    exchange: str = "T",
    lookback_minutes: int = 5,
) -> dict[str, Any]:
    import time as _time
    import datetime as _dt
    sub = _SPREAD_STREAM.touch(symbol, exchange)
    # Always take a synchronous sample so the user gets a fresh reading on
    # every call rather than waiting for the poller's next 30s tick.
    _SPREAD_STREAM.force_sample_now(symbol, exchange)
    samples = _SPREAD_STREAM.snapshot(symbol, exchange)
    now = _time.time()
    cutoff = now - (lookback_minutes * 60)
    window = [s for s in samples if s.get("timestamp", 0) >= cutoff]

    def _iso(ts: float) -> str:
        return _dt.datetime.fromtimestamp(ts, _dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # warming_up: true until we have at least half the samples a full lookback
    # window can hold at the current poll cadence.
    target_samples = max(1, int(lookback_minutes * 60 / _SPREAD_STREAM.poll_interval))
    warming_threshold = max(1, target_samples // 2)
    samples_collected = len(window)

    out: dict[str, Any] = {
        "symbol": symbol,
        "exchange": exchange,
        "lookback_minutes": lookback_minutes,
        "samples_collected": samples_collected,
        "samples_needed_for_meaningful": warming_threshold,
        "target_samples_in_window": target_samples,
        "warming_up": samples_collected < warming_threshold,
        "subscribed": True,
        "subscription_expires_at": _iso(sub.last_touched + _SPREAD_STREAM.idle_ttl_seconds),
        "subscribed_symbols_count": len(_SPREAD_STREAM._subs),  # noqa: SLF001
        "max_subscriptions": _SPREAD_STREAM.max_subscriptions,
        "poll_interval_seconds": _SPREAD_STREAM.poll_interval,
        "spread_history": [
            {
                "timestamp": s["timestamp"],
                "iso_time": _iso(s["timestamp"]),
                "spread": s.get("spread"),
                "best_bid": s.get("best_bid"),
                "best_ask": s.get("best_ask"),
            }
            for s in window
        ],
    }
    if not window:
        out["ready_at"] = _iso(now + warming_threshold * _SPREAD_STREAM.poll_interval)
        out["note"] = (
            "First subscription. Background poller is running; call again every "
            f"{int(_SPREAD_STREAM.poll_interval)}s. Meaningful compression "
            f"baseline ready after ~{warming_threshold} samples."
        )
        return out
    current = window[-1].get("spread")
    spreads = [s.get("spread") for s in window if isinstance(s.get("spread"), (int, float))]
    avg = (sum(spreads) / len(spreads)) if spreads else None
    if isinstance(current, (int, float)) and isinstance(avg, (int, float)) and avg > 0:
        ratio = float(current) / float(avg)
        out["current_spread"] = float(current)
        out["average_spread"] = float(avg)
        out["compression_ratio"] = ratio
        out["compression_alert"] = _classify_compression(ratio)
    else:
        out["note"] = (
            f"Have {samples_collected} sample(s) but cannot compute ratio yet "
            "(zero or missing spread). Try again shortly."
        )
    if out["warming_up"]:
        out["ready_at"] = _iso(now + (warming_threshold - samples_collected) * _SPREAD_STREAM.poll_interval)
    return out


@mcp.tool(description=(
    "Realtime volume surge detector. Compares the live cumulative volume "
    "(or, with as_of_time, the cumulative volume at a past time-of-day) to "
    "what's typical at the same elapsed point across the trailing 20 trading "
    "days. Uses a U-shaped intraday profile (JP: 9:00-10:00=25%, 10:00-11:30=17%, "
    "12:30-13:30=13%, 13:30-14:30=17%, 14:30-15:00=28%; US: 9:30-10:30 ET=30%, "
    "10:30-15:00=35%, 15:00-16:00=35%). JP symbols use the MS2 bridge for live "
    "volume; US symbols use Yahoo. Alerts: <1.0=none / 1.0-1.5=watch / "
    "1.5-2.0=warning / 2.0+=critical. "
    "as_of_time: optional ISO 8601 in past (e.g. '2026-05-12T13:00:00-04:00' or "
    "'2026-05-12T13:00:00Z'). When set, uses minute-bar history to reproduce "
    "the cumulative volume at that moment instead of live."
))
def calc_volume_surge_realtime(symbol: str, as_of_time: str | None = None) -> dict[str, Any]:
    import datetime as _dt
    from . import intraday_volume_profile as ivp

    # ---- mode resolve ----
    now_utc = _dt.datetime.now(_dt.UTC)
    historical = False
    as_of_utc: _dt.datetime | None = None
    if as_of_time:
        historical = True
        try:
            parsed = _dt.datetime.fromisoformat(as_of_time.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=_dt.UTC)
            as_of_utc = parsed.astimezone(_dt.UTC)
        except ValueError:
            return {"symbol": symbol, "status": "bad_as_of_time",
                    "note": f"as_of_time '{as_of_time}' not parseable as ISO 8601."}

    session, elapsed = ivp.elapsed_session_minutes(symbol, now_utc=as_of_utc or now_utc)
    is_jp = ivp.is_jp_symbol(symbol)
    market = session.market

    def _market_closed_note() -> str:
        if market == "JP":
            return "Tokyo Stock Exchange is closed. Trading hours: 09:00-11:30 and 12:30-15:00 JST."
        return "US market is closed. Regular trading hours: 09:30-16:00 ET."

    if elapsed is None:
        return {
            "symbol": symbol, "market": market, "status": "in_break",
            "note": "Session is in a mid-day break (e.g. JP lunch). Try after break ends.",
        }
    total = ivp.total_session_minutes(session)
    cum_frac = ivp.cumulative_fraction(session, elapsed)

    # ---- current cumulative volume ----
    current_volume: float | None = None
    current_volume_source: str | None = None
    if not historical and is_jp:
        try:
            q = ms2.quote(symbol)
            v = q.get("volume")
            if isinstance(v, (int, float)) and v > 0:
                current_volume = float(v)
                current_volume_source = "ms2_quote"
        except Exception as exc:
            log.warning("surge: ms2.quote(%s) failed: %s", symbol, exc)

    import math
    import yfinance as yf
    yf_symbol = symbol if not is_jp or "." in symbol else f"{symbol}.T"
    historical_volume_source = "yfinance_daily_2mo"  # for the 20d baseline
    avg_full_day: float | None = None
    try:
        hist = yf.Ticker(yf_symbol).history(period="2mo", interval="1d")
        vols_clean = [
            float(v) for v in hist["Volume"].tolist()
            if isinstance(v, (int, float)) and not math.isnan(v) and v > 0
        ]
        if current_volume is None and vols_clean and not historical:
            current_volume = vols_clean[-1]
            current_volume_source = "yfinance_daily_latest"
        baseline = (
            vols_clean[:-1]
            if current_volume == (vols_clean[-1] if vols_clean else None) and not historical
            else vols_clean
        )
        if baseline:
            tail = baseline[-20:] if len(baseline) >= 20 else baseline
            avg_full_day = sum(tail) / len(tail)
    except Exception as exc:
        log.warning("surge: yfinance daily(%s) failed: %s", symbol, exc)

    # ---- historical mode: reconstruct cumulative-volume at as_of_time from 1m bars ----
    # yfinance caps 1m granularity to ~7 days of history; we ask for a 2-day
    # window centered on the target date (yesterday + today in market local).
    if historical and current_volume is None:
        try:
            local_tz = _dt.timezone(_dt.timedelta(minutes=session.tz_offset_minutes))
            as_of_local = as_of_utc.astimezone(local_tz)
            target_date = as_of_local.date()
            start = target_date - _dt.timedelta(days=1)
            end = target_date + _dt.timedelta(days=1)
            minute = yf.Ticker(yf_symbol).history(
                start=start.isoformat(), end=end.isoformat(), interval="1m"
            )
            if len(minute):
                idx_local = minute.index.tz_convert(local_tz)
                mask = [
                    (ts.date() == target_date and ts <= as_of_local)
                    for ts in idx_local
                ]
                day_bars = minute[mask]
                vol_to_asof = float(day_bars["Volume"].sum()) if len(day_bars) else 0.0
                if vol_to_asof > 0:
                    current_volume = vol_to_asof
                    current_volume_source = "yfinance_1m_cumsum_to_as_of_time"
        except Exception as exc:
            log.warning("surge: yfinance minute hist (%s, %s) failed: %s",
                        symbol, as_of_time, exc)

    if current_volume is None:
        return {
            "symbol": symbol,
            "market": market,
            "status": "no_volume",
            "as_of_time": as_of_time,
            "note": (_market_closed_note() if elapsed in (0, total) and not historical
                     else "Could not fetch a volume reading for this point in time."),
        }

    out: dict[str, Any] = {
        "symbol": symbol,
        "market": market,
        "as_of_time": as_of_time,
        "mode": "historical" if historical else "live",
        "current_volume": current_volume,
        "current_volume_source": current_volume_source,
        "elapsed_minutes": elapsed,
        "session_total_minutes": total,
        "elapsed_fraction": cum_frac,
        "average_full_day_volume_20d": avg_full_day,
        "historical_volume_source": historical_volume_source,
    }
    if avg_full_day and cum_frac > 0:
        expected_at_now = avg_full_day * cum_frac
        surge_now = current_volume / expected_at_now if expected_at_now > 0 else None
        est_full_day = current_volume / cum_frac
        surge_full = est_full_day / avg_full_day if avg_full_day > 0 else None
        out["expected_volume_at_this_time"] = expected_at_now
        out["current_surge_ratio"] = surge_now
        out["estimated_full_day_volume"] = est_full_day
        out["estimated_full_day_surge_ratio"] = surge_full
        primary = surge_now if surge_now is not None else surge_full
        if primary is not None:
            out["surge_alert"] = ivp.classify_alert(primary)
    elif cum_frac <= 0:
        out["note"] = _market_closed_note() + " (pre-open; elapsed_fraction=0)"
    else:
        out["note"] = "20-day average could not be computed (yfinance history empty)."
    return out


# --- order-mutating tools: registered only when STOCK_MCP_ENABLE_ORDERS=true ---

def _register_order_tools(server: FastMCP) -> None:
    """Attach the preview/confirm tools to ``server``.

    Called from ``_build_mcp`` when ``orders_enabled`` is True so that public
    OAuth installations without the flag never advertise these tools.
    """

    @server.tool(description=(
        "Marketspeed2 PREVIEW: validate a new-position order and return a "
        "confirm_token (60s TTL, single-use). Does NOT place the order. "
        "side='buy'|'sell'. order_type='limit'|'market'|'stop'|'stop_limit'. "
        "price required for limit/stop_limit; trigger_price required for stop/stop_limit. "
        "tif='day' (default) or 'gtc'. account_type='cash' (default) or 'margin'. "
        "Call ms2_place_order_confirm(confirm_token) within 60s to execute."
    ))
    def ms2_place_order_preview(
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "limit",
        price: float | None = None,
        trigger_price: float | None = None,
        tif: str = "day",
        account_type: str = "cash",
        exchange: str = "T",
    ) -> dict[str, Any]:
        cfg = load_config()
        ord_safety.check_orders_enabled(cfg)
        if side not in ("buy", "sell"):
            raise ord_safety.OrderGuardError("side must be 'buy' or 'sell'")
        if order_type not in ("limit", "market", "stop", "stop_limit"):
            raise ord_safety.OrderGuardError(
                "order_type must be 'limit','market','stop','stop_limit'"
            )
        if order_type in ("limit", "stop_limit") and price is None:
            raise ord_safety.OrderGuardError(f"price required for order_type='{order_type}'")
        if order_type in ("stop", "stop_limit") and trigger_price is None:
            raise ord_safety.OrderGuardError(f"trigger_price required for order_type='{order_type}'")
        if tif not in ("day", "gtc"):
            raise ord_safety.OrderGuardError("tif must be 'day' or 'gtc'")
        if account_type not in ("cash", "margin"):
            raise ord_safety.OrderGuardError("account_type must be 'cash' or 'margin'")
        ord_safety.check_quantity(cfg, quantity)
        notional = ord_safety.check_notional(cfg, quantity, price)
        constraints = _validate_market_constraints(
            symbol, exchange, order_type, price, trigger_price, int(quantity),
        )
        effective_tif, expiry_date = _resolve_effective_tif(tif)
        order = {
            "action": "place",
            "symbol": symbol,
            "exchange": exchange,
            "side": side,
            "quantity": int(quantity),
            "order_type": order_type,
            "price": price,
            "trigger_price": trigger_price,
            "tif": tif,
            "account_type": account_type,
        }
        token, exp_ts = ord_safety.issue_confirm_token(cfg, order)
        out: dict[str, Any] = {
            "preview": order,
            "estimated_notional": notional,
            "max_qty_guard": cfg.order_max_qty,
            "max_notional_guard": cfg.order_max_notional,
            "effective_tif": effective_tif,
            "expiry_date": expiry_date,
            "confirm_token": token,
            "expires_at": exp_ts,
            "ttl_seconds": cfg.confirm_token_ttl_seconds,
            "note": "Pass this confirm_token to ms2_place_order_confirm within the TTL.",
        }
        if constraints:
            if "price_band" in constraints:
                out["price_band"] = constraints["price_band"]
                out["price_band_note"] = (
                    "Derived from RSS '当日基準値' (= 前日終値 by default). MS2 desktop "
                    "may display a slightly wider band when it uses a PTS-shifted basis "
                    "(see docs/ms2-rss-reference/REFERENCE.md). Stay clear of the edges "
                    "by 1-2% to avoid borderline-edge rejections."
                )
            if "lot_size" in constraints:
                out["lot_size"] = constraints["lot_size"]
        return out

    @server.tool(description=(
        "Marketspeed2 CONFIRM: consume a confirm_token from ms2_place_order_preview "
        "and place the order on the broker. One-time use."
    ))
    def ms2_place_order_confirm(confirm_token: str) -> dict[str, Any]:
        cfg = load_config()
        ord_safety.check_orders_enabled(cfg)
        order = ord_safety.consume_confirm_token(cfg, confirm_token)
        if order.get("action") != "place":
            raise ord_safety.OrderGuardError(
                f"confirm_token is for action='{order.get('action')}', not 'place'"
            )
        return ms2.place_order(order)

    @server.tool(description=(
        "Marketspeed2 PREVIEW: validate a cancel and return a confirm_token. "
        "Call ms2_cancel_order_confirm(confirm_token) to actually cancel."
    ))
    def ms2_cancel_order_preview(order_id: str, account: str | None = None) -> dict[str, Any]:
        cfg = load_config()
        ord_safety.check_orders_enabled(cfg)
        order = {"action": "cancel", "order_id": order_id, "account": account}
        token, exp_ts = ord_safety.issue_confirm_token(cfg, order)
        return {
            "preview": order,
            "confirm_token": token,
            "expires_at": exp_ts,
            "ttl_seconds": cfg.confirm_token_ttl_seconds,
        }

    @server.tool(description=(
        "Marketspeed2 CONFIRM: consume a confirm_token from ms2_cancel_order_preview "
        "and cancel the order."
    ))
    def ms2_cancel_order_confirm(confirm_token: str) -> dict[str, Any]:
        cfg = load_config()
        ord_safety.check_orders_enabled(cfg)
        order = ord_safety.consume_confirm_token(cfg, confirm_token)
        if order.get("action") != "cancel":
            raise ord_safety.OrderGuardError(
                f"confirm_token is for action='{order.get('action')}', not 'cancel'"
            )
        return ms2.cancel_order(order["order_id"], account=order.get("account"))

    @server.tool(description=(
        "Marketspeed2 PREVIEW: validate an order modification (price/quantity) "
        "and return a confirm_token. Pass only the field(s) you want to change."
    ))
    def ms2_modify_order_preview(
        order_id: str,
        new_price: float | None = None,
        new_quantity: int | None = None,
        account: str | None = None,
    ) -> dict[str, Any]:
        cfg = load_config()
        ord_safety.check_orders_enabled(cfg)
        if new_price is None and new_quantity is None:
            raise ord_safety.OrderGuardError("supply at least one of new_price / new_quantity")
        if new_quantity is not None:
            ord_safety.check_quantity(cfg, new_quantity)
        notional = (
            ord_safety.check_notional(cfg, new_quantity, new_price)
            if new_quantity is not None and new_price is not None
            else None
        )
        order = {
            "action": "modify",
            "order_id": order_id,
            "new_price": new_price,
            "new_quantity": new_quantity,
            "account": account,
        }
        token, exp_ts = ord_safety.issue_confirm_token(cfg, order)
        return {
            "preview": order,
            "estimated_notional": notional,
            "confirm_token": token,
            "expires_at": exp_ts,
            "ttl_seconds": cfg.confirm_token_ttl_seconds,
        }

    @server.tool(description=(
        "Marketspeed2 CONFIRM: consume a confirm_token from ms2_modify_order_preview "
        "and apply the modification."
    ))
    def ms2_modify_order_confirm(confirm_token: str) -> dict[str, Any]:
        cfg = load_config()
        ord_safety.check_orders_enabled(cfg)
        order = ord_safety.consume_confirm_token(cfg, confirm_token)
        if order.get("action") != "modify":
            raise ord_safety.OrderGuardError(
                f"confirm_token is for action='{order.get('action')}', not 'modify'"
            )
        return ms2.modify_order(
            order["order_id"],
            new_price=order.get("new_price"),
            new_quantity=order.get("new_quantity"),
            account=order.get("account"),
        )


_cfg_at_import = load_config()
if _cfg_at_import.orders_enabled:
    _register_order_tools(mcp)
    log.info(
        "MS2 order tools registered (max_qty=%d, max_notional=%.0f, ttl=%ds).",
        _cfg_at_import.order_max_qty,
        _cfg_at_import.order_max_notional,
        _cfg_at_import.confirm_token_ttl_seconds,
    )
else:
    log.info("MS2 order tools NOT registered (STOCK_MCP_ENABLE_ORDERS != true).")


# ---------- entrypoint ----------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()
    log.info("Starting stock-mcp on http://%s:%s (Streamable HTTP)", cfg.host, cfg.port)
    mcp.settings.host = cfg.host
    mcp.settings.port = cfg.port
    # DNS-rebinding protection: the streamable-http transport rejects unknown Host
    # headers by default. When binding to LAN we must explicitly allow the LAN
    # host/origin via TransportSecuritySettings.
    from mcp.server.transport_security import TransportSecuritySettings

    extra_hosts = [h.strip() for h in os.environ.get("STOCK_MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
    extra_origins = [o.strip() for o in os.environ.get("STOCK_MCP_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    current = mcp.settings.transport_security
    if current is None:
        base_hosts: list[str] = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
        base_origins: list[str] = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
    elif isinstance(current, TransportSecuritySettings):
        base_hosts = list(current.allowed_hosts)
        base_origins = list(current.allowed_origins)
    else:
        base_hosts = list(current.get("allowed_hosts", []))
        base_origins = list(current.get("allowed_origins", []))
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list({*base_hosts, *extra_hosts}),
        allowed_origins=list({*base_origins, *extra_origins}),
    )
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

"""Yahoo Finance adapter via the yfinance library."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import yfinance as yf


VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
VALID_INTERVALS = {
    "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h",
    "1d", "5d", "1wk", "1mo", "3mo",
}


def _check_ticker(t: yf.Ticker, symbol: str) -> None:
    if t.isin is None:
        raise ValueError(f"Ticker '{symbol}' not found on Yahoo Finance")


def quote(symbol: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    fi = t.fast_info
    return {
        "symbol": symbol,
        "last_price": fi.get("lastPrice"),
        "previous_close": fi.get("previousClose"),
        "open": fi.get("open"),
        "day_high": fi.get("dayHigh"),
        "day_low": fi.get("dayLow"),
        "year_high": fi.get("yearHigh"),
        "year_low": fi.get("yearLow"),
        "volume": fi.get("lastVolume"),
        "market_cap": fi.get("marketCap"),
        "currency": fi.get("currency"),
        "exchange": fi.get("exchange"),
        "timezone": fi.get("timezone"),
    }


def history(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period '{period}'. Valid: {sorted(VALID_PERIODS)}")
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid interval '{interval}'. Valid: {sorted(VALID_INTERVALS)}")
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    df = df.reset_index(names="Date")
    return df.to_json(orient="records", date_format="iso")


def info(symbol: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    return dict(t.info)


def news(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    out: list[dict[str, Any]] = []
    for item in (t.news or [])[:limit]:
        c = item.get("content", {}) if isinstance(item, dict) else {}
        if c.get("contentType") != "STORY":
            continue
        out.append({
            "title": c.get("title"),
            "summary": c.get("summary"),
            "description": c.get("description"),
            "url": (c.get("canonicalUrl") or {}).get("url"),
            "pub_date": c.get("pubDate"),
        })
    return out


def actions(symbol: str) -> str:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    df = t.actions
    if df is None or df.empty:
        return "[]"
    df = df.reset_index(names="Date")
    return df.to_json(orient="records", date_format="iso")


_STATEMENT_ATTR = {
    "income_stmt": "income_stmt",
    "quarterly_income_stmt": "quarterly_income_stmt",
    "balance_sheet": "balance_sheet",
    "quarterly_balance_sheet": "quarterly_balance_sheet",
    "cashflow": "cashflow",
    "quarterly_cashflow": "quarterly_cashflow",
}


def financials(symbol: str, statement: str) -> str:
    attr = _STATEMENT_ATTR.get(statement)
    if attr is None:
        raise ValueError(f"Unknown statement '{statement}'. Valid: {list(_STATEMENT_ATTR)}")
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    df = getattr(t, attr)
    if df is None or df.empty:
        return "{}"
    return df.to_json(orient="columns", date_format="iso")


def search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    s = yf.Search(query, max_results=limit)
    out: list[dict[str, Any]] = []
    for q in (s.quotes or [])[:limit]:
        out.append({
            "symbol": q.get("symbol"),
            "name": q.get("shortname") or q.get("longname"),
            "exchange": q.get("exchange"),
            "type": q.get("quoteType"),
            "score": q.get("score"),
        })
    return out


def fundamentals(symbol: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    i = t.info or {}
    return {
        "symbol": symbol,
        "pe_ratio": i.get("trailingPE"),
        "forward_pe": i.get("forwardPE"),
        "peg": i.get("trailingPegRatio") or i.get("pegRatio"),
        "eps_ttm": i.get("trailingEps"),
        "eps_forward": i.get("forwardEps"),
        "dividend_yield": i.get("dividendYield"),
        "dividend_rate": i.get("dividendRate"),
        "market_cap": i.get("marketCap"),
        "enterprise_value": i.get("enterpriseValue"),
        "revenue_ttm": i.get("totalRevenue"),
        "net_income_ttm": i.get("netIncomeToCommon"),
        "ebitda": i.get("ebitda"),
        "debt_to_equity": i.get("debtToEquity"),
        "roe": i.get("returnOnEquity"),
        "roa": i.get("returnOnAssets"),
        "profit_margin": i.get("profitMargins"),
        "operating_margin": i.get("operatingMargins"),
        "current_ratio": i.get("currentRatio"),
        "quick_ratio": i.get("quickRatio"),
        "book_value": i.get("bookValue"),
        "price_to_book": i.get("priceToBook"),
        "beta": i.get("beta"),
    }


def analyst_targets(symbol: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    i = t.info or {}
    out: dict[str, Any] = {
        "symbol": symbol,
        "mean_target": i.get("targetMeanPrice"),
        "median_target": i.get("targetMedianPrice"),
        "high_target": i.get("targetHighPrice"),
        "low_target": i.get("targetLowPrice"),
        "num_analysts": i.get("numberOfAnalystOpinions"),
        "consensus_rating": i.get("recommendationKey"),
        "recommendation_mean": i.get("recommendationMean"),
        "current_price": i.get("currentPrice") or i.get("regularMarketPrice"),
    }
    try:
        rec = t.recommendations
        if rec is not None and not rec.empty:
            row = rec.iloc[0].to_dict()
            out["recommendation_distribution"] = {
                "strongBuy": int(row.get("strongBuy", 0) or 0),
                "buy": int(row.get("buy", 0) or 0),
                "hold": int(row.get("hold", 0) or 0),
                "sell": int(row.get("sell", 0) or 0),
                "strongSell": int(row.get("strongSell", 0) or 0),
                "period": str(row.get("period", "")),
            }
    except Exception:
        pass
    return out


def earnings_dates(symbol: str, limit: int = 8) -> str:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    df = None
    try:
        df = t.get_earnings_dates(limit=limit)
    except Exception:
        df = getattr(t, "earnings_dates", None)
    if df is None or df.empty:
        return "[]"
    df = df.reset_index(names="earnings_date")
    return df.to_json(orient="records", date_format="iso")


_POSITIVE_KW = {"beats", "beat", "surge", "rally", "upgrade", "outperform", "strong", "record", "soar", "boost", "raises", "gains"}
_NEGATIVE_KW = {"miss", "missed", "plunge", "downgrade", "underperform", "weak", "loss", "fraud", "lawsuit", "cut", "drops", "falls", "decline"}


def _sentiment_of(text: str) -> str:
    if not text:
        return "neutral"
    t = text.lower()
    pos = sum(1 for w in _POSITIVE_KW if w in t)
    neg = sum(1 for w in _NEGATIVE_KW if w in t)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def news_structured(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    out: list[dict[str, Any]] = []
    for item in (t.news or [])[:limit]:
        c = item.get("content", {}) if isinstance(item, dict) else {}
        if c.get("contentType") not in (None, "STORY"):
            continue
        title = c.get("title") or ""
        summary = c.get("summary") or c.get("description") or ""
        out.append({
            "title": title,
            "publisher": ((c.get("provider") or {}).get("displayName")) or item.get("publisher"),
            "datetime": c.get("pubDate") or item.get("providerPublishTime"),
            "url": (c.get("canonicalUrl") or {}).get("url") or item.get("link"),
            "summary": summary,
            "sentiment": _sentiment_of(f"{title} {summary}"),
        })
    return out


def earnings_calendar(symbol: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    out: dict[str, Any] = {"symbol": symbol}
    try:
        cal = t.calendar
        if isinstance(cal, dict):
            edates = cal.get("Earnings Date") or []
            if edates:
                first = edates[0]
                out["next_earnings_date"] = first.isoformat() if hasattr(first, "isoformat") else str(first)
            out["eps_estimate_average"] = cal.get("Earnings Average")
            out["eps_estimate_high"] = cal.get("Earnings High")
            out["eps_estimate_low"] = cal.get("Earnings Low")
            out["revenue_estimate_average"] = cal.get("Revenue Average")
            exd = cal.get("Ex-Dividend Date")
            out["ex_dividend_date"] = exd.isoformat() if hasattr(exd, "isoformat") else exd
    except Exception:
        pass
    try:
        df = t.get_earnings_dates(limit=8)
        if df is not None and not df.empty:
            df = df.reset_index(names="earnings_date")
            recent = df.to_dict(orient="records")
            for r in recent:
                ed = r.get("earnings_date")
                if hasattr(ed, "isoformat"):
                    r["earnings_date"] = ed.isoformat()
            out["history"] = recent
            last = next((r for r in recent if r.get("Reported EPS") is not None), None)
            if last is not None:
                out["last_eps_estimate"] = last.get("EPS Estimate")
                out["last_eps_actual"] = last.get("Reported EPS")
                out["last_surprise_percent"] = last.get("Surprise(%)")
    except Exception:
        pass
    return out


def institutional_holders(symbol: str, limit: int = 10) -> list[dict[str, Any]]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    df = t.institutional_holders
    if df is None or df.empty:
        return []
    df = df.head(limit)
    return json.loads(df.to_json(orient="records", date_format="iso"))


def insider_transactions(symbol: str, lookback_days: int = 90) -> list[dict[str, Any]]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    df = t.insider_transactions
    if df is None or df.empty:
        return []
    if "Start Date" in df.columns:
        cutoff = pd.Timestamp.utcnow().tz_localize(None).normalize() - pd.Timedelta(days=lookback_days)
        df = df[pd.to_datetime(df["Start Date"], errors="coerce") >= cutoff]
    return json.loads(df.to_json(orient="records", date_format="iso"))


def related_tickers(symbol: str, count: int = 10) -> list[dict[str, Any]]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    out: list[dict[str, Any]] = []
    info = t.info or {}
    sector = info.get("sector")
    industry = info.get("industry")
    try:
        if sector:
            sec = yf.Sector(sector.lower().replace(" ", "-"))
            top = sec.top_companies
            if top is not None and not top.empty:
                for sym, row in top.head(count + 1).iterrows():
                    if sym == symbol:
                        continue
                    out.append({
                        "symbol": sym,
                        "name": row.get("name"),
                        "market_cap": row.get("market cap"),
                        "sector": sector,
                        "industry": industry,
                    })
    except Exception:
        pass
    return out[:count]


def sector_performance(sector: str) -> dict[str, Any]:
    key = sector.lower().replace(" ", "-")
    sec = yf.Sector(key)
    out: dict[str, Any] = {"sector": sector}
    try:
        overview = sec.overview
        if isinstance(overview, dict):
            out["market_weight"] = overview.get("market_weight")
            out["market_cap"] = overview.get("market_cap")
            out["employee_count"] = overview.get("employee_count")
            out["companies_count"] = overview.get("companies_count")
    except Exception:
        pass
    try:
        top = sec.top_companies
        if top is not None and not top.empty:
            companies: list[dict[str, Any]] = []
            for sym, row in top.head(15).iterrows():
                companies.append({
                    "symbol": sym,
                    "name": row.get("name"),
                    "market_cap": row.get("market cap"),
                    "rating": row.get("rating"),
                })
            out["top_companies"] = companies
    except Exception:
        pass
    return out


def etf_holdings(etf_symbol: str) -> dict[str, Any]:
    t = yf.Ticker(etf_symbol)
    _check_ticker(t, etf_symbol)
    out: dict[str, Any] = {"symbol": etf_symbol}
    try:
        fd = t.funds_data
        if fd is None:
            return out
        try:
            top = fd.top_holdings
            if top is not None and not top.empty:
                holdings = []
                for sym, row in top.iterrows():
                    pct = row.get("Holding Percent")
                    if isinstance(pct, (int, float)):
                        pct = pct * 100
                    holdings.append({
                        "symbol": sym,
                        "name": row.get("Name") or row.get("Holding Name"),
                        "weight_percent": pct,
                    })
                out["top_holdings"] = holdings
        except Exception:
            pass
        try:
            out["asset_classes"] = fd.asset_classes
        except Exception:
            pass
        try:
            out["sector_weightings"] = fd.sector_weightings
        except Exception:
            pass
    except Exception:
        pass
    return out


def leveraged_etf_info(etf_symbol: str) -> dict[str, Any]:
    """Best-effort leveraged-ETF metadata (underlying / leverage / decay note)."""
    t = yf.Ticker(etf_symbol)
    _check_ticker(t, etf_symbol)
    i = t.info or {}
    name = (i.get("longName") or i.get("shortName") or "").lower()
    leverage = None
    for token, factor in (("3x", 3.0), ("2x", 2.0), ("ultra", 2.0)):
        if token in name:
            leverage = factor
            break
    direction = -1.0 if any(w in name for w in ("bear", "short", "inverse")) else 1.0
    if direction < 0 and leverage is None:
        leverage = 1.0
    return {
        "symbol": etf_symbol,
        "long_name": i.get("longName"),
        "leverage_factor": (direction * leverage) if leverage is not None else None,
        "reset_frequency": "daily",
        "expense_ratio": i.get("annualReportExpenseRatio") or i.get("netExpenseRatio"),
        "nav": i.get("navPrice"),
        "aum": i.get("totalAssets"),
        "ytd_return": i.get("ytdReturn"),
        "three_year_return": i.get("threeYearAverageReturn"),
        "category": i.get("category"),
        "summary": i.get("longBusinessSummary"),
        "note": "leverage_factor is inferred from the fund name. Daily-reset leveraged ETFs exhibit volatility drag in choppy markets.",
    }


def options_expirations(symbol: str) -> list[str]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    return list(t.options or [])


def options_chain(symbol: str, expiration: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    chain = t.option_chain(expiration)
    calls = json.loads(chain.calls.to_json(orient="records", date_format="iso"))
    puts = json.loads(chain.puts.to_json(orient="records", date_format="iso"))
    return {"symbol": symbol, "expiration": expiration, "calls": calls, "puts": puts}


def short_interest(symbol: str) -> dict[str, Any]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    i = t.info or {}
    float_shares = i.get("floatShares") or i.get("sharesOutstanding")
    shares_short = i.get("sharesShort")
    pct_float = None
    if float_shares and shares_short:
        pct_float = (shares_short / float_shares) * 100
    return {
        "symbol": symbol,
        "shares_short": shares_short,
        "shares_short_prior_month": i.get("sharesShortPriorMonth"),
        "short_ratio": i.get("shortRatio"),
        "short_percent_of_float": i.get("shortPercentOfFloat") or pct_float,
        "days_to_cover": i.get("shortRatio"),
        "float_shares": float_shares,
        "date_short_interest": i.get("dateShortInterest"),
    }


def dividend_history(symbol: str, lookback_years: int = 5) -> list[dict[str, Any]]:
    t = yf.Ticker(symbol)
    _check_ticker(t, symbol)
    s = t.dividends
    if s is None or s.empty:
        return []
    if getattr(s.index, "tz", None) is not None:
        s = s.tz_localize(None)
    cutoff = pd.Timestamp.utcnow().tz_localize(None).normalize() - pd.Timedelta(days=365 * lookback_years)
    s = s[s.index >= cutoff]
    return [
        {"ex_date": idx.isoformat(), "amount": float(v)}
        for idx, v in s.items()
    ]

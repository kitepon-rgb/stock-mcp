"""Tier 4 analytical tools: scenario / sizing / risk-reward / VaR / Dow theory / option Greeks."""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm


# ---------- Scenario analysis -------------------------------------------------


def scenario_analysis(current_price: float, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    """Expected value of a set of (name, probability, target_price) scenarios."""
    if not scenarios:
        raise ValueError("scenarios must be a non-empty list")
    probs = np.array([float(s["probability"]) for s in scenarios])
    if abs(probs.sum() - 1.0) > 0.01:
        raise ValueError(f"probabilities must sum to 1.0 (got {probs.sum():.3f})")
    targets = np.array([float(s["target_price"]) for s in scenarios])
    returns = (targets - current_price) / current_price
    expected_return = float((probs * returns).sum())
    variance = float((probs * (returns - expected_return) ** 2).sum())
    std_dev = math.sqrt(variance)
    max_gain = float(returns.max())
    max_loss = float(returns.min())
    sharpe_proxy = expected_return / std_dev if std_dev > 0 else None
    edge = expected_return
    odds = -max_loss
    kelly = (edge / (odds * odds)) if odds > 0 else None
    return {
        "current_price": current_price,
        "expected_return": expected_return,
        "expected_price": current_price * (1 + expected_return),
        "std_dev": std_dev,
        "max_gain": max_gain,
        "max_loss": max_loss,
        "sharpe_proxy": sharpe_proxy,
        "kelly_fraction": kelly,
        "scenarios": [
            {
                "name": s.get("name"),
                "probability": float(s["probability"]),
                "target_price": float(s["target_price"]),
                "return": float(returns[i]),
            }
            for i, s in enumerate(scenarios)
        ],
    }


# ---------- Position sizing ---------------------------------------------------


def position_sizing(
    account_size: float,
    risk_per_trade_percent: float,
    entry: float,
    stop_loss: float,
) -> dict[str, Any]:
    if entry <= 0 or account_size <= 0:
        raise ValueError("entry and account_size must be positive")
    risk_amount = account_size * (risk_per_trade_percent / 100.0)
    per_share_risk = abs(entry - stop_loss)
    if per_share_risk == 0:
        raise ValueError("entry equals stop_loss; per-share risk is zero")
    shares = math.floor(risk_amount / per_share_risk)
    position_value = shares * entry
    return {
        "recommended_shares": shares,
        "position_value": position_value,
        "risk_amount": risk_amount,
        "risk_percent_of_account": risk_per_trade_percent,
        "per_share_risk": per_share_risk,
        "position_percent_of_account": (position_value / account_size * 100) if account_size else 0.0,
    }


# ---------- Risk-reward -------------------------------------------------------


def risk_reward(entry: float, stop_loss: float, targets: list[float]) -> dict[str, Any]:
    risk = abs(entry - stop_loss)
    if risk == 0:
        raise ValueError("entry equals stop_loss; risk is zero")
    rrs = []
    for tgt in targets:
        reward = abs(tgt - entry)
        rr = reward / risk
        win_rate_required = 1.0 / (1.0 + rr)
        rrs.append({
            "target": tgt,
            "reward": reward,
            "rr_ratio": rr,
            "win_rate_required_breakeven": win_rate_required,
        })
    return {
        "entry": entry,
        "stop_loss": stop_loss,
        "risk": risk,
        "targets": rrs,
    }


# ---------- Portfolio correlation --------------------------------------------


def portfolio_correlation(returns_df: pd.DataFrame, holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """holdings: [{symbol, weight}, ...]; returns_df: DataFrame of daily returns per symbol."""
    corr = returns_df.corr()
    weights = {h["symbol"]: float(h["weight"]) for h in holdings}
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("total weight is zero")
    w = pd.Series(weights) / total_weight
    common = [s for s in w.index if s in corr.columns]
    if not common:
        raise ValueError("no overlap between holdings and returns data")
    w = w[common]
    sub_corr = corr.loc[common, common]
    if len(common) > 1:
        triu = sub_corr.values[np.triu_indices_from(sub_corr.values, k=1)]
        avg_corr = float(triu.mean())
    else:
        avg_corr = 0.0
    concentration_hhi = float((w ** 2).sum())
    return {
        "correlation_matrix": json.loads(sub_corr.to_json(orient="split")),
        "average_pairwise_correlation": avg_corr,
        "diversification_score": 1.0 - avg_corr,
        "concentration_hhi": concentration_hhi,
        "weights": w.to_dict(),
    }


# ---------- Value at Risk -----------------------------------------------------


def value_at_risk(
    returns: pd.Series,
    confidence: float = 0.95,
    time_horizon_days: int = 1,
    position_value: float = 1.0,
) -> dict[str, Any]:
    r = returns.dropna()
    if r.empty:
        raise ValueError("returns series is empty")
    mu = float(r.mean())
    sigma = float(r.std(ddof=1))
    z = norm.ppf(1 - confidence)
    var_pct = (mu + z * sigma) * math.sqrt(time_horizon_days)
    es_pct = (mu - sigma * norm.pdf(z) / (1 - confidence)) * math.sqrt(time_horizon_days)
    return {
        "confidence": confidence,
        "time_horizon_days": time_horizon_days,
        "var_percent": var_pct,
        "var_amount": position_value * abs(var_pct),
        "expected_shortfall_percent": es_pct,
        "expected_shortfall_amount": position_value * abs(es_pct),
        "sample_size": len(r),
        "mean_daily_return": mu,
        "std_daily_return": sigma,
    }


# ---------- Dow-theory phase classifier ---------------------------------------


def dow_theory_phase(df: pd.DataFrame, media_heat: float | None = None) -> dict[str, Any]:
    """Rough 1/2/3-phase classifier using RSI proxy, volume surge, MA stack, and rate of change.

    Phase 1 = accumulation, Phase 2 = markup, Phase 3 = distribution/mania.
    """
    if df.empty or len(df) < 60:
        return {"phase": None, "confidence": 0.0, "reason": "not enough data"}
    close = df["close"]
    volume = df.get("volume")
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(21).mean()
    loss = -delta.clip(upper=0).rolling(21).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi_dropped = rsi.dropna()
    rsi_latest = float(rsi_dropped.iloc[-1]) if not rsi_dropped.empty else float("nan")
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200_window = 200 if len(close) >= 200 else min(len(close), 100)
    ma200 = close.rolling(ma200_window).mean()
    perfect_order = bool(
        ma20.iloc[-1] > ma50.iloc[-1] > ma200.iloc[-1]
    ) if not (np.isnan(ma20.iloc[-1]) or np.isnan(ma50.iloc[-1]) or np.isnan(ma200.iloc[-1])) else False
    vol_surge = None
    if volume is not None and not volume.empty:
        recent_vol = float(volume.tail(20).mean())
        baseline_vol = float(volume.tail(120).mean()) if len(volume) >= 120 else float(volume.mean())
        vol_surge = (recent_vol / baseline_vol) if baseline_vol else None
    roc_60d = float((close.iloc[-1] / close.iloc[-60] - 1) * 100) if len(close) >= 60 else 0.0
    parabolic = roc_60d > 40

    matching: list[str] = []
    phase = 1
    confidence = 0.3
    if perfect_order:
        matching.append("ma_perfect_order")
        phase = 2
        confidence = 0.5
    if rsi_latest > 55:
        matching.append("rsi_rising")
        if phase < 2:
            phase = 2
        confidence += 0.1
    if vol_surge and vol_surge > 1.3:
        matching.append("volume_surge")
        confidence += 0.1
    if rsi_latest > 75 or parabolic:
        matching.append("euphoria_signal")
        phase = 3
        confidence = max(confidence, 0.6)
    if media_heat is not None and media_heat >= 0.7:
        matching.append("media_overheating")
        phase = 3
        confidence = max(confidence, 0.7)

    return {
        "phase": phase,
        "confidence": min(confidence, 1.0),
        "indicators_matching": matching,
        "rsi_21d": rsi_latest,
        "perfect_order": perfect_order,
        "volume_surge_ratio": vol_surge,
        "rate_of_change_60d_pct": roc_60d,
        "parabolic": parabolic,
    }


# ---------- Trade-outcome simulation ------------------------------------------


def simulate_trade(df: pd.DataFrame, entry_date: str, exit_date: str, shares: float) -> dict[str, Any]:
    if df.empty:
        raise ValueError("history DataFrame is empty")
    entry_ts = pd.Timestamp(entry_date)
    exit_ts = pd.Timestamp(exit_date)
    idx_tz = getattr(df.index, "tz", None)
    if idx_tz is not None:
        if entry_ts.tzinfo is None:
            entry_ts = entry_ts.tz_localize(idx_tz)
        if exit_ts.tzinfo is None:
            exit_ts = exit_ts.tz_localize(idx_tz)
    window = df.loc[(df.index >= entry_ts) & (df.index <= exit_ts)]
    if window.empty:
        raise ValueError("no bars in the given date range")
    entry_price = float(window["close"].iloc[0])
    exit_price = float(window["close"].iloc[-1])
    pnl = (exit_price - entry_price) * shares
    return_pct = (exit_price - entry_price) / entry_price * 100
    peak = window["high"].cummax()
    trough = window["low"].cummin()
    max_unrealized_gain = float((peak.max() - entry_price) * shares)
    max_drawdown = float((entry_price - trough.min()) * shares)
    return {
        "entry_date": entry_ts.isoformat(),
        "exit_date": exit_ts.isoformat(),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "shares": shares,
        "pnl": pnl,
        "actual_return_pct": return_pct,
        "max_unrealized_gain": max_unrealized_gain,
        "max_drawdown": max_drawdown,
        "bars_in_trade": int(len(window)),
    }


# ---------- Option Greeks (Black-Scholes) -------------------------------------


def black_scholes_greeks(
    spot: float,
    strike: float,
    days_to_expiration: int,
    rate: float = 0.045,
    volatility: float = 0.30,
    option_type: str = "call",
    dividend_yield: float = 0.0,
) -> dict[str, Any]:
    if days_to_expiration <= 0 or volatility <= 0:
        raise ValueError("days_to_expiration and volatility must be positive")
    T = days_to_expiration / 365.0
    sigma = volatility
    S = spot
    K = strike
    r = rate
    q = dividend_yield
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)
    pdf_d1 = norm.pdf(d1)
    if option_type == "call":
        price = S * math.exp(-q * T) * Nd1 - K * math.exp(-r * T) * Nd2
        delta = math.exp(-q * T) * Nd1
        theta = (
            -(S * pdf_d1 * sigma * math.exp(-q * T)) / (2 * math.sqrt(T))
            - r * K * math.exp(-r * T) * Nd2
            + q * S * math.exp(-q * T) * Nd1
        )
        rho = K * T * math.exp(-r * T) * Nd2
    elif option_type == "put":
        price = K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)
        delta = math.exp(-q * T) * (Nd1 - 1)
        theta = (
            -(S * pdf_d1 * sigma * math.exp(-q * T)) / (2 * math.sqrt(T))
            + r * K * math.exp(-r * T) * norm.cdf(-d2)
            - q * S * math.exp(-q * T) * norm.cdf(-d1)
        )
        rho = -K * T * math.exp(-r * T) * norm.cdf(-d2)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    gamma = math.exp(-q * T) * pdf_d1 / (S * sigma * math.sqrt(T))
    vega = S * math.exp(-q * T) * pdf_d1 * math.sqrt(T) / 100.0
    theta_per_day = theta / 365.0
    return {
        "option_type": option_type,
        "spot": S,
        "strike": K,
        "days_to_expiration": days_to_expiration,
        "rate": r,
        "implied_volatility": sigma,
        "dividend_yield": q,
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta_per_day,
        "rho": rho / 100.0,
    }

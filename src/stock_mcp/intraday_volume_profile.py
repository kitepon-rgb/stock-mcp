"""Intraday cumulative-volume profile for surge detection.

For each supported market session, we hold a piecewise-linear estimate of
"what fraction of a typical full-day volume has happened by minute X of the
session?". Given a current volume and elapsed minutes, this lets us answer:

  * expected_volume_at_this_time = full_day_volume * cum_pct(elapsed)
  * surge_ratio = current_volume / expected_volume_at_this_time
  * estimated_full_day_volume = current_volume / cum_pct(elapsed)
  * estimated_full_day_surge_ratio = estimated_full_day / avg_full_day_volume

These profiles are *rules of thumb* — every stock and session deviates. Good
enough for "is today wildly busier than normal?" alarms; don't use as a
precision instrument.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import NamedTuple


class _ProfileSegment(NamedTuple):
    # Cumulative fraction of full-day volume by the END of this segment.
    end_minute: int     # minutes since session open (lunch excluded)
    cum_fraction: float


# JP 東証: 9:00-11:30 前場 (150 min) + 12:30-15:00 後場 (150 min) = 300 min total session.
# Empirical bucket allocation per user request:
#   9:00-10:00 = 25% (0-60 min)
#   10:00-11:30 = 17% (60-150 min)
#   12:30-13:30 = 13% (150-210 min)
#   13:30-14:30 = 17% (210-270 min)
#   14:30-15:00 = 28% (270-300 min)
_JP_PROFILE = [
    _ProfileSegment(end_minute=60,  cum_fraction=0.25),
    _ProfileSegment(end_minute=150, cum_fraction=0.42),
    _ProfileSegment(end_minute=210, cum_fraction=0.55),
    _ProfileSegment(end_minute=270, cum_fraction=0.72),
    _ProfileSegment(end_minute=300, cum_fraction=1.00),
]

# US NYSE/NASDAQ regular session: 9:30-16:00 ET = 390 min.
# Empirical buckets per user request:
#   9:30-10:30 ET = 30% (0-60 min)
#   10:30-15:00 ET = 35% (60-330 min)
#   15:00-16:00 ET = 35% (330-390 min)
_US_PROFILE = [
    _ProfileSegment(end_minute=60,  cum_fraction=0.30),
    _ProfileSegment(end_minute=330, cum_fraction=0.65),
    _ProfileSegment(end_minute=390, cum_fraction=1.00),
]


@dataclass(frozen=True)
class _Session:
    market: str             # "JP" or "US"
    tz_offset_minutes: int  # vs UTC; JST=+540, ET (DST=EDT)=-240, ET (STD=EST)=-300
    open_h: int
    open_m: int
    close_h: int
    close_m: int
    lunch_open_h: int | None = None
    lunch_open_m: int | None = None
    lunch_close_h: int | None = None
    lunch_close_m: int | None = None
    profile: list[_ProfileSegment] = None  # type: ignore


_JP_SESSION = _Session(
    market="JP",
    tz_offset_minutes=540,
    open_h=9, open_m=0,
    close_h=15, close_m=0,
    lunch_open_h=11, lunch_open_m=30,
    lunch_close_h=12, lunch_close_m=30,
    profile=_JP_PROFILE,
)

# US: assume EDT (UTC-4). DST detection deferred until needed.
_US_SESSION_EDT = _Session(
    market="US",
    tz_offset_minutes=-240,
    open_h=9, open_m=30,
    close_h=16, close_m=0,
    profile=_US_PROFILE,
)


class SurgeAlert:
    NONE = "none"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


def classify_alert(surge_ratio: float) -> str:
    if surge_ratio < 1.0:
        return SurgeAlert.NONE
    if surge_ratio < 1.5:
        return SurgeAlert.WATCH
    if surge_ratio < 2.0:
        return SurgeAlert.WARNING
    return SurgeAlert.CRITICAL


def is_jp_symbol(symbol: str) -> bool:
    """Heuristic: starts with digit + 4 alphanumeric chars total.

    Accepts the legacy all-digit form (``7203``) AND the post-2024 JPX format
    that uses one letter in the 4th slot (``285A``, ``133A``). Optionally
    suffixed with ``.T``/``.JAX``/``.JNX``.
    """
    import re
    return bool(re.match(r"^[0-9][0-9A-Z]{3}(\.(T|JAX|JNX))?$", symbol))


def _now_session_local(session: _Session, now_utc: _dt.datetime | None = None) -> _dt.datetime:
    now_utc = now_utc or _dt.datetime.now(_dt.UTC)
    return now_utc + _dt.timedelta(minutes=session.tz_offset_minutes)


def elapsed_session_minutes(
    symbol: str,
    now_utc: _dt.datetime | None = None,
) -> tuple[_Session, int | None]:
    """How many session-minutes have elapsed since open for ``symbol``'s market.

    Returns (session, elapsed) where elapsed is:
      * 0 if pre-open
      * accumulated open-minutes (lunch break excluded for JP) up to "now"
      * full session length if post-close
      * None if "now" lands inside a session-internal break (lunch)
    """
    if is_jp_symbol(symbol):
        session = _JP_SESSION
    else:
        session = _US_SESSION_EDT
    local = _now_session_local(session, now_utc)
    return session, _elapsed_in_session(session, local)


def _elapsed_in_session(session: _Session, local_now: _dt.datetime) -> int | None:
    """Minutes since open, with intra-session breaks subtracted."""
    open_t = local_now.replace(hour=session.open_h, minute=session.open_m,
                               second=0, microsecond=0)
    close_t = local_now.replace(hour=session.close_h, minute=session.close_m,
                                second=0, microsecond=0)
    if local_now < open_t:
        return 0
    if local_now >= close_t:
        return int((close_t - open_t).total_seconds() / 60) - _lunch_minutes(session)
    if (session.lunch_open_h is not None and session.lunch_close_h is not None
            and session.lunch_open_m is not None and session.lunch_close_m is not None):
        lunch_open = local_now.replace(hour=session.lunch_open_h, minute=session.lunch_open_m,
                                       second=0, microsecond=0)
        lunch_close = local_now.replace(hour=session.lunch_close_h, minute=session.lunch_close_m,
                                        second=0, microsecond=0)
        if lunch_open <= local_now < lunch_close:
            return None
        if local_now >= lunch_close:
            return int(((lunch_open - open_t) + (local_now - lunch_close)).total_seconds() / 60)
    return int((local_now - open_t).total_seconds() / 60)


def _lunch_minutes(session: _Session) -> int:
    if session.lunch_open_h is None:
        return 0
    return (session.lunch_close_h - session.lunch_open_h) * 60 + (
        session.lunch_close_m - session.lunch_open_m  # type: ignore
    )


def cumulative_fraction(session: _Session, elapsed_minutes: int) -> float:
    """Linearly-interpolated cumulative-volume fraction at ``elapsed_minutes``."""
    if elapsed_minutes <= 0:
        return 0.0
    prev_end = 0
    prev_cum = 0.0
    for seg in session.profile:
        if elapsed_minutes <= seg.end_minute:
            span = seg.end_minute - prev_end
            if span <= 0:
                return seg.cum_fraction
            frac = (elapsed_minutes - prev_end) / span
            return prev_cum + frac * (seg.cum_fraction - prev_cum)
        prev_end = seg.end_minute
        prev_cum = seg.cum_fraction
    return 1.0


def total_session_minutes(session: _Session) -> int:
    """Tradable minutes in this session (lunch excluded)."""
    if not session.profile:
        return 0
    return session.profile[-1].end_minute

"""In-memory background poller for streaming-like signals.

Used by ``calc_spread_compression`` (and any future signal that wants a recent
history window over an external feed) to avoid forcing the user to drive a
``/loop`` themselves.

Design
------
* A symbol becomes "subscribed" the first time a tool consults it. Subscription
  carries a last-seen timestamp.
* A single daemon thread, started lazily, polls every 30s for every currently
  subscribed (symbol, exchange) pair. Each pair gets its own rolling deque of
  samples (up to ``max_samples`` covering ``window_seconds``).
* Subscriptions auto-expire after ``idle_ttl_seconds`` of no consumer touches
  to stop pestering external systems.
* ``max_subscriptions`` caps concurrent symbols; the oldest-touched gets evicted
  when a new symbol arrives.
* The poller is per-stream (each ``Stream`` instance manages one signal type);
  a stream supplies its own ``sampler`` callback so the store stays generic.

Thread model: the daemon thread is started by ``Stream.touch()`` if not yet
running. State mutations are protected by a per-stream ``RLock``. The store is
process-local; stock-mcp restart wipes everything (intentional — high-frequency
intraday signals shouldn't survive a deploy).
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

log = logging.getLogger(__name__)


@dataclass
class _Subscription:
    samples: deque
    last_touched: float
    last_polled: float = 0.0


class Stream:
    """One per signal type (e.g. one for spread, one for tick prints, ...).

    Parameters
    ----------
    name:
        Identifier used in logs.
    sampler:
        ``sampler(symbol, exchange) -> dict | None``. Called by the poller for
        each subscribed pair. Should return a JSON-friendly dict describing the
        snapshot (the dict is appended to the deque verbatim with a
        ``"timestamp"`` key added). Return ``None`` to skip this poll (e.g.
        market closed).
    poll_interval_seconds:
        How often the daemon thread wakes up to poll each subscription.
    window_seconds:
        Subscriptions retain samples newer than this; older samples drop off
        the rolling deque.
    max_samples:
        Hard cap on deque size as a defense against runaway memory.
    idle_ttl_seconds:
        A subscription that hasn't been touched for this long is dropped.
    max_subscriptions:
        Hard cap on concurrent symbols. When exceeded, the least-recently
        touched subscription is evicted to make room.
    """

    def __init__(
        self,
        name: str,
        sampler: Callable[[str, str], dict[str, Any] | None],
        *,
        poll_interval_seconds: float = 30.0,
        window_seconds: float = 600.0,
        max_samples: int = 200,
        idle_ttl_seconds: float = 600.0,
        max_subscriptions: int = 20,
    ) -> None:
        self.name = name
        self.sampler = sampler
        self.poll_interval = poll_interval_seconds
        self.window_seconds = window_seconds
        self.max_samples = max_samples
        self.idle_ttl_seconds = idle_ttl_seconds
        self.max_subscriptions = max_subscriptions
        self._subs: dict[tuple[str, str], _Subscription] = {}
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    # ---------- public API ----------

    def touch(self, symbol: str, exchange: str) -> _Subscription:
        """Mark a (symbol, exchange) as currently watched; start poller if idle.

        Returns the subscription's deque-bearing record. Callers can read
        ``record.samples`` after this returns; the very first touch always
        returns an empty deque (the first poll happens asynchronously).
        """
        key = (symbol, exchange)
        now = time.time()
        with self._lock:
            sub = self._subs.get(key)
            if sub is None:
                self._evict_if_full_locked()
                sub = _Subscription(
                    samples=deque(maxlen=self.max_samples),
                    last_touched=now,
                )
                self._subs[key] = sub
                log.info("stream %s: subscribed %s/%s (now %d subs)",
                         self.name, symbol, exchange, len(self._subs))
            else:
                sub.last_touched = now
        self._ensure_poller_running()
        return sub

    def snapshot(self, symbol: str, exchange: str) -> list[dict[str, Any]]:
        """Return a copy of the current rolling samples for the pair."""
        key = (symbol, exchange)
        with self._lock:
            sub = self._subs.get(key)
            if sub is None:
                return []
            return list(sub.samples)

    def force_sample_now(self, symbol: str, exchange: str) -> dict[str, Any] | None:
        """Run the sampler synchronously and append the result.

        Useful to immediately give the caller at least one fresh sample
        rather than the deque the poller will fill async.
        """
        sample = self._take_one_sample(symbol, exchange)
        if sample is None:
            return None
        key = (symbol, exchange)
        with self._lock:
            sub = self._subs.get(key)
            if sub is not None:
                sub.samples.append(sample)
                sub.last_polled = sample["timestamp"]
        return sample

    # ---------- internals ----------

    def _take_one_sample(self, symbol: str, exchange: str) -> dict[str, Any] | None:
        try:
            data = self.sampler(symbol, exchange)
        except Exception as exc:
            log.warning("stream %s: sampler error for %s/%s: %s",
                        self.name, symbol, exchange, exc)
            return None
        if data is None:
            return None
        data = dict(data)
        data["timestamp"] = time.time()
        return data

    def _ensure_poller_running(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            t = threading.Thread(target=self._poller_loop, name=f"stream-{self.name}", daemon=True)
            self._thread = t
            t.start()
            log.info("stream %s: poller started", self.name)

    def _poller_loop(self) -> None:
        while not self._stop.is_set():
            now = time.time()
            # Snapshot keys under lock, then poll outside to avoid holding the
            # lock during slow Excel-RTD round-trips.
            with self._lock:
                self._evict_idle_locked(now)
                pending = [
                    (key, sub) for key, sub in self._subs.items()
                    if now - sub.last_polled >= self.poll_interval
                ]
            for (symbol, exchange), _ in pending:
                if self._stop.is_set():
                    return
                sample = self._take_one_sample(symbol, exchange)
                if sample is None:
                    continue
                with self._lock:
                    sub = self._subs.get((symbol, exchange))
                    if sub is None:
                        continue
                    sub.samples.append(sample)
                    sub.last_polled = sample["timestamp"]
                    self._trim_window_locked(sub)
            # Sleep until the soonest next poll or 1 second, whichever is shorter.
            if self._stop.wait(timeout=1.0):
                return
            with self._lock:
                if not self._subs:
                    # No subscribers — go quiet (next touch will restart).
                    log.info("stream %s: no subs left, poller exiting", self.name)
                    self._thread = None
                    return

    def _trim_window_locked(self, sub: _Subscription) -> None:
        cutoff = time.time() - self.window_seconds
        while sub.samples and sub.samples[0].get("timestamp", 0) < cutoff:
            sub.samples.popleft()

    def _evict_idle_locked(self, now: float) -> None:
        stale = [
            k for k, s in self._subs.items()
            if now - s.last_touched > self.idle_ttl_seconds
        ]
        for k in stale:
            log.info("stream %s: idle-evicting %s", self.name, k)
            del self._subs[k]

    def _evict_if_full_locked(self) -> None:
        if len(self._subs) < self.max_subscriptions:
            return
        oldest_key = min(self._subs, key=lambda k: self._subs[k].last_touched)
        log.info("stream %s: LRU-evicting %s to make room", self.name, oldest_key)
        del self._subs[oldest_key]

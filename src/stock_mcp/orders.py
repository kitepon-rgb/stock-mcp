"""Order-execution safety layer.

Two-stage flow used by every order-mutating tool:

    *_preview(...)  -> returns the canonical order dict + a short-lived
                       `confirm_token` (HMAC-signed, single-use, default 60s TTL).
                       Guard checks (max qty / max notional / orders-enabled) run here.

    *_confirm(token) -> verifies signature, expiry, and not-yet-used; pops the
                        pending order; the caller then forwards it to the broker
                        bridge.

Guard knobs live in :class:`stock_mcp.config.Config`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

from .config import Config


class OrderGuardError(RuntimeError):
    """Raised when an order is rejected by the safety layer."""


@dataclass
class _PendingOrder:
    order: dict[str, Any]
    exp_ts: float


_pending: dict[str, _PendingOrder] = {}
_pending_lock = threading.Lock()


def _hmac(secret: str, message: bytes) -> bytes:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def check_orders_enabled(cfg: Config) -> None:
    if not cfg.orders_enabled:
        raise OrderGuardError(
            "Order tools are disabled on this server. "
            "Set STOCK_MCP_ENABLE_ORDERS=true and restart to enable."
        )


def check_quantity(cfg: Config, quantity: int) -> None:
    if quantity <= 0:
        raise OrderGuardError(f"quantity must be positive (got {quantity})")
    if quantity > cfg.order_max_qty:
        raise OrderGuardError(
            f"quantity {quantity} exceeds STOCK_MCP_MAX_ORDER_QTY={cfg.order_max_qty}"
        )


def check_notional(cfg: Config, quantity: int, price: float | None) -> float | None:
    """Estimate notional and reject if over the cap.

    Market orders pass ``price=None`` — no notional check is possible; only the
    qty guard applies and the caller is responsible for showing a reference
    price in the preview so the user can judge.
    """
    if price is None:
        return None
    notional = float(quantity) * float(price)
    if notional > cfg.order_max_notional:
        raise OrderGuardError(
            f"notional {notional:.0f} exceeds "
            f"STOCK_MCP_MAX_ORDER_NOTIONAL={cfg.order_max_notional:.0f}"
        )
    return notional


def issue_confirm_token(cfg: Config, order: dict[str, Any]) -> tuple[str, float]:
    """Store ``order`` under a fresh ID and return ``(confirm_token, exp_ts)``."""
    payload_id = secrets.token_urlsafe(16)
    exp_ts = time.time() + cfg.confirm_token_ttl_seconds
    sig = _hmac(cfg.confirm_token_secret, payload_id.encode("ascii"))
    token = f"{payload_id}.{_b64(sig)}"
    with _pending_lock:
        _pending[payload_id] = _PendingOrder(order=order, exp_ts=exp_ts)
        _gc_expired_locked()
    return token, exp_ts


def consume_confirm_token(cfg: Config, token: str) -> dict[str, Any]:
    """Verify ``token`` and pop the pending order. One-time use."""
    try:
        payload_id, sig_b64 = token.split(".", 1)
        sig = _unb64(sig_b64)
    except (ValueError, base64.binascii.Error) as exc:
        raise OrderGuardError("malformed confirm_token") from exc
    expected = _hmac(cfg.confirm_token_secret, payload_id.encode("ascii"))
    if not hmac.compare_digest(sig, expected):
        raise OrderGuardError("invalid confirm_token signature")
    now = time.time()
    with _pending_lock:
        entry = _pending.pop(payload_id, None)
        if entry is None:
            raise OrderGuardError("confirm_token expired, already used, or unknown")
        if entry.exp_ts < now:
            raise OrderGuardError("confirm_token expired")
    return entry.order


def _gc_expired_locked() -> None:
    now = time.time()
    stale = [k for k, v in _pending.items() if v.exp_ts < now]
    for k in stale:
        del _pending[k]


def canonical_order_json(order: dict[str, Any]) -> str:
    """Canonical JSON serialization for debug/logging. Sorted keys."""
    return json.dumps(order, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

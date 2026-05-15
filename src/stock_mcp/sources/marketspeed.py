"""Marketspeed2 (Rakuten Securities) adapter via a Windows-side HTTP bridge.

Marketspeed2 has no direct HTTP API; it speaks through the RSS Excel add-in.
We therefore run a small FastAPI service on the same Windows host where
Marketspeed2 + Excel + RSS are installed (see ``tools/ms2-bridge/``).

This module is a thin HTTP client to that bridge. The bridge handles all
Excel/COM details and exposes a stable JSON API.

Two trust boundaries:
  * stock-mcp <-> bridge: ``MS2_BRIDGE_TOKEN`` bearer (LAN-only).
  * bridge <-> Marketspeed2: in-process via Excel COM; never crosses the network.
"""

from __future__ import annotations

from typing import Any

import requests

from ..config import load as load_config

_READ_TIMEOUT = 20    # quote / board / lists — bridge polls Excel RTD up to ~10s
_ORDER_TIMEOUT = 60   # place / cancel / modify — bridge polls up to ~30s + buffer


class MarketspeedError(RuntimeError):
    """Raised when the MS2 bridge returns an error or is unreachable."""


def _client() -> tuple[str, dict[str, str]]:
    cfg = load_config()
    if not cfg.ms2_bridge_url:
        raise MarketspeedError(
            "Marketspeed2 bridge is not configured. "
            "Set MS2_BRIDGE_URL (and MS2_BRIDGE_TOKEN) on the MCP server."
        )
    if not cfg.ms2_bridge_token:
        raise MarketspeedError(
            "MS2_BRIDGE_TOKEN is not set. The bridge requires bearer auth."
        )
    headers = {
        "Authorization": f"Bearer {cfg.ms2_bridge_token}",
        "Accept": "application/json",
    }
    return cfg.ms2_bridge_url, headers


def _get(path: str, params: dict[str, Any] | None = None, timeout: float = _READ_TIMEOUT) -> Any:
    base, headers = _client()
    resp = requests.get(f"{base}{path}", params=params, headers=headers, timeout=timeout)
    return _handle(resp)


def _post(path: str, body: dict[str, Any], timeout: float = _READ_TIMEOUT) -> Any:
    base, headers = _client()
    try:
        resp = requests.post(f"{base}{path}", json=body, headers=headers, timeout=timeout)
    except requests.Timeout as exc:
        raise MarketspeedError(
            f"bridge timed out after {timeout}s on {path}. "
            "Likely cause: MS2 注文確認画面 is still set to 表示する — open MS2 → "
            "RSS toolbar → 各種設定 → RSS の設定 → 注文確認画面の表示 をオフ, "
            "and confirm 1回あたり発注上限金額 is set. Also check that the MS2 RSS "
            "toolbar shows 接続中 / 発注可."
        ) from exc
    return _handle(resp)


def _handle(resp: requests.Response) -> Any:
    try:
        data = resp.json()
    except ValueError:
        raise MarketspeedError(
            f"non-JSON response from bridge ({resp.status_code}): {resp.text[:200]}"
        )
    if resp.status_code >= 400:
        err = data.get("error") if isinstance(data, dict) else None
        raise MarketspeedError(f"bridge {resp.status_code}: {err or data}")
    return data


# ---------- read-only ----------

def quote(symbol: str, exchange: str = "T") -> dict[str, Any]:
    """Latest snapshot (last price, bid/ask, day range, volume)."""
    return _get("/quote", params={"symbol": symbol, "exchange": exchange})


def board(symbol: str, exchange: str = "T") -> dict[str, Any]:
    """Order book (depth) snapshot."""
    return _get("/board", params={"symbol": symbol, "exchange": exchange})


def positions(account: str | None = None) -> list[dict[str, Any]]:
    """Holdings for the given account (None = default account)."""
    params: dict[str, Any] = {}
    if account is not None:
        params["account"] = account
    out = _get("/positions", params=params)
    return out if isinstance(out, list) else out.get("positions", [])


def margin(account: str | None = None) -> dict[str, Any]:
    """Buying power / margin balances."""
    params: dict[str, Any] = {}
    if account is not None:
        params["account"] = account
    return _get("/margin", params=params)


def orders(account: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    """List orders (state filter optional). Read-only: lists, no placement."""
    params: dict[str, Any] = {}
    if account is not None:
        params["account"] = account
    if status is not None:
        params["status"] = status
    out = _get("/orders", params=params)
    return out if isinstance(out, list) else out.get("orders", [])


def trades(
    account: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    """Execution/fills history."""
    params: dict[str, Any] = {}
    if account is not None:
        params["account"] = account
    if from_date is not None:
        params["from"] = from_date
    if to_date is not None:
        params["to"] = to_date
    out = _get("/trades", params=params)
    return out if isinstance(out, list) else out.get("trades", [])


# ---------- mutating: forwarded by the *_confirm tools after token verify ----------

def place_order(order: dict[str, Any]) -> dict[str, Any]:
    """Forward an already-validated order to the bridge.

    ``order`` is the canonical dict produced by ``ms2_place_order_preview`` and
    returned from ``consume_confirm_token``.
    """
    return _post("/orders/place", order, timeout=_ORDER_TIMEOUT)


def cancel_order(order_id: str, account: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"order_id": order_id}
    if account is not None:
        body["account"] = account
    return _post("/orders/cancel", body, timeout=_ORDER_TIMEOUT)


def modify_order(
    order_id: str,
    new_price: float | None = None,
    new_quantity: int | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"order_id": order_id}
    if new_price is not None:
        body["new_price"] = new_price
    if new_quantity is not None:
        body["new_quantity"] = new_quantity
    if account is not None:
        body["account"] = account
    return _post("/orders/modify", body, timeout=_ORDER_TIMEOUT)

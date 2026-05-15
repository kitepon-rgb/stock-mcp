"""kabu.com (kabu Station API) adapter — READ ONLY.

The kabu Station REST API runs on the machine where kabu Station is installed.
Set KABU_BASE_URL (e.g. 'http://127.0.0.1:18080') and KABU_API_PASSWORD in env.
Set KABU_PRODUCTION=true for the real-trading port (18080 default) vs test (18081).

This adapter only exposes READ-ONLY tools:
  - board (board quote / depth snapshot)
  - positions
  - orders (list)
  - symbolinfo

Order submission tools are intentionally NOT exposed.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from ..config import load as load_config

_TIMEOUT = 15
_token_cache: dict[str, Any] = {"token": None, "ts": 0.0}
_TOKEN_TTL_SEC = 60 * 60  # kabu Station rotates daily; refresh hourly to be safe.


def _require_config() -> tuple[str, str]:
    cfg = load_config()
    if not cfg.kabu_base_url or not cfg.kabu_api_password:
        raise RuntimeError(
            "kabu.com is not configured. Set KABU_BASE_URL and KABU_API_PASSWORD "
            "in the MCP server environment."
        )
    return cfg.kabu_base_url.rstrip("/"), cfg.kabu_api_password


def _token() -> str:
    base, password = _require_config()
    now = time.time()
    if _token_cache["token"] and now - _token_cache["ts"] < _TOKEN_TTL_SEC:
        return _token_cache["token"]
    resp = requests.post(
        f"{base}/kabusapi/token",
        json={"APIPassword": password},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    tok = resp.json().get("Token")
    if not tok:
        raise RuntimeError(f"kabu token endpoint returned no token: {resp.text}")
    _token_cache["token"] = tok
    _token_cache["ts"] = now
    return tok


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    base, _ = _require_config()
    headers = {"X-API-KEY": _token()}
    resp = requests.get(f"{base}/kabusapi{path}", headers=headers, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def board(symbol: str, exchange: int = 1) -> dict[str, Any]:
    """Board (quote+depth) snapshot.

    exchange: 1=東証, 3=名証, 5=福証, 6=札証.
    """
    return _get(f"/board/{symbol}@{exchange}")


def symbol_info(symbol: str, exchange: int = 1) -> dict[str, Any]:
    return _get(f"/symbol/{symbol}@{exchange}")


def positions(product: int | None = None) -> Any:
    params = {}
    if product is not None:
        params["product"] = str(product)
    return _get("/positions", params=params or None)


def orders(product: int | None = None, state: int | None = None) -> Any:
    params: dict[str, str] = {}
    if product is not None:
        params["product"] = str(product)
    if state is not None:
        params["state"] = str(state)
    return _get("/orders", params=params or None)

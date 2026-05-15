"""Marketspeed2 (Rakuten Securities) HTTP bridge.

Runs on the Windows host where Marketspeed2 + Excel + RSS are installed.
stock-mcp talks to this service over LAN HTTP (bearer-token auth).

Endpoints
---------
GET  /healthz                       liveness probe
GET  /quote?symbol=...&exchange=T   latest snapshot
GET  /board?symbol=...&exchange=T   order-book depth
GET  /positions[?account=...]       holdings
GET  /margin[?account=...]          buying power
GET  /orders[?account=...&status=...]
GET  /trades[?account=...&from=YYYY-MM-DD&to=YYYY-MM-DD]
POST /orders/place                  place a new order   (needs MS2_BRIDGE_ENABLE_ORDERS=true)
POST /orders/cancel                 cancel an order     (needs MS2_BRIDGE_ENABLE_ORDERS=true)
POST /orders/modify                 modify an order     (needs MS2_BRIDGE_ENABLE_ORDERS=true)

Run
---
    python bridge.py
or
    uvicorn bridge:app --host 0.0.0.0 --port 39201

Environment variables (.env)
----------------------------
    MS2_BRIDGE_TOKEN            shared secret with stock-mcp (required)
    MS2_BRIDGE_HOST             bind address (default 0.0.0.0)
    MS2_BRIDGE_PORT             bind port    (default 39201)
    MS2_BRIDGE_ENABLE_ORDERS    'true' to allow mutating endpoints (default false)
    MS2_BRIDGE_DRY_RUN          'true' to skip real RSS order calls and return a stub (default false)
    MS2_WORKBOOK_PATH           absolute path to the Excel workbook hosting RSS

See README.md for Excel + RSS setup details.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import sys
import threading
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from rss import RssClient, RssError


_TOKEN = os.environ.get("MS2_BRIDGE_TOKEN", "").strip()
_HOST = os.environ.get("MS2_BRIDGE_HOST", "0.0.0.0")
_PORT = int(os.environ.get("MS2_BRIDGE_PORT", "39201"))
_ORDERS_ENABLED = os.environ.get("MS2_BRIDGE_ENABLE_ORDERS", "false").lower() == "true"
_DRY_RUN = os.environ.get("MS2_BRIDGE_DRY_RUN", "false").lower() == "true"
_WORKBOOK = os.environ.get("MS2_WORKBOOK_PATH", "").strip() or None

if not _TOKEN:
    print(
        "FATAL: MS2_BRIDGE_TOKEN is not set. Generate one with "
        "`python -c \"import secrets; print(secrets.token_urlsafe(32))\"` "
        "and put it in .env, then share the same value with the stock-mcp server.",
        file=sys.stderr,
    )
    sys.exit(2)


app = FastAPI(title="ms2-bridge", version="0.1.0")
_rss: RssClient | None = None


def _do_rss_connect() -> None:
    """MS2 リボンを接続済み・発注可にする内部処理（HTTP 不要）。"""
    try:
        rss = _get_rss()
        rss._ensure_workbook()
        state = _ms2_ribbon_state()
        buttons = state.get("buttons", [])
        if "未接続" in buttons:
            _uia_click_once("未接続")
            time.sleep(8)
            state = _ms2_ribbon_state()
            buttons = state.get("buttons", [])
        if "発注不可" in buttons:
            _uia_click_once("発注不可")
    except Exception:
        pass


@app.on_event("startup")
async def _startup_connect() -> None:
    """ブリッジ起動 15 秒後に MS2 を自動接続する。"""
    async def _delayed() -> None:
        await asyncio.sleep(45)
        await asyncio.get_event_loop().run_in_executor(None, _do_rss_connect)
    asyncio.create_task(_delayed())


def _on_workbook_opened() -> None:
    threading.Thread(
        target=lambda: (time.sleep(45), _do_rss_connect()),
        daemon=True,
    ).start()


def _get_rss() -> RssClient:
    global _rss
    if _rss is None:
        _rss = RssClient(workbook_path=_WORKBOOK, dry_run=_DRY_RUN,
                         on_workbook_open=_on_workbook_opened)
    return _rss


def _check_auth(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or malformed Authorization header")
    presented = authorization[len("Bearer ") :].strip()
    if not secrets.compare_digest(presented, _TOKEN):
        raise HTTPException(status_code=403, detail="invalid bearer token")


def _check_orders_enabled() -> None:
    if not _ORDERS_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Order endpoints are disabled on this bridge. Set MS2_BRIDGE_ENABLE_ORDERS=true.",
        )


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "orders_enabled": _ORDERS_ENABLED,
        "dry_run": _DRY_RUN,
        "workbook": _WORKBOOK,
    }


@app.get("/admin/uia-dump")
def uia_dump(authorization: str | None = Header(default=None)) -> Any:
    """Excel リボン上の UIA コントロール名一覧を返す（デバッグ用）。"""
    _check_auth(authorization)
    try:
        import uiautomation as auto
        excel = auto.WindowControl(ClassName="XLMAIN", searchDepth=1)
        if not excel.Exists(2):
            return {"error": "Excel window not found"}
        items: list[dict] = []

        def _walk(ctrl: Any, depth: int = 0) -> None:
            if depth > 10:
                return
            name = ctrl.Name
            ctype = ctrl.ControlTypeName
            if name and depth >= 2:
                items.append({"type": ctype, "name": name, "depth": depth})
            if len(items) >= 400:
                return
            for child in ctrl.GetChildren():
                _walk(child, depth + 1)
        _walk(excel)
        return {"controls": items}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/admin/vba-code")
def get_vba_code(authorization: str | None = Header(default=None)) -> Any:
    """Module1のVBAコードを返す。"""
    _check_auth(authorization)
    try:
        rss = _get_rss()
        wb = rss._ensure_workbook()
        mod = wb.api.VBProject.VBComponents("Module1").CodeModule
        code = mod.Lines(1, mod.CountOfLines)
        return {"code": code}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


def _uia_click_once(button_name: str, wait_secs: int = 5) -> dict[str, Any]:
    import uiautomation as auto
    excel = auto.WindowControl(ClassName="XLMAIN", searchDepth=1)
    if not excel.Exists(2):
        return {"error": "Excel window not found"}
    ms2 = excel.GroupControl(Name="マーケットスピード II", searchDepth=15)
    if not ms2.Exists(wait_secs):
        return {"error": "MS2 ribbon group not found"}
    btn = None
    for group in ms2.GetChildren():
        for child in group.GetChildren():
            if child.ControlTypeName == "ButtonControl" and child.Name.strip() == button_name:
                btn = child
                break
        if btn:
            break
    if btn is None:
        return {"found": False, "button": button_name}
    try:
        tp = btn.GetTogglePattern()
        tp.Toggle()
        return {"ok": True, "method": "toggle", "button": button_name}
    except Exception:
        pass
    try:
        ip = btn.GetInvokePattern()
        ip.Invoke()
        return {"ok": True, "method": "invoke", "button": button_name}
    except Exception:
        pass
    btn.Click()
    return {"ok": True, "method": "click", "button": button_name}


def _activate_ms2_tab() -> bool:
    """MS2 リボンタブを選択状態にする。すでに選択済みなら何もしない。"""
    import uiautomation as auto
    excel = auto.WindowControl(ClassName="XLMAIN", searchDepth=1)
    if not excel.Exists(2):
        return False
    tab = excel.TabItemControl(Name="マーケットスピード II", searchDepth=10)
    if not tab.Exists(3):
        return False
    try:
        sp = tab.GetSelectionItemPattern()
        sp.Select()
    except Exception:
        tab.Click()
    time.sleep(0.5)
    return True


def _ms2_ribbon_state() -> dict[str, Any]:
    """MS2 リボングループ内のボタン名（現在の状態）を返す。"""
    import uiautomation as auto
    _activate_ms2_tab()
    excel = auto.WindowControl(ClassName="XLMAIN", searchDepth=1)
    if not excel.Exists(2):
        return {}
    ms2 = excel.GroupControl(Name="マーケットスピード II", searchDepth=15)
    if not ms2.Exists(3):
        return {}
    names: list[str] = []
    for group in ms2.GetChildren():
        for child in group.GetChildren():
            if child.ControlTypeName == "ButtonControl":
                names.append(child.Name.strip())
    return {"buttons": names}


@app.post("/admin/rss-connect")
def rss_connect(authorization: str | None = Header(default=None)) -> Any:
    """MS2 リボンを「接続中・発注可」状態にする。すでにその状態なら何もしない。"""
    _check_auth(authorization)
    try:
        rss = _get_rss()
        rss._ensure_workbook()
        results: dict[str, Any] = {}

        # 接続: 「未接続」ボタンが見えていればクリック（「接続中」なら何もしない）
        state = _ms2_ribbon_state()
        buttons = state.get("buttons", [])
        if "未接続" in buttons:
            results["接続"] = _uia_click_once("未接続")
            time.sleep(6)
        else:
            results["接続"] = {"skipped": True, "reason": "already connected"}

        # 発注: 「発注不可」が表示されている（=無効）ときだけクリック
        state = _ms2_ribbon_state()
        buttons = state.get("buttons", [])
        if "発注不可" in buttons:
            results["発注"] = _uia_click_once("発注不可")
        else:
            results["発注"] = {"skipped": True, "reason": "already enabled"}

        return {"ok": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/quote")
def quote(
    symbol: str = Query(...),
    exchange: str = Query("T"),
    authorization: str | None = Header(default=None),
) -> Any:
    _check_auth(authorization)
    try:
        return _get_rss().quote(symbol, exchange)
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/board")
def board(
    symbol: str = Query(...),
    exchange: str = Query("T"),
    authorization: str | None = Header(default=None),
) -> Any:
    _check_auth(authorization)
    try:
        return _get_rss().board(symbol, exchange)
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/positions")
def positions(
    account: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> Any:
    _check_auth(authorization)
    try:
        return {"positions": _get_rss().positions(account)}
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/margin")
def margin(
    account: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> Any:
    _check_auth(authorization)
    try:
        return _get_rss().margin(account)
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/orders")
def orders(
    account: str | None = Query(default=None),
    status: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> Any:
    _check_auth(authorization)
    try:
        return {"orders": _get_rss().orders(account, status)}
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/trades")
def trades(
    account: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
) -> Any:
    _check_auth(authorization)
    try:
        return {"trades": _get_rss().trades(account, from_, to)}
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


class PlaceOrderBody(BaseModel):
    symbol: str
    exchange: str = "T"
    side: str
    quantity: int
    order_type: str
    price: float | None = None
    trigger_price: float | None = None
    tif: str = "day"
    account_type: str = "cash"


@app.post("/orders/place")
def place_order(body: PlaceOrderBody, authorization: str | None = Header(default=None)) -> Any:
    _check_auth(authorization)
    _check_orders_enabled()
    try:
        return _get_rss().place_order(body.model_dump())
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


class CancelOrderBody(BaseModel):
    order_id: str
    account: str | None = None


@app.post("/orders/cancel")
def cancel_order(body: CancelOrderBody, authorization: str | None = Header(default=None)) -> Any:
    _check_auth(authorization)
    _check_orders_enabled()
    try:
        return _get_rss().cancel_order(body.order_id, account=body.account)
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


class ModifyOrderBody(BaseModel):
    order_id: str
    new_price: float | None = None
    new_quantity: int | None = None
    account: str | None = None


@app.post("/orders/modify")
def modify_order(body: ModifyOrderBody, authorization: str | None = Header(default=None)) -> Any:
    _check_auth(authorization)
    _check_orders_enabled()
    try:
        return _get_rss().modify_order(
            body.order_id,
            new_price=body.new_price,
            new_quantity=body.new_quantity,
            account=body.account,
        )
    except RssError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.exception_handler(HTTPException)
def _err(request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bridge:app", host=_HOST, port=_PORT, reload=False)

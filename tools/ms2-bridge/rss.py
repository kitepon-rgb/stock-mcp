"""Excel + Marketspeed2 RSS wrapper.

This module is the only part of ms2-bridge that touches Windows COM / Excel.
It uses ``xlwings`` to drive an Excel workbook that has the RSS add-in
loaded (see README.md for setup steps).

Authoritative source for RSS function names and field names:
``docs/ms2-rss-reference/REFERENCE.md`` (extracted from the official PDF
``ms2rss_function.pdf``). Do NOT guess names — quote that reference.

Design
------
The bridge claims one worksheet (``_SHEET_NAME``) and assigns each RSS
function its own non-overlapping column block:

    A:B    quote (single-cell RssMarket calls per field)
    D:E    board (10 ask levels)
    G:H    board (10 buy levels)
    J:R    capacity / 余力       (RssCapacityList)
    T:AK   positions             (RssPositionList)
    AM:BP  orders                (RssOrderList)
    BR:CF  executions            (RssExecutionList)
    CH1    place order           (RssStockOrder)
    CH2    cancel order          (RssCancelOrder)
    CH3    modify order          (RssModifyOrder)

For list functions we use **mode A**: pre-fill row 2 of the block with the
desired Japanese header names, point the formula's ``ヘッダー行`` argument
at that range, and read data from row 3 downward. This avoids Excel's
dynamic-array implicit-intersection rewrites and makes column order
deterministic.

RSS is RTD-based — first reads return ``"取得中"`` / ``"応答待ち"`` until
data arrives. The bridge polls each formula cell until it stabilizes.

``MS2_BRIDGE_DRY_RUN=true`` short-circuits the order-mutation paths
(place/cancel/modify) and returns a stub — used to safely test the
preview/confirm flow end-to-end without touching real capital.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

try:
    import xlwings as xw
except ImportError:
    xw = None  # type: ignore


# === RSS function names (canonical, from REFERENCE.md) ================
_FN_QUOTE = "RssMarket"             # =RssMarket(銘柄, 取得項目) — single value
_FN_ORDER_LIST = "RssOrderList"     # 注文一覧 — list
_FN_EXEC_LIST = "RssExecutionList"  # 約定一覧 — list
_FN_POSITION_LIST = "RssPositionList"   # 保有銘柄一覧 — list
_FN_CAPACITY = "RssCapacityList"    # 余力・保証金率 — list (1 row)
_FN_STOCK_ORDER = "RssStockOrder"   # 現物注文 — placement
_FN_MODIFY = "RssModifyOrder"
_FN_CANCEL = "RssCancelOrder"

# RSS RTD loading sentinels — cell value while still loading
_LOADING_STRINGS = frozenset(["", "取得中", "応答待ち", "#N/A", "loading"])

_RETRIES = 12
# Order placement can take longer: server validation + broker round-trip.
# 60 * 0.5s = 30s upper bound.
_ORDER_RETRIES = 60
_RETRY_SLEEP = 0.5
_SHEET_NAME = "ms2_bridge"

# Per-area state: a single Excel session can't be safely concurrent
# because every call rewrites cells. One module-level lock is enough.
_excel_lock = threading.Lock()


class RssError(RuntimeError):
    """Bridge-internal error wrapping Excel/COM failures and RSS loading states."""


# === Excel helpers ====================================================

def _col_letter(n: int) -> str:
    """1-indexed column number → Excel column letter (1=A, 27=AA, ...)."""
    out: list[str] = []
    while n > 0:
        n, r = divmod(n - 1, 26)
        out.append(chr(65 + r))
    return "".join(reversed(out))


def _is_loading(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    s = value.strip()
    if s in _LOADING_STRINGS:
        return True
    # Order-formula cells render as "={formula_text} => {status}". When the
    # broker is still processing, {status} is one of the loading sentinels.
    # Recognize that suffix form too.
    if " => " in s:
        suffix = s.rsplit(" => ", 1)[1].strip()
        if suffix in _LOADING_STRINGS:
            return True
    return False


# === Column blocks ====================================================
# Start column (1-indexed) and width (number of columns).

_CAPACITY_COL = 10   # J
_CAPACITY_WIDTH = 7

_POSITION_COL = 20   # T
_POSITION_HEADERS = [
    "銘柄コード", "銘柄名称", "口座区分", "保有数量", "発注数量",
    "平均取得価額", "時価", "前日比", "前日比率", "時価評価額",
    "評価損益額", "評価損益率", "銘柄情報等", "JAX時価", "JNX時価",
    "PER", "PBR", "配当利回り",
]
_POSITION_KEYS = [
    "symbol", "name", "account_type", "quantity", "open_order_qty",
    "avg_price", "last_price", "change", "change_pct", "market_value",
    "unrealized_pnl", "unrealized_pnl_pct", "notes", "jax_price", "jnx_price",
    "per", "pbr", "dividend_yield",
]

_ORDER_COL = 39      # AM
_ORDER_HEADERS = [
    "注文番号", "受付No", "通常注文状況", "逆指値注文状況", "アルゴ注文状況",
    "銘柄コード", "銘柄名称", "口座区分", "市場名称", "信用区分",
    "弁済期限", "発注/受注日時", "売買", "取引", "執行条件",
    "注文期限", "注文数量", "約定数量", "注文単価", "注文区分",
    "逆指値条件", "セット注文", "セット注文条件", "税区分", "注文失効日時",
    "注文失効理由", "入力経路", "アルゴ注文条件", "SOR判定時刻",
    "SOR判定時主市場情報/対象外理由",
]
_ORDER_KEYS = [
    "order_id", "receipt_no", "status_normal", "status_stop", "status_algo",
    "symbol", "name", "account_type", "exchange", "margin_class",
    "settlement_term", "submitted_at", "side", "transaction", "tif",
    "expiry", "quantity", "executed_qty", "price", "order_kind",
    "stop_condition", "is_set", "set_condition", "tax_class", "failed_at",
    "failed_reason", "input_channel", "algo_condition", "sor_decided_at",
    "sor_market_info",
]

_EXEC_COL = 70       # BR
_EXEC_HEADERS = [
    "約定日", "受渡日", "銘柄コード", "銘柄名称", "口座区分",
    "市場名称", "信用区分", "弁済期限", "取引", "売買",
    "約定数量", "約定単価", "約定代金", "税区分", "特別空売り料(円)",
]
_EXEC_KEYS = [
    "filled_at", "settled_on", "symbol", "name", "account_type",
    "exchange", "margin_class", "settlement_term", "transaction", "side",
    "quantity", "price", "amount", "tax_class", "special_short_fee",
]

_CAPACITY_HEADERS = [
    "現物買付可能額", "信用口座_保証金余裕額", "信用口座_信用新規建余力",
    "信用口座_保証金率（新規建）", "自動振替含む_保証金余裕額",
    "自動振替含む_信用新規建余力", "自動振替含む_保証金率（新規建）",
]
_CAPACITY_KEYS = [
    "cash_buying_power", "margin_room", "margin_buying_power",
    "margin_ratio_new", "margin_room_autotransfer",
    "margin_buying_power_autotransfer", "margin_ratio_autotransfer",
]

_ORDER_PLACE_CELL = "CH1"
_ORDER_CANCEL_CELL = "CH2"
_ORDER_MODIFY_CELL = "CH3"
_ORDER_ID_LOOKUP_CELL = "CJ1"
_ORDER_ID_LIST_COL = 88  # CJ — RssOrderIDList anchor
_ORDER_ID_LIST_HEADERS = [
    "発注ID", "関数名", "発注日", "発注時刻", "注文番号", "発注結果",
]


# === Quote field names (from REFERENCE.md, 取得項目 column) ===========

_QUOTE_FIELDS: list[tuple[str, str]] = [
    ("name", "銘柄名称"),
    ("market", "市場名称"),
    ("ts_date", "現在日付"),
    ("ts_time", "現在値詳細時刻"),
    ("last_price", "現在値"),
    ("previous_close", "前日終値"),
    ("change", "前日比"),
    ("change_pct", "前日比率"),
    ("open", "始値"),
    ("day_high", "高値"),
    ("day_low", "安値"),
    ("bid", "最良買気配値"),
    ("ask", "最良売気配値"),
    ("bid_size", "最良買気配数量"),
    ("ask_size", "最良売気配数量"),
    ("volume", "出来高"),
    ("value", "売買代金"),
    ("vwap", "出来高加重平均"),
    ("market_cap", "時価総額"),
    ("lot_size", "単位株数"),
    ("over_qty", "OVER気配数量"),
    ("under_qty", "UNDER気配数量"),
    ("market_buy_qty", "買成行数量"),
    ("market_sell_qty", "売成行数量"),
    ("base_price", "当日基準値"),
]


class RssClient:
    """Connection to Excel + RSS via xlwings.

    Parameters
    ----------
    workbook_path:
        Absolute path to the Excel workbook that has the RSS add-in loaded.
        If None, the bridge attaches to the currently active Excel workbook.
    dry_run:
        When True, mutating calls (place/cancel/modify) return a stub
        instead of actually invoking RSS order functions.
    """

    def __init__(self, workbook_path: str | None = None, dry_run: bool = False,
                 on_workbook_open: Any = None) -> None:
        self.workbook_path = workbook_path
        self.dry_run = dry_run
        self._wb: Any = None
        self._labels_set = False
        self._next_order_id = int(time.time()) % 1_000_000_000
        self._on_workbook_open = on_workbook_open

    # ---------- lifecycle ----------

    def _ensure_workbook(self) -> Any:
        if xw is None:
            raise RssError(
                "xlwings is not installed on this host. "
                "Install it on the Windows machine: `pip install xlwings`."
            )
        if self._wb is not None:
            try:
                _ = self._wb.name
                return self._wb
            except Exception:
                self._wb = None
                self._labels_set = False
        if self.workbook_path and os.path.exists(self.workbook_path):
            # シェル経由で開く: COM直接起動だとRSSアドインが読み込まれないため
            import subprocess
            try:
                already_open = any(
                    os.path.normcase(b.fullname) == os.path.normcase(self.workbook_path)
                    for b in xw.books
                )
            except Exception:
                already_open = False
            if not already_open:
                subprocess.Popen(["cmd", "/c", "start", "", self.workbook_path],
                                 shell=False)
                for _ in range(30):
                    time.sleep(1)
                    try:
                        for b in xw.books:
                            if os.path.normcase(b.fullname) == os.path.normcase(self.workbook_path):
                                self._wb = b
                                break
                    except Exception:
                        pass
                    if self._wb:
                        break
                if self._wb is None:
                    raise RssError("Workbook did not open within 30 seconds.")
            else:
                for b in xw.books:
                    if os.path.normcase(b.fullname) == os.path.normcase(self.workbook_path):
                        self._wb = b
                        break
        else:
            try:
                self._wb = xw.books.active
            except Exception as exc:
                raise RssError(
                    "no active Excel workbook found. "
                    "Open Excel with the RSS add-in loaded, or set MS2_WORKBOOK_PATH."
                ) from exc
        if _SHEET_NAME not in [s.name for s in self._wb.sheets]:
            self._wb.sheets.add(_SHEET_NAME)
        if not self._labels_set:
            self._setup_sheet_labels(self._wb.sheets[_SHEET_NAME])
            self._labels_set = True
        if self._on_workbook_open:
            self._on_workbook_open()
        return self._wb

    def _sheet(self) -> Any:
        wb = self._ensure_workbook()
        return wb.sheets[_SHEET_NAME]

    def _recalc(self) -> None:
        try:
            self._wb.app.calculate()
        except Exception:
            pass

    def _setup_sheet_labels(self, sheet: Any) -> None:
        """A列にフィールドラベルとエリアガイドを設定する（初回接続時のみ実行）。"""
        if sheet.range("A1").value:
            return  # 既設定済み

        # A列: 株価フィールド名
        for i, (_key, field) in enumerate(_QUOTE_FIELDS):
            cell = sheet.range(f"A{i + 1}")
            cell.value = field
            cell.color = (220, 235, 255)
            cell.api.Font.Bold = True
            cell.api.HorizontalAlignment = -4152  # xlRight

        # 各エリアのマーカー（未使用列に配置）
        markers = [
            ("C1",  "【売板】D=値 / E=数量"),
            ("F1",  "【買板】G=値 / H=数量"),
            ("I1",  "【余力】→ J列〜"),
            ("S1",  "【保有銘柄】→ T列〜"),
            ("AL1", "【注文一覧】→ AM列〜"),
            ("BQ1", "【約定一覧】→ BR列〜"),
            ("CG1", "【発注制御】CH1=発注 / CH2=取消 / CH3=訂正  ← 触らない"),
        ]
        marker_colors = {
            "C1": (255, 235, 235), "F1": (235, 255, 235),
            "I1": (255, 255, 200), "S1": (200, 255, 210),
            "AL1": (200, 220, 255), "BQ1": (255, 220, 200),
            "CG1": (255, 200, 200),
        }
        for cell_addr, text in markers:
            c = sheet.range(cell_addr)
            c.value = text
            c.color = marker_colors[cell_addr]
            c.api.Font.Bold = True

        # 列幅
        col_widths = {
            "A:A": 16, "B:B": 18, "C:C": 20, "D:E": 10,
            "F:F": 20, "G:H": 10, "I:I": 14, "S:S": 20,
            "AL:AL": 20, "BQ:BQ": 20, "CG:CG": 45,
        }
        for cols, width in col_widths.items():
            sheet.api.Columns(cols).ColumnWidth = width

        # A27〜: エリアガイド表
        guide = [
            ["エリア",          "場所",              "内容"],
            ["リアルタイム株価", "B列 (1〜25行)",     "直近照会銘柄のスナップショット"],
            ["売板 (10本)",     "D〜E列 (1〜10行)",  "売気配値・数量"],
            ["買板 (10本)",     "G〜H列 (1〜10行)",  "買気配値・数量"],
            ["余力・保証金",    "J〜P列 (3行目〜)",   "現物余力・信用余力"],
            ["保有銘柄",        "T〜AK列 (3行目〜)",  "ポジション一覧"],
            ["注文一覧",        "AM〜BP列 (3行目〜)", "未約定・約定済"],
            ["約定一覧",        "BR〜CF列 (3行目〜)", "本日約定履歴"],
            ["発注制御 ※触らない", "CH〜CJ列 (1行目〜)", "stock-mcp が自動書込み"],
        ]
        for i, row in enumerate(guide):
            r = 27 + i
            sheet.range(f"A{r}:C{r}").value = row
            if i == 0:
                rng = sheet.range(f"A{r}:C{r}")
                rng.color = (60, 80, 160)
                rng.api.Font.Bold = True
                rng.api.Font.Color = 0xFFFFFF
            elif i % 2 == 0:
                sheet.range(f"A{r}:C{r}").color = (245, 245, 255)

    # ---------- read helpers ----------

    def _write_formula(self, sheet: Any, cell: str, formula: str) -> None:
        sheet.range(cell).formula = formula

    def _write_headers(self, sheet: Any, row: int, start_col: int, headers: list[str]) -> None:
        rng = sheet.range(
            f"{_col_letter(start_col)}{row}:{_col_letter(start_col + len(headers) - 1)}{row}"
        )
        rng.value = headers

    def _wait_for(self, sheet: Any, cell: str, retries: int = _RETRIES) -> Any:
        last: Any = None
        for _ in range(retries):
            self._recalc()
            value = sheet.range(cell).value
            last = value
            if not _is_loading(value):
                return value
            time.sleep(_RETRY_SLEEP)
        return last

    def _wait_for_data_row(
        self,
        sheet: Any,
        start_col: int,
        row: int,
        width: int,
    ) -> list[list[Any]]:
        """Poll a single output row until cells stabilize.

        RTD-backed cells fill in asynchronously even after the formula cell
        itself has settled. We wait until the first row reaches a steady
        state — either every cell has a definite value (number, string, or
        the RSS dash placeholder), or the retry budget is exhausted.

        Returns the row as a list-of-lists shape (1 row × ``width`` cols).
        """
        rows: list[list[Any]] = [[None] * width]
        for _ in range(_RETRIES):
            self._recalc()
            rows = self._read_block(sheet, start_col, row, 1, width)
            cells = rows[0] if rows else [None] * width
            if all(not _is_loading(c) for c in cells):
                return rows
            time.sleep(_RETRY_SLEEP)
        return rows

    def _read_block(
        self,
        sheet: Any,
        start_col: int,
        first_row: int,
        max_rows: int,
        width: int,
    ) -> list[list[Any]]:
        end_col = start_col + width - 1
        start = f"{_col_letter(start_col)}{first_row}"
        end = f"{_col_letter(end_col)}{first_row + max_rows - 1}"
        rng = sheet.range(f"{start}:{end}")
        v = rng.value
        if v is None:
            return [[None] * width]
        if not isinstance(v, list):
            return [[v]]
        if v and not isinstance(v[0], list):
            return [v]
        return v

    def _list_to_dicts(
        self,
        rows: list[list[Any]],
        keys: list[str],
    ) -> list[dict[str, Any]]:
        """Convert a list-function result block to per-row dicts.

        Skips:
          * rows whose first cell is empty / None
          * "placeholder" rows where every non-None cell is a dash string
            (RSS returns ``'--------'`` for fields that don't apply, e.g.
            no-data sentinels for empty position/order lists).
        """
        out: list[dict[str, Any]] = []
        for row in rows:
            if not row:
                break
            first = row[0]
            if first is None or (isinstance(first, str) and first.strip() == ""):
                break
            if self._is_placeholder_row(row):
                continue
            out.append({k: (row[i] if i < len(row) else None) for i, k in enumerate(keys)})
        return out

    @staticmethod
    def _is_placeholder_row(row: list[Any]) -> bool:
        """True when every populated cell is an RSS dash placeholder."""
        any_value = False
        for cell in row:
            if cell is None:
                continue
            any_value = True
            if isinstance(cell, str) and set(cell.strip()) <= {"-", "ー", "－"}:
                continue
            return False
        return any_value

    # ---------- read-only APIs ----------

    def quote(self, symbol: str, exchange: str = "T") -> dict[str, Any]:
        with _excel_lock:
            sheet = self._sheet()
            sym = self._normalize_symbol(symbol, exchange)
            for i, (_key, field) in enumerate(_QUOTE_FIELDS):
                self._write_formula(sheet, f"B{i + 1}", f'={_FN_QUOTE}("{sym}","{field}")')
            n = len(_QUOTE_FIELDS)
            values: list[Any] = [None] * n
            for _ in range(_RETRIES):
                self._recalc()
                raw = sheet.range(f"B1:B{n}").value
                values = raw if isinstance(raw, list) else [raw]
                if not any(_is_loading(v) for v in values):
                    break
                time.sleep(_RETRY_SLEEP)
        out: dict[str, Any] = {"symbol": symbol, "exchange": exchange}
        for (key, _field), value in zip(_QUOTE_FIELDS, values):
            out[key] = value
        return out

    def board(self, symbol: str, exchange: str = "T") -> dict[str, Any]:
        with _excel_lock:
            sheet = self._sheet()
            sym = self._normalize_symbol(symbol, exchange)
            for level in range(1, 11):
                self._write_formula(sheet, f"D{level}", f'={_FN_QUOTE}("{sym}","最良売気配値{level}")')
                self._write_formula(sheet, f"E{level}", f'={_FN_QUOTE}("{sym}","最良売気配数量{level}")')
                self._write_formula(sheet, f"G{level}", f'={_FN_QUOTE}("{sym}","最良買気配値{level}")')
                self._write_formula(sheet, f"H{level}", f'={_FN_QUOTE}("{sym}","最良買気配数量{level}")')
            ask_vals: list[list[Any]] = []
            bid_vals: list[list[Any]] = []
            for _ in range(_RETRIES):
                self._recalc()
                ask_vals = self._read_block(sheet, 4, 1, 10, 2)
                bid_vals = self._read_block(sheet, 7, 1, 10, 2)
                flat = [c for row in (ask_vals + bid_vals) for c in row]
                if not any(_is_loading(v) for v in flat):
                    break
                time.sleep(_RETRY_SLEEP)
            bids = [{"level": i + 1, "price": bid_vals[i][0], "size": bid_vals[i][1]} for i in range(10)]
            asks = [{"level": i + 1, "price": ask_vals[i][0], "size": ask_vals[i][1]} for i in range(10)]
            return {"symbol": symbol, "exchange": exchange, "bids": bids, "asks": asks}

    def margin(self, account: str | None = None) -> dict[str, Any]:
        with _excel_lock:
            sheet = self._sheet()
            anchor_col = _CAPACITY_COL
            self._write_headers(sheet, 2, anchor_col, _CAPACITY_HEADERS)
            header_range = (
                f"{_col_letter(anchor_col)}2:"
                f"{_col_letter(anchor_col + _CAPACITY_WIDTH - 1)}2"
            )
            anchor_cell = f"{_col_letter(anchor_col)}1"
            self._write_formula(sheet, anchor_cell, f"={_FN_CAPACITY}({header_range})")
            self._wait_for(sheet, anchor_cell)
            rows = self._wait_for_data_row(sheet, anchor_col, 3, _CAPACITY_WIDTH)
        data = rows[0] if rows else [None] * _CAPACITY_WIDTH
        out: dict[str, Any] = {"account": account}
        for key, value in zip(_CAPACITY_KEYS, data):
            out[key] = value
        return out

    def positions(self, account: str | None = None) -> list[dict[str, Any]]:
        with _excel_lock:
            sheet = self._sheet()
            anchor_col = _POSITION_COL
            self._write_headers(sheet, 2, anchor_col, _POSITION_HEADERS)
            width = len(_POSITION_HEADERS)
            header_range = (
                f"{_col_letter(anchor_col)}2:"
                f"{_col_letter(anchor_col + width - 1)}2"
            )
            account_arg = self._account_filter(account)
            anchor_cell = f"{_col_letter(anchor_col)}1"
            self._write_formula(
                sheet, anchor_cell,
                f'={_FN_POSITION_LIST}({header_range},,"{account_arg}")',
            )
            self._wait_for(sheet, anchor_cell)
            self._wait_for_data_row(sheet, anchor_col, 3, width)
            rows = self._read_block(sheet, anchor_col, 3, 500, width)
        return self._list_to_dicts(rows, _POSITION_KEYS)

    def orders(self, account: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        with _excel_lock:
            sheet = self._sheet()
            anchor_col = _ORDER_COL
            self._write_headers(sheet, 2, anchor_col, _ORDER_HEADERS)
            width = len(_ORDER_HEADERS)
            header_range = (
                f"{_col_letter(anchor_col)}2:"
                f"{_col_letter(anchor_col + width - 1)}2"
            )
            status_code = self._order_status_code(status)
            account_arg = self._account_filter(account)
            anchor_cell = f"{_col_letter(anchor_col)}1"
            # =RssOrderList(ヘッダー行, 注文状況, 注文種類, 銘柄コード, 口座区分, ...)
            self._write_formula(
                sheet, anchor_cell,
                f'={_FN_ORDER_LIST}({header_range},{status_code},0,,"{account_arg}",0,0,0,0,0)',
            )
            self._wait_for(sheet, anchor_cell)
            self._wait_for_data_row(sheet, anchor_col, 3, width)
            rows = self._read_block(sheet, anchor_col, 3, 500, width)
        return self._list_to_dicts(rows, _ORDER_KEYS)

    def trades(
        self,
        account: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict[str, Any]]:
        with _excel_lock:
            sheet = self._sheet()
            anchor_col = _EXEC_COL
            self._write_headers(sheet, 2, anchor_col, _EXEC_HEADERS)
            width = len(_EXEC_HEADERS)
            header_range = (
                f"{_col_letter(anchor_col)}2:"
                f"{_col_letter(anchor_col + width - 1)}2"
            )
            account_arg = self._account_filter(account)
            anchor_cell = f"{_col_letter(anchor_col)}1"
            self._write_formula(
                sheet, anchor_cell,
                f'={_FN_EXEC_LIST}({header_range},0,,"{account_arg}",0,0)',
            )
            self._wait_for(sheet, anchor_cell)
            self._wait_for_data_row(sheet, anchor_col, 3, width)
            rows = self._read_block(sheet, anchor_col, 3, 1000, width)
        items = self._list_to_dicts(rows, _EXEC_KEYS)
        if from_date or to_date:
            items = [
                d for d in items
                if self._date_in_range(d.get("filled_at"), from_date, to_date)
            ]
        return items

    # ---------- mutating APIs ----------

    def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            return {
                "dry_run": True,
                "would_send": order,
                "rss_formula": self._build_stock_order_formula(order, order_id="DRY", trigger=0),
                "order_id": f"DRY-{int(time.time())}",
            }
        if order.get("account_type") == "margin":
            raise RssError(
                "margin (信用) orders are not yet implemented. "
                "Use account_type='cash' for 現物 only."
            )
        with _excel_lock:
            sheet = self._sheet()
            order_id = self._allocate_order_id()
            # Stage 1: 発注トリガー=0 to confirm argument validation passes.
            formula_stage1 = self._build_stock_order_formula(order, order_id=order_id, trigger=0)
            self._write_formula(sheet, _ORDER_PLACE_CELL, formula_stage1)
            staged = self._wait_for(sheet, _ORDER_PLACE_CELL, retries=_ORDER_RETRIES)
            staged_str = str(staged) if staged is not None else ""
            if "入力エラー" in staged_str or "エラー" in staged_str:
                return {
                    "ok": False,
                    "stage": "validation",
                    "status": staged_str,
                    "echo": order,
                }
            # Stage 2: flip 発注トリガー to 1.
            formula_stage2 = self._build_stock_order_formula(order, order_id=order_id, trigger=1)
            self._write_formula(sheet, _ORDER_PLACE_CELL, formula_stage2)
            final = self._wait_for(sheet, _ORDER_PLACE_CELL, retries=_ORDER_RETRIES)
            # Look up the broker-side 注文番号 from RssOrderIDList using our 発注ID.
            broker_order_id = None
            if "発注済み" in str(final or ""):
                broker_order_id = self._lookup_broker_order_id(sheet, order_id)
            sheet.range(_ORDER_PLACE_CELL).clear_contents()
        final_str = str(final) if final is not None else ""
        return {
            "ok": "発注済み" in final_str,
            "stage": "submit",
            "status": final_str,
            "submission_id": order_id,             # Excel-side 発注ID
            "order_id": broker_order_id,           # broker 注文番号 — pass to cancel/modify
            "echo": order,
        }

    def _lookup_broker_order_id(self, sheet: Any, submission_id: int) -> int | None:
        """Map a 発注ID (Excel-side) to a 注文番号 (broker-side) via RssOrderIDList.

        Returns ``None`` if the lookup fails or the id is not in the list yet
        (RSS sometimes takes a moment to update the list after acceptance).
        """
        anchor = _ORDER_ID_LOOKUP_CELL
        header_range = (
            f"{_col_letter(_ORDER_ID_LIST_COL)}2:"
            f"{_col_letter(_ORDER_ID_LIST_COL + len(_ORDER_ID_LIST_HEADERS) - 1)}2"
        )
        self._write_headers(sheet, 2, _ORDER_ID_LIST_COL, _ORDER_ID_LIST_HEADERS)
        self._write_formula(sheet, anchor, f"=RssOrderIDList({header_range})")
        self._wait_for(sheet, anchor)
        # Poll up to ~5s for the new id to appear.
        target = float(submission_id)
        for _ in range(10):
            self._recalc()
            rows = self._read_block(sheet, _ORDER_ID_LIST_COL, 3, 100, len(_ORDER_ID_LIST_HEADERS))
            for row in rows:
                if not row or row[0] is None:
                    break
                try:
                    if float(row[0]) == target:
                        # column 5 = 注文番号
                        raw = row[4]
                        if raw is None or (isinstance(raw, str) and raw.strip() in ("", "-", "ー", "--------")):
                            return None
                        try:
                            return int(raw)
                        except (TypeError, ValueError):
                            return None
                except (TypeError, ValueError):
                    continue
            time.sleep(0.5)
        return None

    def cancel_order(self, order_id: str, account: str | None = None) -> dict[str, Any]:
        if self.dry_run:
            return {"dry_run": True, "order_id": order_id, "cancelled": True}
        with _excel_lock:
            sheet = self._sheet()
            rss_id = self._allocate_order_id()
            formula1 = f'={_FN_CANCEL}({rss_id},0,{order_id})'
            self._write_formula(sheet, _ORDER_CANCEL_CELL, formula1)
            staged = self._wait_for(sheet, _ORDER_CANCEL_CELL, retries=_ORDER_RETRIES)
            staged_str = str(staged) if staged is not None else ""
            if "入力エラー" in staged_str or "エラー" in staged_str:
                return {"ok": False, "stage": "validation", "status": staged_str}
            formula2 = f'={_FN_CANCEL}({rss_id},1,{order_id})'
            self._write_formula(sheet, _ORDER_CANCEL_CELL, formula2)
            final = self._wait_for(sheet, _ORDER_CANCEL_CELL, retries=_ORDER_RETRIES)
            sheet.range(_ORDER_CANCEL_CELL).clear_contents()
        final_str = str(final) if final is not None else ""
        return {
            "ok": "発注済み" in final_str or "受付" in final_str,
            "status": final_str,
            "order_id": order_id,
        }

    def modify_order(
        self,
        order_id: str,
        new_price: float | None = None,
        new_quantity: int | None = None,
        account: str | None = None,
    ) -> dict[str, Any]:
        if self.dry_run:
            return {
                "dry_run": True,
                "order_id": order_id,
                "new_price": new_price,
                "new_quantity": new_quantity,
            }
        with _excel_lock:
            sheet = self._sheet()
            rss_id = self._allocate_order_id()
            # Assume original 注文区分=0 (通常). Only price/qty are modified.
            qty_arg = new_quantity if new_quantity is not None else ""
            price_kind = "1" if new_price is not None else ""   # 1=指値
            price_arg = new_price if new_price is not None else ""
            formula1 = (
                f"={_FN_MODIFY}({rss_id},0,{order_id},0,"
                f"{qty_arg},{price_kind},{price_arg})"
            )
            self._write_formula(sheet, _ORDER_MODIFY_CELL, formula1)
            staged = self._wait_for(sheet, _ORDER_MODIFY_CELL, retries=_ORDER_RETRIES)
            staged_str = str(staged) if staged is not None else ""
            if "入力エラー" in staged_str or "エラー" in staged_str:
                return {"ok": False, "stage": "validation", "status": staged_str}
            formula2 = (
                f"={_FN_MODIFY}({rss_id},1,{order_id},0,"
                f"{qty_arg},{price_kind},{price_arg})"
            )
            self._write_formula(sheet, _ORDER_MODIFY_CELL, formula2)
            final = self._wait_for(sheet, _ORDER_MODIFY_CELL, retries=_ORDER_RETRIES)
            sheet.range(_ORDER_MODIFY_CELL).clear_contents()
        final_str = str(final) if final is not None else ""
        return {
            "ok": "発注済み" in final_str or "受付" in final_str,
            "status": final_str,
            "order_id": order_id,
        }

    # ---------- internal helpers ----------

    def _allocate_order_id(self) -> int:
        self._next_order_id += 1
        return self._next_order_id

    @staticmethod
    def _normalize_symbol(symbol: str, exchange: str) -> str:
        if "." in symbol:
            return symbol
        ex = (exchange or "T").upper()
        if ex == "T":
            return symbol
        if ex in ("JAX", "JNX"):
            return f"{symbol}.{ex}"
        return symbol

    @staticmethod
    def _account_filter(account: str | None) -> str:
        if account is None:
            return "A"
        m = {
            "all": "A", "a": "A",
            "specific": "0", "cash": "0", "0": "0",
            "general": "1", "1": "1",
            "nisa": "2", "2": "2",
            "old_nisa": "3", "3": "3",
        }
        return m.get(str(account).lower(), "A")

    @staticmethod
    def _order_status_code(status: str | None) -> int:
        if status is None:
            return 0
        try:
            return int(status)
        except (TypeError, ValueError):
            pass
        m = {
            "all": 0, "active": 1, "waiting": 2, "executing": 3,
            "partial": 4, "filled": 5, "cancelled": 8, "rejected": 11,
        }
        return m.get(status.lower(), 0)

    @staticmethod
    def _date_in_range(filled_at: Any, from_date: str | None, to_date: str | None) -> bool:
        if not isinstance(filled_at, str):
            return True
        # filled_at format from RSS: 'YYYY/MM/DD HH:MM:SS'
        day = filled_at.split(" ", 1)[0].replace("/", "-")
        if from_date and day < from_date:
            return False
        if to_date and day > to_date:
            return False
        return True

    def _build_stock_order_formula(self, order: dict[str, Any], *, order_id: Any, trigger: int) -> str:
        sym = self._normalize_symbol(order["symbol"], order.get("exchange", "T"))
        side_code = 3 if order["side"] == "buy" else 1
        quantity = int(order["quantity"])
        otype = order["order_type"]
        # 注文区分=0 (通常) requires the four 逆指値* args (12-15 of the stop block,
        # i.e. positional args 13-16 of the formula) to be OMITTED, not zero.
        # Rakuten's server-side validation rejects "通常注文 with 逆指値条件価格"
        # when those slots carry a literal 0 instead of an empty value.
        if otype == "limit":
            order_kind = 0   # 通常
            price_kind = 1   # 指値
            price = order.get("price") or 0
            stop_trigger_price = ""
            stop_trigger_op = ""
            stop_price_kind = ""
            stop_price = ""
        elif otype == "market":
            order_kind = 0
            price_kind = 0   # 成行
            price = ""
            stop_trigger_price = ""
            stop_trigger_op = ""
            stop_price_kind = ""
            stop_price = ""
        elif otype == "stop":
            order_kind = 2   # 逆指値待機
            price_kind = ""
            price = ""
            stop_trigger_price = order.get("trigger_price") or 0
            stop_trigger_op = 1 if order["side"] == "buy" else 2
            stop_price_kind = 0   # 成行
            stop_price = ""
        elif otype == "stop_limit":
            order_kind = 2
            price_kind = ""
            price = ""
            stop_trigger_price = order.get("trigger_price") or 0
            stop_trigger_op = 1 if order["side"] == "buy" else 2
            stop_price_kind = 1   # 指値
            stop_price = order.get("price") or 0
        else:
            raise RssError(f"unsupported order_type: {otype}")
        tif_map = {
            "day": 1, "week": 2, "opening": 3, "closing": 4,
            "gtd": 5, "closing_unconditional": 6, "unconditional": 7,
            "gtc": 2,   # legacy alias from stock-mcp side
        }
        tif_code = tif_map.get(order.get("tif", "day"), 1)
        expiry = order.get("expiry", "")
        account_kind = 0   # 特定
        # SOR=1 (Smart Order Routing) is the safer default:
        #   - Rakuten "手数料ゼロコース" accounts REQUIRE SOR=1; orders with SOR=0
        #     are rejected at the broker server with status "手数料ゼロコースでは、
        #     SORを有効にして、再度注文してください。"
        #   - Non-zero-commission accounts accept either.
        # SOR=1 is incompatible only with 執行条件=3 (寄付) / 4 (引け).
        sor_kind = 0 if tif_code in (3, 4) else 1
        if "sor" in order:                # explicit override from upstream
            sor_kind = 1 if order["sor"] else 0
        args = [
            order_id, trigger, f'"{sym}"', side_code, order_kind, sor_kind,
            quantity, price_kind, price, tif_code, expiry, account_kind,
            stop_trigger_price, stop_trigger_op, stop_price_kind, stop_price,
            0, "", "", "",   # セット注文: 不使用
        ]
        return f"={_FN_STOCK_ORDER}({','.join(str(a) for a in args)})"

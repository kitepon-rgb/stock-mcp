# ms2-bridge

Windows-side HTTP bridge that lets `stock-mcp` (running on the LAN server)
read market data and place orders through Rakuten Securities **Marketspeed2**
via the **RSS** Excel add-in.

```text
[Claude / Claude.ai]
        |   OAuth
        v
[stock-mcp on 192.168.1.2:39200]  --- HTTP+bearer --->  [ms2-bridge on Windows:39201]
                                                                |
                                                                | xlwings (Excel COM)
                                                                v
                                                       [Excel + RSS add-in]
                                                                |
                                                                v
                                                       [Marketspeed2]
```

---

## Prerequisites on the Windows host

1. **Marketspeed2** installed and logged in to your Rakuten account.
2. **Microsoft Excel** (Office 365 / Excel 2019+).
3. **RSS add-in** for Marketspeed2 loaded in Excel.
   - In Marketspeed2: enable RSS from the menu (the wording depends on the MS2
     version; look for something like "RSS のインストール" / "RSS の起動").
   - In Excel: File → Options → Add-ins → make sure the `MarketspeedRss`
     (or similar) add-in is checked.
4. **Python 3.11+** on Windows (the python.org installer is fine; tick
   "Add Python to PATH" during install).
5. Network: the Windows host must be reachable from the LAN server at
   `192.168.1.2`. Confirm with `ping <windows-ip>` from the server.

---

## Install the bridge

```powershell
# Copy this folder onto Windows, e.g. C:\Users\<you>\ms2-bridge
cd C:\Users\<you>\ms2-bridge

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configure

1. Copy `.env.example` → `.env`.
2. Generate the shared bearer token:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Paste it into `.env` as `MS2_BRIDGE_TOKEN=...`.
3. Set the same value on the stock-mcp server as `MS2_BRIDGE_TOKEN`, and add
   `MS2_BRIDGE_URL=http://<windows-ip>:39201` there.
4. Set `MS2_WORKBOOK_PATH` to the absolute path of the RSS-enabled workbook:

   ```text
   MS2_WORKBOOK_PATH=C:\Users\<you>\Documents\Book1.xlsm
   ```

   This allows the bridge to open Excel automatically if it is not already
   running when a request arrives.
5. Keep `MS2_BRIDGE_ENABLE_ORDERS=false` and `MS2_BRIDGE_DRY_RUN=true` while
   you smoke-test the wiring.

---

## Run

1. Start Marketspeed2 and log in.
2. In the bridge folder:

   ```powershell
   .venv\Scripts\activate
   python bridge.py
   ```

   The bridge will open Excel automatically if it is not already running,
   and will enable the RSS connection and order mode within 45 seconds.

3. Smoke test from the stock-mcp server (LAN):

   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://<windows-ip>:39201/healthz
   # -> {"ok": true, "orders_enabled": false, "dry_run": true, ...}

   curl -H "Authorization: Bearer <TOKEN>" \
        "http://<windows-ip>:39201/quote?symbol=7203&exchange=T"
   ```

4. End-to-end via Claude / MCP: call `ms2_quote(symbol="7203")` once
   `MS2_BRIDGE_URL` and `MS2_BRIDGE_TOKEN` are set on stock-mcp.

---

## Auto-connect behaviour

The bridge manages the MS2 ribbon state automatically:

- **On startup**: 45 seconds after the bridge starts, it checks the MS2
  ribbon and clicks "未接続" → "接続中" and "発注不可" → "発注可" as needed.
- **When Excel is closed and reopened**: if the bridge opens a new workbook
  (because Excel was not running), the same 45-second timer fires again.
- The check is idempotent — if the ribbon is already in the correct state,
  nothing is clicked.

To trigger the auto-connect manually at any time:

```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" \
     http://<windows-ip>:39201/admin/rss-connect
```

---

## Run on boot

Place two items in the Windows **Startup folder**
(`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`):

1. **A shortcut to the workbook** (`Book1.xlsm`) — opens Excel with the
   RSS add-in loaded at login.
2. **A VBScript** that starts the bridge without a console window:

   ```vbscript
   Set ws = CreateObject("WScript.Shell")
   ws.CurrentDirectory = "C:\Users\<you>\ms2-bridge"
   ws.Run """C:\Users\<you>\ms2-bridge\.venv\Scripts\python.exe"" bridge.py", 0, False
   ```

   Save as `ms2-bridge.vbs` in the Startup folder.

> **Note**: Task Scheduler requires elevation to register tasks. The Startup
> folder approach works without administrator rights.

---

## Going live with orders

The bridge ships **disabled for mutations** on purpose. To enable order
placement:

1. On the bridge: set `MS2_BRIDGE_ENABLE_ORDERS=true` and
   `MS2_BRIDGE_DRY_RUN=false`.
2. On stock-mcp: set `STOCK_MCP_ENABLE_ORDERS=true` and restart the service.
3. The 2-step preview/confirm flow is enforced by stock-mcp:
   - `ms2_place_order_preview(...)` → returns a 60-second `confirm_token`
     after running max-qty (1000) and max-notional (¥5M) guards.
   - `ms2_place_order_confirm(confirm_token)` → the bridge forwards to RSS.

Tip: leave `MS2_BRIDGE_DRY_RUN=true` for first end-to-end verification — the
bridge returns a `DRY-<timestamp>` order id instead of touching the broker.
Flip to `false` only when you've seen the dry-run path succeed.

---

## Admin endpoints

These endpoints require the same bearer token as the data endpoints.

| Endpoint | Method | Description |
|---|---|---|
| `/admin/rss-connect` | POST | Click ribbon buttons to reach 接続中・発注可 (idempotent) |
| `/admin/uia-dump` | GET | Dump MS2 ribbon control names (debug) |
| `/admin/vba-code` | GET | Read Module1 VBA code (requires VBProject trust setting) |

---

## RSS function names

`rss.py` references RSS functions by short names (`RssMarket`, `RssBoard`,
`RssOpen`, `RssCancel`, `RssChange`, etc.). If your Excel add-in registers
them under a prefix like `MarketspeedRss.RssMarket`, edit the constants at
the top of `rss.py` to match.

Field names (`現在値`, `最良買気配値`, `買付余力`, etc.) and side / order-type
code numbers come from the Marketspeed2 RSS reference distributed by Rakuten
Securities — see the Excel RSS リファレンス bundled with MS2 and adjust if
your version uses different codes.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `xlwings is not installed` | wheel missing | `pip install xlwings` in the venv |
| `no active Excel workbook found` | `MS2_WORKBOOK_PATH` not set and Excel closed | set `MS2_WORKBOOK_PATH` in `.env` |
| Quote fields all return `"取得中"` | RSS still loading | wait a few seconds; make sure MS2 is logged in |
| MS2 ribbon tab missing in Excel | Excel opened via COM (no add-in) | set `MS2_WORKBOOK_PATH` so bridge uses shell-open |
| 発注不可 after reboot | bridge not yet at 45s mark | wait, or call `/admin/rss-connect` manually |
| Bridge `401` / `403` | wrong / missing bearer | confirm `MS2_BRIDGE_TOKEN` matches on both sides |
| stock-mcp says `Marketspeed2 bridge is not configured` | env missing | set `MS2_BRIDGE_URL` and `MS2_BRIDGE_TOKEN` on the server, restart |

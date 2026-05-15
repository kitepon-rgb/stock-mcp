# Marketspeed2 RSS — order-side settings

Settings live in the **Marketspeed II desktop app** (not in Excel and not in the
RSS add-in). Two distinct setting areas to touch before RSS-driven orders fire
without manual intervention:

## 1. Required to enable order placement at all

> 環境設定 → 注文・約定2 → 取引暗証番号
>
> - 「マーケットスピード II RSSの注文機能を利用する」にチェック
> - 取引暗証番号を登録

Without this, `RssStockOrder` / `RssCancelOrder` / `RssModifyOrder` return the
status string `発注ロック中` regardless of 発注トリガー.

Source: <https://marketspeed.jp/ms2_rss/onlinehelp/ohm_001/ohm_001_06.html>

## 2. Skip the per-order confirmation dialog

> 各種設定 → RSSの設定
>
> - 「注文確認画面の表示」をオフ
> - 「1回あたり発注上限金額」を任意で設定 (推奨)

With "注文確認画面の表示" ON, Marketspeed II pops a confirmation dialog every
time a 発注トリガー=1 formula fires; the RSS cell status stays at `応答待ち`
until the user clicks through. Turn it off to let Excel-driven flow complete
automatically.

Pair with "1回あたり発注上限金額" so that even if Excel mis-fires, the broker
itself caps damage. This is independent of stock-mcp's `STOCK_MCP_MAX_ORDER_QTY`
and `STOCK_MCP_MAX_ORDER_NOTIONAL` (which guard *before* the request leaves
stock-mcp).

Source: <https://marketspeed.jp/ms2_rss/onlinehelp/ohm_002/ohm_002_06.html>

## Status strings to watch (for debugging from the bridge side)

The `RssStockOrder` cell value, after a 発注トリガー=1 fire, takes one of:

| Status | Meaning |
|---|---|
| `待機中` | 発注トリガー is still 0 |
| `応答待ち` | electronic protocol response pending — also stays here while the MS2 confirmation dialog is open |
| `発注済み(発注ID=xxxx)` | success |
| `キャンセル` | user dismissed the MS2 confirmation dialog |
| `入力エラー:〜` | argument validation failed (発注ID NOT consumed) |
| `発注ロック中` | RSS 発注機能 OFF in MS2 (see section 1 above) |
| `発注ID=xxxx は既に使用済みです。` | 発注ID was reused after broker consumed it |

If a placement stalls at `応答待ち` indefinitely, the most common cause is the
MS2 confirmation dialog waiting for a click — flip the setting in section 2.

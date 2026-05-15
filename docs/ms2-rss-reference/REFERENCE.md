# Marketspeed2 RSS Reference (extracted)

Source: `ms2rss_function.pdf` (楽天証券, 2026/3/30 revision).
Full PDF text dumped to `ms2rss_function.txt` for fuzzy search.

This file is the canonical lookup the **bridge** (`tools/ms2-bridge/rss.py`) and
docs should agree with. Do not paraphrase from training data — quote this file.

---

## Function names we actually use

| Purpose | Correct name | Earlier wrong guess |
|---|---|---|
| Quote (国内株式 単項目) | `RssMarket` | (correct) |
| Board (depth) | `RssMarket` w/ depth fields | `RssBoard` ✗ |
| Order list | `RssOrderList` | (correct) |
| Execution / fill list | `RssExecutionList` | `RssTradeList` ✗ |
| Position (cash) | `RssPositionList` | `RssPosition` ✗ |
| Capacity / 余力 | `RssCapacityList` | `RssMargin` ✗ |
| Place cash order | `RssStockOrder` | `RssOpen` ✗ |
| Place margin open | `RssMarginOpenOrder` | — |
| Place margin close | `RssMarginCloseOrder` | — |
| Modify | `RssModifyOrder` | `RssChange` ✗ |
| Cancel | `RssCancelOrder` | `RssCancel` ✗ |
| Tick (歩み値) | `RssTickList` | — |
| Chart | `RssChart` / `RssChartPast` | — |
| Indicator (指数) | `RssIndexMarket` | — |
| FX | `RssFXMarket` | — |

---

## RssMarket(銘柄, 取得項目) — single value lookup

Required fields the bridge uses (subset; full list has 148 fields):

| English key | RSS 取得項目 |
|---|---|
| last_price | 現在値 |
| previous_close | 前日終値 |
| open | 始値 |
| day_high | 高値 |
| day_low | 安値 |
| volume | 出来高 |
| value | 売買代金 |
| vwap | 出来高加重平均 |
| market_cap | 時価総額 |
| lot_size | 単位株数 |
| change | 前日比 |
| change_pct | 前日比率 |
| name | 銘柄名称 |
| market | 市場名称 |
| ts_date | 現在日付 |
| ts_time | 現在値詳細時刻 |
| bid (最良) | 最良買気配値 |
| ask (最良) | 最良売気配値 |
| bid_size (最良) | 最良買気配数量 |
| ask_size (最良) | 最良売気配数量 |
| over_qty | OVER気配数量 |
| under_qty | UNDER気配数量 |
| market_buy_qty | 買成行数量 |
| market_sell_qty | 売成行数量 |

Depth (10 levels) — all via `RssMarket` with these field names:

| Level | Ask price | Ask size | Bid price | Bid size |
|---|---|---|---|---|
| 1 | 最良売気配値1 | 最良売気配数量1 | 最良買気配値1 | 最良買気配数量1 |
| 2 | 最良売気配値2 | 最良売気配数量2 | 最良買気配値2 | 最良買気配数量2 |
| ... | ... | ... | ... | ... |
| 10 | 最良売気配値10 | 最良売気配数量10 | 最良買気配値10 | 最良買気配数量10 |

---

## RssOrderList — 国内株式注文一覧

Signature:
```
=RssOrderList(ヘッダー行, 注文状況, 注文種類, 銘柄コード, 口座区分, 売買,
              信用取引, 信用区分, アルゴ注文, アルゴ注文種類)
```

All args optional. `ヘッダー行` is a cell range pre-filled with the desired
column names; the function returns only those columns, in the same order,
starting at the cell **directly below** the header range.

Filter codes:
- 注文状況: `0`=全て, `1`=訂正取消可能注文, `2`=執行待ち, `3`=執行中, `4`=出来有, `5`=約定,
  `6`=取消中（出来有）, `7`=取消中（出来無）, `8`=取消済（出来無）, `9`=取消済（出来有）,
  `10`=出来ず（出来有）, `11`=出来ず（出来無）, `12`=訂正済, `13`=- (逆指値/アルゴ)
- 注文種類: `0`=全て, `1`=現物, `2`=信用
- 口座区分: `A`=全て, `0`=特定, `1`=一般, `2`=NISA, `3`=旧NISA
- 売買: `0`=全て, `1`=売, `3`=買
- 信用取引: `0`=全て, `1`=信用新規, `2`=信用返済, `3`=現引, `4`=現渡
- 信用区分: `0`=全て, `1`=制度（6ヶ月）, `2`=一般（無期限）, `3`=一般（14日）, `4`=一般（1日）

Returned columns (30, in this exact order when all selected):

| # | 取得項目 | English key | Note |
|---|---|---|---|
| 1 | 注文番号 | order_id | 0 → blank |
| 2 | 受付No | receipt_no | |
| 3 | 通常注文状況 | status_normal | 執行待ち / 執行中 / 出来有 / 約定 / 取消中 / 取消済 / 出来ず / 訂正済 |
| 4 | 逆指値注文状況 | status_stop | 受付 / 待機中 / 市場執行中 / 取消済 |
| 5 | アルゴ注文状況 | status_algo | 監視中 / 執行済 / 取消済 / 出来ず |
| 6 | 銘柄コード | symbol | |
| 7 | 銘柄名称 | name | |
| 8 | 口座区分 | account_type | 一般 / 特定 / NISA / 旧NISA |
| 9 | 市場名称 | exchange | 東証 / 東証（SOR） / JAX / JNX |
| 10 | 信用区分 | margin_class | 制度 / 一般 |
| 11 | 弁済期限 | settlement_term | 6ヶ月 / 無期限 / 14日 / 1日 |
| 12 | 発注/受注日時 | submitted_at | YYYY/MM/DD HH:MM:SS (since 2025-11-22) |
| 13 | 売買 | side | 買付 / 買建 / 買埋 / 売付 / 売建 / 売埋 |
| 14 | 取引 | transaction | 現物 / 信用新規 / 信用返済 |
| 15 | 執行条件 | tif | 本日中 / 今週中 / 期間指定 / 寄付 / 引け / 不成 / 大引不成 |
| 16 | 注文期限 | expiry | YYYYMMDD |
| 17 | 注文数量 | quantity | |
| 18 | 約定数量 | executed_qty | |
| 19 | 注文単価 | price | 0 → 「成行」 |
| 20 | 注文区分 | order_kind | 通常注文 / 逆指値注文 / 逆指値付通常注文 |
| 21 | 逆指値条件 | stop_condition | |
| 22 | セット注文 | is_set | |
| 23 | セット注文条件 | set_condition | |
| 24 | 税区分 | tax_class | 申告 / 源泉あり |
| 25 | 注文失効日時 | failed_at | |
| 26 | 注文失効理由 | failed_reason | |
| 27 | 入力経路 | input_channel | |
| 28 | アルゴ注文条件 | algo_condition | |
| 29 | SOR判定時刻 | sor_decided_at | |
| 30 | SOR判定時主市場情報/対象外理由 | sor_market_info | |

---

## RssExecutionList — 国内株式約定一覧

Signature:
```
=RssExecutionList(ヘッダー行, 注文種類, 銘柄コード, 口座区分, 信用区分, 売買)
```

Returned columns (15):

| # | 取得項目 | English key |
|---|---|---|
| 1 | 約定日 | filled_at (YYYY/MM/DD HH:MM:SS) |
| 2 | 受渡日 | settled_on (YYYYMMDD) |
| 3 | 銘柄コード | symbol |
| 4 | 銘柄名称 | name |
| 5 | 口座区分 | account_type |
| 6 | 市場名称 | exchange |
| 7 | 信用区分 | margin_class |
| 8 | 弁済期限 | settlement_term |
| 9 | 取引 | transaction |
| 10 | 売買 | side |
| 11 | 約定数量 | quantity |
| 12 | 約定単価 | price |
| 13 | 約定代金 | amount |
| 14 | 税区分 | tax_class |
| 15 | 特別空売り料(円) | special_short_fee |

---

## RssPositionList — 保有銘柄一覧 (現物)

Signature:
```
=RssPositionList(ヘッダー行, 銘柄コード, 口座区分)
```

Returned columns (18):

| # | 取得項目 | English key |
|---|---|---|
| 1 | 銘柄コード | symbol |
| 2 | 銘柄名称 | name |
| 3 | 口座区分 | account_type |
| 4 | 保有数量 | quantity |
| 5 | 発注数量 | open_order_qty |
| 6 | 平均取得価額 | avg_price |
| 7 | 時価 | last_price |
| 8 | 前日比 | change |
| 9 | 前日比率 | change_pct |
| 10 | 時価評価額 | market_value |
| 11 | 評価損益額 | unrealized_pnl |
| 12 | 評価損益率 | unrealized_pnl_pct |
| 13 | 銘柄情報等 | notes |
| 14 | JAX時価 | jax_price |
| 15 | JNX時価 | jnx_price |
| 16 | PER | per |
| 17 | PBR | pbr |
| 18 | 配当利回り | dividend_yield |

---

## RssCapacityList — 余力・保証金率

Signature:
```
=RssCapacityList(ヘッダー行)
```

Returned columns (7):

| # | 取得項目 | English key |
|---|---|---|
| 1 | 現物買付可能額 | cash_buying_power |
| 2 | 信用口座_保証金余裕額 | margin_room |
| 3 | 信用口座_信用新規建余力 | margin_buying_power |
| 4 | 信用口座_保証金率（新規建） | margin_ratio_new |
| 5 | 自動振替含む_保証金余裕額 | margin_room_autotransfer |
| 6 | 自動振替含む_信用新規建余力 | margin_buying_power_autotransfer |
| 7 | 自動振替含む_保証金率（新規建） | margin_ratio_autotransfer |

(信用口座未開設なら `-` 文字列が返る)

---

## RssStockOrder — 国内株式 現物注文 (placement)

Signature (20 args):
```
=RssStockOrder(発注ID, 発注トリガー, 銘柄コード, 売買区分, 注文区分, SOR区分,
               注文数量, 価格区分, 注文価格, 執行条件, 注文期限, 口座区分,
               逆指値条件価格, 逆指値条件区分, 逆指値価格区分, 逆指値価格,
               セット注文区分, セット注文価格, セット注文執行条件, セット注文期限)
```

Value codes:

| Arg | Codes |
|---|---|
| 発注ID | unique positive int per Excel session |
| 発注トリガー | `0`/FALSE=待機, `1`/TRUE=発注 (flip from 0 to 1 to fire) |
| 銘柄コード | `7203` または `7203.T` / `.JAX` / `.JNX` |
| 売買区分 | `1`=売り, `3`=買い |
| 注文区分 | `0`=通常注文, `1`=逆指値付通常注文, `2`=逆指値待機注文 |
| SOR区分 | `0`=通常, `1`=SOR |
| 価格区分 | `0`=成行, `1`=指値 (注文区分が 0 or 1 のとき必須) |
| 注文価格 | 成行なら省略 |
| 執行条件 | `1`=本日中, `2`=今週中, `3`=寄付, `4`=引け, `5`=期間指定, `6`=大引不成, `7`=不成 (SOR=1 のとき 3/4 不可) |
| 注文期限 | YYYYMMDD (執行条件=5 のとき必須) |
| 口座区分 | `0`=特定, `1`=一般, `2`=NISA, `3`=旧NISA |
| 逆指値条件区分 | `1`=以上, `2`=以下 |
| 逆指値価格区分 | `0`=成行, `1`=指値 |
| セット注文区分 | `0`=通常, `1`=セット |

Return: a status string in the cell, prefixed with `=>` then one of:
- `待機中` — 発注トリガー=0
- `応答待ち` — 電文応答待ち
- `発注済み(発注ID=xxxx)` — success
- `キャンセル` — confirm dialog cancelled
- `入力エラー:〜` — argument-check failure (発注ID is NOT consumed)
- `(server error)` — server-side error (発注ID IS consumed)
- `発注ロック中` — Marketspeed2 の発注機能 OFF
- `発注ID=xxxx は既に使用済みです。`

Once 発注ID is consumed (= server reached), reusing it yields the "already used" error.

---

## RssModifyOrder — 訂正

```
=RssModifyOrder(発注ID, 発注トリガー, 注文番号, 注文区分, 注文数量, 価格区分,
                注文価格, 執行条件, 注文期限, 逆指値条件価格, 逆指値条件区分,
                逆指値価格区分, 逆指値価格, セット注文価格区分, セット注文価格,
                セット注文執行条件, セット注文期限)
```

Non-modified fields can be omitted. 注文区分 can also be re-typed
(3 = 通常→逆指値付通常, 4 = 逆指値付通常→通常).

## RssCancelOrder — 取消

```
=RssCancelOrder(発注ID, 発注トリガー, 注文番号)
```

---

## List function output layout (critical)

> 1行目: 関数 (the formula cell)
> 2行目: 取得項目 (header row — user-provided or auto-filled)
> 3行目: 取得データ (data rows)

Two ways to use a list function (`Rss*List`):

**A. User-provided headers (deterministic — bridge uses this).**
1. Write desired Japanese header names into row 2 of a chosen range (e.g. N2:U2).
2. Put `=RssOrderList(N2:U2, ...)` in N1.
3. Read data from N3 downward. Columns match user's header order exactly.

**B. Auto-headers.**
1. Put `=RssOrderList()` in N1 with no `ヘッダー行`.
2. Function auto-fills all 30 column names into row 2 starting at N2.
3. Data starts at N3.

Mode A is more robust; Excel's dynamic-array implicit-intersection rewrite
(`=@RssOrderList($N$2:$AQ$2)`) can confuse the bridge in mode B.

---

## Status strings to watch for

These can appear in any RSS cell while data is loading:

- `取得中` — RTD still loading
- `応答待ち` — waiting for protocol response
- `#N/A` — Excel: value not yet available
- `` (empty) — same

The bridge polls with retry until a non-loading value appears.

---

## Source files in this folder

- `ms2rss_function.pdf` — Original PDF (1.3 MB, 38 pages, dated 2026/3/30)
- `ms2rss_function.txt` — pypdf text extraction (1900 lines) for grep/RAG
- `REFERENCE.md` — this file

# 米株リアルタイムデータ源 候補メモ

stock-mcp の米株リアルタイム取得を強化するための候補調査（2026-05-21 時点）。

## 背景: なぜ今リアルタイムが取れないか

現行の無料データ源は米株のリアルタイムにどれも不向き:

| 現行データ源 | 米株リアルタイム性 | 問題 |
|---|---|---|
| Yahoo Finance (yfinance) | 約15分遅延 | 連続アクセスで Yahoo 側に締め出される |
| Alpha Vantage | リアルタイム相当はあるが無料枠が 1分5回・1日25回 | 実用にならない |
| Stooq | 日足のみ（前日終値ベース） | そもそも日中値が出ない |

→ 設定の問題ではなく、データ源選定の問題。リアルタイム対応の源を 1 つ足すのが解。

## データ源候補

### ◎ Finnhub — 採用（実装中）

- 米株の現在値・歩み値・企業ニュースが無料枠でリアルタイム
- 都度問い合わせ 1分60回（Alpha Vantage の 1日25回と桁違い）
- 常時接続のリアルタイム配信も無料枠（同時 50 銘柄まで）
- 既存の `sources/<name>.py` + `@mcp.tool` パターンにそのまま乗る。新規依存なし（`requests` のみ）
- 無料キー: <https://finnhub.io/register>
- リンク: <https://finnhub.io/> / レート上限 <https://finnhub.io/docs/api/rate-limit>

### ○ Alpaca — 発展候補（未着手）

- 米国の手数料無料ネット証券。リアルタイムデータ + **発注API** + ペーパートレードが一体
- 無料枠のリアルタイム配信は IEX 取引所のみ（市場全体の約2%）→ 出来高の薄い銘柄は値が薄い。大型株は実用範囲
- 価値は発注側。現状の発注はマーケットスピード2（日本株）だけ → Alpaca を足せば **米株の発注ブローカー** になり得る（安全装置を通す相応の作業が必要）
- リンク: <https://alpaca.markets/data> / 無料枠の制約 <https://docs.alpaca.markets/us/docs/about-market-data-api>

### △ その他（必要になれば）

- **Polygon.io** — 機関級の品質・カバレッジ。意味のあるリアルタイムは有料（月 $29〜49〜）
- **iTick** — 無料リアルタイムAPI。基本クォートは無制限を謳う。実績は未検証
- **Financial Modeling Prep (FMP)** — リアルタイム値 + 財務データが豊富。無料枠あり

## GitHub / X で見つけた注目リポジトリ

参考・アイデア源。導入候補ではなく「眺める」対象。

- **OpenBB** <https://github.com/OpenBB-finance/OpenBB> — 6.7万スター。Bloomberg端末の無料オープンソース代替。データ源の組み合わせ方の参考
- **maverick-mcp** <https://github.com/wshobson/maverick-mcp> — 個人向け株式分析の同種 MCP サーバ。活発に更新。ツール設計の参考
- **open-stocks-mcp** <https://github.com/Open-Agent-Tools/open-stocks-mcp> — 複数ブローカー（Robinhood / Schwab）対応の MCP サーバ
- **insider-political-alpha-mcp** <https://github.com/apifyforge/insider-political-alpha-mcp> — 米議員の売買報告・内部者届出をスコア化。「有力情報」寄り。小規模・未検証なので中身は要確認
- **chart-library-mcp** <https://github.com/grahammccain/chart-library-mcp> — 過去の類似チャートを検索し「その後どうなったか」を返す

X 上では「OpenBB + Finnhub + yfinance」が無料リアルタイム構成の定番と評価されている。

## 出典

- [Finnhub](https://finnhub.io/) / [レート上限](https://finnhub.io/docs/api/rate-limit)
- [Alpaca Market Data](https://alpaca.markets/data) / [データプラン](https://docs.alpaca.markets/us/docs/about-market-data-api)
- [2026 リアルタイムAPI比較 (Coinmonks)](https://medium.com/coinmonks/the-7-best-real-time-stock-data-apis-for-investors-and-developers-in-2026-in-depth-analysis-61614dc9bf6c)

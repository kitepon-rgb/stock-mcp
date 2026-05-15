# CLAUDE.md -- stock-mcp

このプロジェクトを Claude が触るときの前提と運用ルール。

## このプロジェクトは何か
- 自宅 LAN サーバ `192.168.1.2:39200` で動かす MCP サーバ
- 株式の市場データ・指標計算・**読み書き両対応 (発注含む)** のツール群を MCP として公開する
- 発注ツールを足すときは **以下の安全装置をすべて通す** こと:
  - 2 段フロー: `*_place_order_preview` (注文内容と短命の `confirm_token` を返す) → `*_place_order_confirm(confirm_token)` (本発注)。プレビューなしの直接発注は禁止
  - `confirm_token` は HMAC 署名 + 60 秒 TTL + 1 度限り (使い捨て)
  - 1 注文あたりの数量・概算金額ガード: `STOCK_MCP_MAX_ORDER_QTY=1000`, `STOCK_MCP_MAX_ORDER_NOTIONAL=5000000` (env で上書き可)。超えたら preview 段で拒否
  - 公開接続でも発注可 (本ユーザは外出時に OAuth 経由で使う)。ただし発注ツール登録は `STOCK_MCP_ENABLE_ORDERS=true` 必須、デフォルト false
  - 発注対応ブローカーは **マーケットスピード2 のみ**。kabu は引き続き read-only (`kabu_orders` は注文 *履歴* の取得であって発注ではない)
  - マーケットスピード2 連携は Windows 側 **ブリッジ** 経由。ブリッジ自体にも `MS2_BRIDGE_ENABLE_ORDERS=true` の二重スイッチ
  - ブリッジ ↔ stock-mcp は `MS2_BRIDGE_TOKEN` の bearer 認証で LAN 内通信

## データ源
1. **Yahoo Finance** (`yfinance`) -- グローバル、無料、キー不要
2. **Alpha Vantage** -- 無料 API キー必要（`ALPHA_VANTAGE_API_KEY`）。Rate limit: 5 req/min, 25 req/day（free tier）
3. **Stooq** -- API キー必要（`STOOQ_API_KEY`）。日本株は `7203.jp` 形式、指数は `^n225` 等
4. **kabu.com (kabu Station API)** -- read-only のみ。`KABU_BASE_URL` + `KABU_API_PASSWORD` 要設定。kabu Station プロセスが起動済の Windows マシンにアクセスする前提
5. **マーケットスピード2 (楽天証券)** -- データ取得 + **発注対応** (唯一)。`MS2_BRIDGE_URL` + `MS2_BRIDGE_TOKEN` 要設定。Windows パソコン上で動く [tools/ms2-bridge/](tools/ms2-bridge/) (FastAPI + xlwings + Excel + RSS アドイン) 経由

## ローカル指標・分析
- `indicators.py`: SMA / EMA / RSI / MACD / Bollinger / ATR / ADX / Stochastic を pandas+numpy で実装
- `analysis.py`: サポレジ検出 / フィボリトレース・エクステンション / チャートパターン検出（scipy.find_peaks）
- `charts.py`: ローソク足画像 (mplfinance) と chart-img.com クライアント
- `risk.py`: シナリオ分析 / ポジションサイジング / RR / VaR / ダウ理論判定 / Black-Scholes Greeks / トレード結果シミュレーション
- 外部 TA-Lib / pandas-ta は入れていない（依存最小化、CLAUDE.md 方針）。追加した依存は scipy・matplotlib・mplfinance のみ

## ツール命名の二層構造
- **仕様書名 (Tier 1-4)**: `get_*`, `calc_*`, `detect_*`, `generate_*`, `simulate_*`。
  `docs/stock-mcp-spec.md` §3.1〜§3.4 と一対一。Claude からの主入口。
- **raw アダプタ**: `yahoo_*`, `av_*`, `stooq_*`, `kabu_*`。データ源直結、デバッグ・補完用。
- 仕様書名ツールは raw アダプタ・指標関数を内部で呼ぶ薄いラッパ。両方を並存させ、破壊的変更を避ける。
- 仕様書名ツールは `source='yahoo'|'stooq'` と `history_period` を受け取り、データ源を切り替えられる。

## アーキテクチャ要点
- `server.py` は FastMCP の `streamable-http` transport で起動
- 各データ源は `sources/<name>.py` に純粋関数として隔離（`server.py` は薄いラッパ）
- 設定は `config.py` の `load()` から env を読むだけ。永続化なし
- kabu トークンはプロセス内 dict にキャッシュ（1 時間 TTL）
- 発注ツールは `orders.py` の preview/confirm + HMAC 短命トークン経由。pending dict はプロセス内、再起動で消える (許容)
- マーケットスピード2 連携: Windows パソコン上の独立プロセス `tools/ms2-bridge/` (FastAPI + xlwings) が Excel + RSS アドインを駆動し、stock-mcp は `sources/marketspeed.py` の HTTP クライアントで bearer 認証 LAN 経由で呼ぶ

## 触るときの原則
- データ取得・計算・発注すべて追加できる。発注ツールは上記安全装置をすべて通すこと
- 発注系ツールの命名規約: `<broker>_place_*` / `<broker>_cancel_*` / `<broker>_modify_*` を使い、read-only と一目で区別
- データ源を増やすときは `sources/<name>.py` + `server.py` の `@mcp.tool` 関数を 1 セットで足す
- 既存ツールの引数名は破壊的に変えない（Claude 側の呼び出しが壊れる）
- 認証情報は必ず env から読む。コード中にハードコードしない
- `analyze_ticker` のような複合ツールは「pure な計算」と「I/O」を `_fetch_ohlcv` のように分けたまま保つ
- 発注ツールの追加時はテストハーネスを最小でも 1 つ書く (dry-run でリクエスト JSON が安全装置を通る/弾かれるの両方)

## デプロイ
- ソースはこの WSL リポジトリで編集 → `bash scripts/deploy.sh` で `kite@192.168.1.2:~/stock-mcp/` に rsync
- systemd unit: `scripts/stock-mcp.service` → `/etc/systemd/system/stock-mcp.service`
- 起動: `sudo systemctl restart stock-mcp` / ログ: `journalctl -u stock-mcp -f`

## Claude 登録
- ユーザースコープで HTTP 接続:
  ```
  claude mcp add --transport http stock-mcp http://192.168.1.2:39200/mcp
  ```
- 接続確認: `claude mcp list` -> `stock-mcp Connected`

## トラブル時のチェック順
1. `ssh kite@192.168.1.2 'systemctl status stock-mcp'`
2. `ssh kite@192.168.1.2 'journalctl -u stock-mcp -n 100 --no-pager'`
3. ポート: `nc -z 192.168.1.2 39200 && echo ok`
4. ヘルス: `curl -sS http://192.168.1.2:39200/mcp -H 'Accept: text/event-stream'` -> MCP initialize 応答

## 既知の落とし穴
- Yahoo Finance は予告なくレスポンス構造を変える → 失敗時は `journalctl` で raw 例外を確認
- yfinance `fast_info` は **camelCase キー** (`lastPrice`, `dayHigh`, `marketCap` 等)。snake_case で取りに行くと全 `None` になる (1.3.x で変わった)
- yfinance は短時間に多リクエストすると Yahoo 側 burst 判定でしばらく全 endpoint が 30s タイムアウトする → 一度 `sudo systemctl restart stock-mcp` でセッション/IP-状態をリセットすると復活
- Alpha Vantage の free tier は厳しい。`Note` フィールドで rate limit 通知が返ると `RuntimeError`
- Stooq は **API キー必須** になった (匿名 CSV エンドポイント廃止)。`STOOQ_API_KEY` を env にセット (<https://stooq.com/q/d/?s=aapl.us&get_apikey> で取得)
- Stooq は休日や直近日に空セルを返す → `None` で受けてあるが indicator 計算では NaN になる
- kabu Station は **毎朝トークン rotate**。1 時間 TTL のキャッシュは粗いので 503 が出たらキャッシュ強制無効化を検討
- `simulate_trade` は yfinance 由来の tz-aware index と naive な `entry_date/exit_date` を比較するため、`Timestamp` 側を index の tz に揃えてから比較する (修正済み)

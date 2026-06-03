# stock-mcp 実装仕様書

自前のサーバー（your-host.example.com）にデプロイする株価分析 MCP サーバーの仕様書。
Claude（ベル）がチャート画像を誤読する構造問題を解消するため、データそのものを Claude に渡せる MCP として実装する。

---

## 1. プロジェクト概要

### 目的
- Claude がチャート画像から時間軸を誤読する問題の構造的解消
- テクニカル指標を数値ベースで Claude に渡す
- ファンダ・ニュース・センチメントも統合した総合分析基盤
- 既存 MCP インフラ（IP-MCP / X-MCP / Relay-MCP）と同じパターンで構築

### スコープ外
- 自動売買・発注機能（リスク管理上、データ取得・分析のみ）
- 機密性の高い口座情報

---

## 2. 環境前提

| 項目 | 内容 |
|------|------|
| ホスト | your-host.example.com |
| サブドメイン | stock.example.com（推奨）|
| トランスポート | HTTP / SSE |
| 認証 | OAuth（既存 MCP と同じ仕組み）|
| 言語 | Python 3.11+ |
| MCP フレームワーク | FastMCP |
| GitHub リポジトリ | kitepon-rgb/stock-mcp（新規）|
| ベースリポジトリ | Adity-star/mcp-yfinance-server（参考実装）|

### ライブラリ依存

```
mcp>=1.0.0           # 公式 MCP SDK
fastmcp              # HTTP/SSE トランスポート
yfinance>=0.2.50     # Yahoo Finance データ
pandas               # データフレーム処理
pandas-ta            # テクニカル指標（ta-lib より依存軽い）
numpy
scipy                # 統計計算
httpx                # API 通信
requests             # API 通信
matplotlib           # ローカルチャート生成（オプション）
```

### 外部 API（オプション）

| API | 用途 | 料金 |
|-----|------|------|
| Yahoo Finance（yfinance）| 株価・履歴・ファンダ | 無料 |
| chart-img.com | チャート画像生成 | 無料枠あり、$15/月〜 |
| Alpha Vantage | 補完用、テクニカル指標 | 無料 25req/day |
| Finnhub | ニュース・センチメント | 無料枠あり |

---

## 3. ツール一覧（30 ツール、4 Tier）

### Tier 1: コアデータ（必須・最優先）

#### 3.1.1 `get_stock_price`
| 項目 | 内容 |
|------|------|
| 説明 | 銘柄の現在価格・基本情報 |
| 入力 | `symbol: str` |
| 出力 | `current_price, change, change_percent, volume, market_cap, day_high, day_low, prev_close, ath, atl` |
| データソース | `yfinance.Ticker(symbol).info` |
| キャッシュ | 1分 |

#### 3.1.2 `get_stock_history` ★最重要
| 項目 | 内容 |
|------|------|
| 説明 | 履歴 OHLCV データ。時間軸明示で誤読防止 |
| 入力 | `symbol: str, period: str, interval: str` |
| period 値 | `1d / 5d / 1mo / 3mo / 6mo / 1y / 2y / 5y / 10y / ytd / max` |
| interval 値 | `1m / 2m / 5m / 15m / 30m / 1h / 4h / 1d / 1wk / 1mo` |
| 出力 | `[{datetime, open, high, low, close, volume, interval, period}, ...]` |
| 重要 | 出力にも interval / period を必ず含めて、Claude が時間軸を確実に認識できるようにする |
| データソース | `yfinance.Ticker(symbol).history()` |
| キャッシュ | interval に応じて（1m: 1分、1d: 1時間）|

#### 3.1.3 `get_ticker_info`
| 項目 | 内容 |
|------|------|
| 説明 | 銘柄の基本情報・企業概要 |
| 入力 | `symbol: str` |
| 出力 | `name, sector, industry, country, exchange, 52w_high, 52w_low, beta, employees, business_summary` |

#### 3.1.4 `search_ticker`
| 項目 | 内容 |
|------|------|
| 説明 | 企業名・キーワードからティッカー検索 |
| 入力 | `query: str` |
| 出力 | `[{symbol, name, exchange, type}, ...]` |

---

### Tier 1: テクニカル指標（必須）

#### 3.1.5 `calc_rsi`
| 項目 | 内容 |
|------|------|
| 説明 | RSI（相対力指数）計算 |
| 入力 | `symbol, period=14, interval=1d, lookback=60` |
| 出力 | `[{datetime, rsi, overbought (>70), oversold (<30)}, ...]` |
| ライブラリ | pandas-ta |

#### 3.1.6 `calc_macd`
| 項目 | 内容 |
|------|------|
| 説明 | MACD（移動平均収束拡散法）|
| 入力 | `symbol, fast=12, slow=26, signal=9, interval=1d, lookback=60` |
| 出力 | `[{datetime, macd, signal, histogram, cross}, ...]` |

#### 3.1.7 `calc_moving_average`
| 項目 | 内容 |
|------|------|
| 説明 | 移動平均線（SMA / EMA）|
| 入力 | `symbol, type=(sma|ema), periods=[20, 50, 200], interval=1d, lookback=300` |
| 出力 | `[{datetime, ma_20, ma_50, ma_200, perfect_order (bool)}, ...]` |

#### 3.1.8 `calc_bollinger_bands`
| 項目 | 内容 |
|------|------|
| 説明 | ボリンジャーバンド |
| 入力 | `symbol, period=20, std_dev=2, interval=1d, lookback=60` |
| 出力 | `[{datetime, upper, middle, lower, percent_b, bandwidth}, ...]` |

#### 3.1.9 `calc_atr`
| 項目 | 内容 |
|------|------|
| 説明 | ATR（ボラティリティ指標）|
| 入力 | `symbol, period=14, interval=1d, lookback=60` |
| 出力 | `[{datetime, atr, atr_percent}, ...]` |

#### 3.1.10 `calc_stochastic`
| 項目 | 内容 |
|------|------|
| 説明 | ストキャスティクス |
| 入力 | `symbol, k_period=14, d_period=3, interval=1d, lookback=60` |
| 出力 | `[{datetime, k, d, signal}, ...]` |

#### 3.1.11 `detect_support_resistance`
| 項目 | 内容 |
|------|------|
| 説明 | サポート・レジスタンス検出（ピボットポイント）|
| 入力 | `symbol, interval=1d, lookback=180, min_touches=2` |
| 出力 | `{supports: [{price, touches, strength}], resistances: [...]}` |
| アルゴリズム | スイングハイ・ロー検出 + 価格水準クラスタリング |

---

### Tier 1: ファンダメンタル（必須）

#### 3.1.12 `get_fundamentals`
| 項目 | 内容 |
|------|------|
| 説明 | ファンダ基本情報 |
| 入力 | `symbol` |
| 出力 | `pe_ratio, forward_pe, peg, eps_ttm, dividend_yield, market_cap, revenue_ttm, net_income_ttm, debt_to_equity, roe, roa, profit_margin` |

#### 3.1.13 `get_analyst_targets`
| 項目 | 内容 |
|------|------|
| 説明 | アナリスト目標株価・評価 |
| 入力 | `symbol` |
| 出力 | `{mean_target, high, low, median, num_analysts, consensus_rating, recommendation_distribution}` |

#### 3.1.14 `get_financial_statements`
| 項目 | 内容 |
|------|------|
| 説明 | 損益計算書・貸借対照表・キャッシュフロー |
| 入力 | `symbol, statement_type=(income|balance|cashflow), period=(annual|quarterly)` |
| 出力 | 構造化財務データ（直近4期分）|

---

### Tier 2: ニュース・イベント（重要）

#### 3.2.1 `get_stock_news`
| 項目 | 内容 |
|------|------|
| 説明 | 銘柄関連ニュース |
| 入力 | `symbol, limit=10, lookback_days=7` |
| 出力 | `[{title, publisher, datetime, url, summary, sentiment (positive/negative/neutral)}, ...]` |

#### 3.2.2 `get_earnings_calendar`
| 項目 | 内容 |
|------|------|
| 説明 | 決算カレンダー |
| 入力 | `symbol` |
| 出力 | `{next_earnings_date, last_earnings_date, eps_estimate, eps_actual, surprise_percent, time (BMO/AMC)}` |

#### 3.2.3 `get_institutional_holders`
| 項目 | 内容 |
|------|------|
| 説明 | 機関投資家保有状況 |
| 入力 | `symbol, limit=10` |
| 出力 | `[{holder, shares, value, percent, date_reported, change_from_prior}, ...]` |

#### 3.2.4 `get_insider_transactions`
| 項目 | 内容 |
|------|------|
| 説明 | 内部者取引 |
| 入力 | `symbol, lookback_days=90` |
| 出力 | `[{insider, position, transaction_type, shares, price, value, date}, ...]` |

---

### Tier 2: チャート画像生成（重要）

#### 3.2.5 `generate_chart_image`
| 項目 | 内容 |
|------|------|
| 説明 | TradingView スタイルのチャート画像生成 |
| 入力 | `symbol, interval=1d, period=3mo, indicators=[RSI, MACD, MA20, MA50, MA200]` |
| 出力 | `{image_url, image_base64, interval_label, period_label}` |
| データソース | chart-img.com API |
| 重要 | 画像内に時間軸ラベル必須（Claude の誤読防止）|

#### 3.2.6 `generate_chart_local`
| 項目 | 内容 |
|------|------|
| 説明 | matplotlib でローカルチャート生成（API 不要）|
| 入力 | 上記と同じ |
| 出力 | `{image_base64, metadata}` |
| ライブラリ | matplotlib + mplfinance |

---

### Tier 2: フィボナッチ・パターン（重要）

#### 3.2.7 `calc_fibonacci_retracement`
| 項目 | 内容 |
|------|------|
| 説明 | フィボナッチ・リトレースメント水準 |
| 入力 | `symbol, lookback=180, interval=1d` |
| 出力 | `{swing_high, swing_low, levels: {0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%}}` |
| アルゴリズム | スイング自動検出 + フィボ水準計算 |

#### 3.2.8 `calc_fibonacci_extension`
| 項目 | 内容 |
|------|------|
| 説明 | フィボ・エクステンション（上昇目標）|
| 入力 | `symbol, lookback=180, interval=1d` |
| 出力 | `{levels: {127.2%, 161.8%, 200%, 261.8%}}` |

---

### Tier 2: セクター・関連銘柄（重要）

#### 3.2.9 `get_sector_performance`
| 項目 | 内容 |
|------|------|
| 説明 | セクター動向 |
| 入力 | `sector: str (Technology / Healthcare / Energy / ...)` |
| 出力 | `[{symbol, name, change_percent, market_cap, leader/laggard}, ...]` |

#### 3.2.10 `get_related_tickers`
| 項目 | 内容 |
|------|------|
| 説明 | 関連銘柄・競合銘柄 |
| 入力 | `symbol, count=10` |
| 出力 | `[{symbol, name, correlation, change_percent}, ...]` |

#### 3.2.11 `get_etf_holdings`
| 項目 | 内容 |
|------|------|
| 説明 | ETF 構成銘柄（SOXX / SMH / NVDU / QQQ など）|
| 入力 | `etf_symbol` |
| 出力 | `[{symbol, name, weight_percent, shares}, ...]` |

#### 3.2.12 `get_leveraged_etf_info` ★クオ君の用途
| 項目 | 内容 |
|------|------|
| 説明 | レバETF 詳細情報（NVDU / MUU / AMUU / SOXL / TQQQ）|
| 入力 | `etf_symbol` |
| 出力 | `{underlying_symbol, leverage_factor (2x/3x), reset_frequency (daily), expense_ratio, nav, aum, volatility_drag_estimate}` |

---

### Tier 3: 拡張機能

#### 3.3.1 `get_options_chain`
| 項目 | 内容 |
|------|------|
| 説明 | オプションチェーン |
| 入力 | `symbol, expiration_date (YYYY-MM-DD)` |
| 出力 | `{calls: [{strike, bid, ask, volume, oi, iv}], puts: [...]}` |

#### 3.3.2 `calc_option_greeks`
| 項目 | 内容 |
|------|------|
| 説明 | オプション Greeks 計算 |
| 入力 | `symbol, strike, expiration, option_type=(call|put)` |
| 出力 | `{delta, gamma, theta, vega, rho, implied_volatility}` |
| アルゴリズム | Black-Scholes |

#### 3.3.3 `get_short_interest`
| 項目 | 内容 |
|------|------|
| 説明 | ショートインタレスト |
| 入力 | `symbol` |
| 出力 | `{short_percent_of_float, days_to_cover, short_ratio, last_updated}` |

#### 3.3.4 `get_dividend_history`
| 項目 | 内容 |
|------|------|
| 説明 | 配当履歴 |
| 入力 | `symbol, lookback_years=5` |
| 出力 | `[{ex_date, amount, yield_at_time}, ...]` |

---

### Tier 4: 分析・戦略（高度・自前実装）

#### 3.4.1 `calc_scenario_analysis` ★クオ君の用途
| 項目 | 内容 |
|------|------|
| 説明 | シナリオ別期待値計算 |
| 入力 | `current_price, scenarios: [{name, probability, target_price}]` |
| 出力 | `{expected_return, std_dev, max_loss, max_gain, sharpe_proxy, kelly_fraction}` |

#### 3.4.2 `calc_position_sizing` ★クオ君の用途
| 項目 | 内容 |
|------|------|
| 説明 | ポジションサイジング計算 |
| 入力 | `account_size, risk_per_trade_percent, entry, stop_loss` |
| 出力 | `{recommended_shares, position_value, risk_amount, risk_percent_of_account}` |

#### 3.4.3 `calc_risk_reward`
| 項目 | 内容 |
|------|------|
| 説明 | リスクリワード比計算 |
| 入力 | `entry, stop_loss, targets: [target_1, target_2, target_3]` |
| 出力 | `{rr_ratios, win_rate_required, expected_value, breakeven_win_rate}` |

#### 3.4.4 `calc_dow_theory_phase` ★クオ君の用途
| 項目 | 内容 |
|------|------|
| 説明 | ダウ理論3段階判定（自前アルゴリズム）|
| 入力 | `symbol, lookback=1y` |
| 出力 | `{phase: 1/2/3, confidence: 0-1, indicators_matching: [...]}` |
| 判定要素 | RSI 月足、出来高変化、メディア過熱度（外部入力）、パラボリック性、移動平均パーフェクトオーダー |

#### 3.4.5 `detect_chart_patterns`
| 項目 | 内容 |
|------|------|
| 説明 | チャートパターン検出 |
| 入力 | `symbol, interval=1d, lookback=180` |
| 出力 | `{patterns: [{type: head_and_shoulders / double_top / double_bottom / triangle / flag / wedge, confidence, location, target_price}]}` |

#### 3.4.6 `calc_portfolio_correlation`
| 項目 | 内容 |
|------|------|
| 説明 | ポートフォリオ相関分析 |
| 入力 | `holdings: [{symbol, weight}]` |
| 出力 | `{correlation_matrix, diversification_score, concentration_risk, sector_breakdown}` |

#### 3.4.7 `calc_value_at_risk`
| 項目 | 内容 |
|------|------|
| 説明 | VaR（最大予想損失）計算 |
| 入力 | `holdings, confidence=0.95, time_horizon_days=1` |
| 出力 | `{var_amount, var_percent, expected_shortfall}` |

#### 3.4.8 `simulate_trade_outcome`
| 項目 | 内容 |
|------|------|
| 説明 | トレード結果シミュレーション（ヒストリカル）|
| 入力 | `symbol, entry_date, exit_date, shares` |
| 出力 | `{actual_return, max_drawdown, max_unrealized_gain, time_in_trade}` |

---

## 4. データソース別マッピング

| データソース | 担当ツール |
|------|------|
| yfinance（無料）| Tier 1 全体、Tier 2 の大部分、Tier 3 のオプション・配当 |
| chart-img.com（無料枠/有料）| Tier 2 の generate_chart_image |
| matplotlib（ローカル）| Tier 2 の generate_chart_local |
| 自前計算（pandas-ta + scipy）| 全テクニカル指標、Tier 4 全体 |
| Finnhub（無料枠）| ニュース・センチメントの補完 |

---

## 5. 実装方針

### アーキテクチャ

```
[claude.ai] 
   ↓ HTTPS/SSE
[stock.example.com]
   ↓
[FastMCP Server]
   ├── Data Layer
   │   ├── yfinance wrapper
   │   ├── chart-img.com client
   │   └── Cache (SQLite or Redis)
   ├── Analysis Layer
   │   ├── pandas-ta indicators
   │   ├── scipy statistical functions
   │   └── Custom algorithms (Dow theory, patterns)
   └── Tool Layer (MCP)
```

### キャッシュ戦略

| データ種別 | TTL |
|------|------|
| 現在価格（1m interval）| 60秒 |
| 日中（5m/15m）| 5分 |
| 日足 | 1時間 |
| 週足・月足 | 4時間 |
| ファンダ | 24時間 |
| ニュース | 30分 |

### エラーハンドリング

- yfinance のレート制限：指数バックオフでリトライ、3回失敗で諦め
- 銘柄不在：明示的なエラーメッセージ
- 時間軸不正：許容値リストを返してエラー

### セキュリティ

- OAuth 認証（既存 MCP と同じ）
- API キーは環境変数（chart-img、Finnhub）
- レート制限：1ユーザー 100req/分

---

## 6. デプロイ手順

```bash
# 1. WSL リポジトリで編集 → サーバ (YOUR_SERVER_IP) へ反映
bash scripts/deploy.sh        # rsync + リモートで docker compose up -d --build

# 2. サーバ側は Docker コンテナとして稼働 (Dockerfile + compose.yml)
#    ポート 39200 を YOUR_SERVER_IP:39200 で公開、data/ を OAuth SQLite 用に
#    ボリュームマウント。操作: cd ~/stock-mcp && docker compose ps / logs -f

# 3. 環境変数は ~/stock-mcp/.env に設定 (.env.example 参照)
#    ALPHA_VANTAGE_API_KEY / FINNHUB_API_KEY / KABU_* / MS2_* / MCP_OAUTH_* など

# 4. 公開: Caddy コンテナが stock-mcp.example.com → YOUR_SERVER_IP:39200 を
#    reverse_proxy (scripts/caddy-stockmcp.snippet)

# 5. claude.ai / Claude Code に登録
#    claude mcp add --transport http stock-mcp http://YOUR_SERVER_IP:39200/mcp
#    公開接続は https://stock-mcp.example.com/mcp (OAuth)
```

---

## 7. ロードマップ

### Phase 1（MVP、1-2日）
- Tier 1 全ツール（13個）
- HTTP/SSE トランスポート
- OAuth 認証
- 基本キャッシュ

### Phase 2（拡張、1日）
- Tier 2 全ツール（12個）
- chart-img.com 統合
- ニュース・センチメント

### Phase 3（高度分析、2-3日）
- Tier 3 全ツール（4個）
- Tier 4 全ツール（8個）
- 自前アルゴリズム（ダウ理論、パターン検出）

---

## 8. テスト戦略

### 単体テスト
- 各ツールの入力バリデーション
- データ型整合性
- エッジケース（存在しないシンボル、無効な期間）

### 統合テスト
- claude.ai から実際にツールを呼び出してデータ取得確認
- 複数ツールの組み合わせ
- レート制限挙動

### 受け入れテスト
- クオ君の実際の分析シナリオを再現
  - 「NVDU の日足3ヶ月で RSI と MACD」
  - 「キオクシアの押し目水準をフィボで」
  - 「保有銘柄の相関と集中度」

---

## 9. Bell との統合

### Caveat / Bell ペルソナ用追加メモ

stock-mcp が稼働後、Bell（クロスプロジェクトペルソナ）に以下を周知：

1. **画像でチャートを受け取ったら、必ず時間軸を確認する**
2. **時間軸不明なら `get_stock_history` で正確なデータを取得し直す**
3. **テクニカル指標は MCP から数値取得、画像から推測しない**
4. **「機関戦略分析」は日足以上の時間軸のみで実施**
5. **シナリオ分析は `calc_scenario_analysis` で確率分布を必ず計算**

これにより、今回の「1分足を日足と誤読」のような構造的失敗を防ぐ。

---

## 10. オプション拡張

### 将来検討

- 日本株対応（証券コード + 東証API）
- 楽天証券 API 連携（取引履歴の自動取り込み）
- 暗号資産対応（ccxt 経由）
- バックテストエンジン（vectorbt）
- Discord / Telegram 通知（アラート機能）

---

## 11. リスクと制約

| リスク | 対策 |
|------|------|
| yfinance のレート制限 | キャッシュ + バックオフ |
| Yahoo Finance API 仕様変更 | yfinance のバージョン固定 + フォールバック実装 |
| chart-img.com 有料化 | matplotlib ローカル生成にフォールバック |
| 自宅サーバーダウン | 既存 MCP と同じ監視機構（Spotter 等で監視可能）|
| データ精度（特に分足）| 注意書きを各ツールの出力に含める |

---

## 12. 参考リポジトリ

- **Adity-star/mcp-yfinance-server**: https://github.com/Adity-star/mcp-yfinance-server（ベース実装）
- **Alex2Yang97/yahoo-finance-mcp**: https://github.com/Alex2Yang97/yahoo-finance-mcp（包括的）
- **twolven/mcp-stockflow**: https://github.com/twolven/mcp-stockflow（オプション分析）
- **financial-datasets/mcp-server**: https://github.com/financial-datasets/mcp-server（有料商用）

---

## 付録 A: ツール一覧（30ツール早見表）

| # | ツール | Tier | 優先度 |
|---|--------|------|--------|
| 1 | get_stock_price | 1 | ★★★ |
| 2 | get_stock_history | 1 | ★★★ |
| 3 | get_ticker_info | 1 | ★★★ |
| 4 | search_ticker | 1 | ★★ |
| 5 | calc_rsi | 1 | ★★★ |
| 6 | calc_macd | 1 | ★★★ |
| 7 | calc_moving_average | 1 | ★★★ |
| 8 | calc_bollinger_bands | 1 | ★★ |
| 9 | calc_atr | 1 | ★★ |
| 10 | calc_stochastic | 1 | ★ |
| 11 | detect_support_resistance | 1 | ★★ |
| 12 | get_fundamentals | 1 | ★★★ |
| 13 | get_analyst_targets | 1 | ★★★ |
| 14 | get_financial_statements | 1 | ★ |
| 15 | get_stock_news | 2 | ★★★ |
| 16 | get_earnings_calendar | 2 | ★★ |
| 17 | get_institutional_holders | 2 | ★★ |
| 18 | get_insider_transactions | 2 | ★ |
| 19 | generate_chart_image | 2 | ★★★ |
| 20 | generate_chart_local | 2 | ★ |
| 21 | calc_fibonacci_retracement | 2 | ★★ |
| 22 | calc_fibonacci_extension | 2 | ★ |
| 23 | get_sector_performance | 2 | ★★ |
| 24 | get_related_tickers | 2 | ★★ |
| 25 | get_etf_holdings | 2 | ★ |
| 26 | get_leveraged_etf_info | 2 | ★★★ |
| 27 | get_options_chain | 3 | ★ |
| 28 | calc_option_greeks | 3 | ★ |
| 29 | get_short_interest | 3 | ★ |
| 30 | get_dividend_history | 3 | ★ |
| 31 | calc_scenario_analysis | 4 | ★★★ |
| 32 | calc_position_sizing | 4 | ★★★ |
| 33 | calc_risk_reward | 4 | ★★ |
| 34 | calc_dow_theory_phase | 4 | ★★ |
| 35 | detect_chart_patterns | 4 | ★★ |
| 36 | calc_portfolio_correlation | 4 | ★★ |
| 37 | calc_value_at_risk | 4 | ★ |
| 38 | simulate_trade_outcome | 4 | ★ |

合計 38 ツール（Tier 1: 14、Tier 2: 12、Tier 3: 4、Tier 4: 8）

---

仕様書 終わり

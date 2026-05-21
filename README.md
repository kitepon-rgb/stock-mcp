# stock-mcp

Read-only MCP server exposing stock market data and technical analysis as tools.
Designed for the home LAN at `192.168.1.2`, reachable from Claude Code via the
Streamable HTTP transport.

## Tools

Spec-named Tier 1 tools (`docs/stock-mcp-spec.md` §3.1) are the preferred entrypoints
for Claude. Lower-level source adapters and the composite `analyze_ticker` are also
exposed for direct access.

| Category | Tools |
|---|---|
| Core data (spec T1) | `get_stock_price`, `get_stock_history`★, `get_ticker_info`, `search_ticker` |
| Indicators (spec T1) | `calc_rsi`, `calc_macd`, `calc_moving_average`, `calc_bollinger_bands`, `calc_atr`, `calc_stochastic` |
| Levels (spec T1) | `detect_support_resistance` |
| Fundamentals (spec T1) | `get_fundamentals`, `get_analyst_targets`, `get_financial_statements` |
| News & events (spec T2) | `get_stock_news`, `get_earnings_calendar`, `get_institutional_holders`, `get_insider_transactions` |
| Charts (spec T2) | `generate_chart_image` (chart-img.com), `generate_chart_local` (mplfinance, no key) |
| Fibonacci (spec T2) | `calc_fibonacci_retracement`, `calc_fibonacci_extension` |
| Sector / ETF (spec T2) | `get_sector_performance`, `get_related_tickers`, `get_etf_holdings`, `get_leveraged_etf_info` |
| Options / shorts (spec T3) | `get_options_chain`, `calc_option_greeks` (Black-Scholes), `get_short_interest`, `get_dividend_history` |
| Strategy / risk (spec T4) | `calc_scenario_analysis`, `calc_position_sizing`, `calc_risk_reward`, `calc_dow_theory_phase`, `detect_chart_patterns`, `calc_portfolio_correlation`, `calc_value_at_risk`, `simulate_trade_outcome` |
| Yahoo Finance (raw) | `yahoo_quote`, `yahoo_history`, `yahoo_info`, `yahoo_news`, `yahoo_actions`, `yahoo_financials` |
| Alpha Vantage | `av_quote`, `av_intraday`, `av_daily`, `av_indicator` |
| Finnhub | `finnhub_quote` (real-time US stock quotes) |
| Stooq | `stooq_history` |
| kabu.com (read-only) | `kabu_board`, `kabu_symbol_info`, `kabu_positions`, `kabu_orders` |
| Local composite | `analyze_ticker` (history + RSI / MACD / BB / SMA / EMA / ATR / ADX) |

★ `get_stock_history` always tags every record with `interval` and `period`
so Claude cannot misread the time axis (the design driver of this server).

No order-execution tools are exposed.

## Layout

```
src/stock_mcp/
  server.py            # FastMCP entrypoint; tool registration
  config.py            # env-var loader
  indicators.py        # local technical indicators (pure pandas/numpy)
  analysis.py          # higher-level analytics (support/resistance, fibonacci, chart patterns)
  charts.py            # chart images: mplfinance (local) + chart-img.com (remote)
  risk.py              # Tier 4: scenario / sizing / RR / VaR / Dow theory / option Greeks
  sources/
    yahoo.py           # yfinance adapter (quote / history / news / fundamentals / earnings / holders / options / dividends / sector)
    alpha_vantage.py   # Alpha Vantage REST adapter
    finnhub.py         # Finnhub REST adapter (real-time US stock quotes)
    stooq.py           # Stooq CSV adapter
    kabu.py            # kabu Station REST adapter (read-only)
scripts/
  deploy.sh            # rsync source + docker compose up on remote
  stock-mcp.service    # legacy systemd unit (superseded by Docker)
docs/
  REGISTER.md          # how to register with Claude
Dockerfile             # container image (python:3.12-slim)
compose.yml            # container service: port 39200, data/ volume
.env.example
pyproject.toml
```

## Deploy

Runs as a Docker container on the home server (`Dockerfile` + `compose.yml`).

```bash
REMOTE=kite@192.168.1.2 bash scripts/deploy.sh
```

`deploy.sh` rsyncs the source and runs `docker compose up -d --build` on the
server. Edit `~/stock-mcp/.env` there to set API keys (`ALPHA_VANTAGE_API_KEY`,
`FINNHUB_API_KEY`, and if used `KABU_BASE_URL` / `KABU_API_PASSWORD`), then
`cd ~/stock-mcp && docker compose up -d` to apply.

## Register with Claude

```bash
claude mcp add --transport http stock-mcp http://192.168.1.2:39200/mcp
```

See `docs/REGISTER.md` for scope details and verification commands.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `STOCK_MCP_HOST` | `0.0.0.0` | Bind address (LAN-reachable by default) |
| `STOCK_MCP_PORT` | `39200` | TCP port |
| `ALPHA_VANTAGE_API_KEY` | _(unset)_ | Required for `av_*` tools |
| `FINNHUB_API_KEY` | _(unset)_ | Required for `finnhub_quote` (real-time US quotes) |
| `CHART_IMG_API_KEY` | _(unset)_ | Required for `generate_chart_image` (local fallback: `generate_chart_local`) |
| `KABU_BASE_URL` | _(unset)_ | e.g. `http://127.0.0.1:18080` |
| `KABU_API_PASSWORD` | _(unset)_ | kabu Station API password |
| `KABU_PRODUCTION` | `false` | `true` = live-trading port |

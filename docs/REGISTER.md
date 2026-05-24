# Register stock-mcp with Claude

## Quick register (user scope, HTTP transport)

```bash
claude mcp add --transport http stock-mcp http://192.168.1.2:39200/mcp
```

Verify:

```bash
claude mcp list
# Expected: stock-mcp  Connected
```

## Scope options

| Scope | Flag | Where stored |
|---|---|---|
| Local (default) | _(none)_ | per-project, per-user |
| Project (committed) | `--scope project` | `.mcp.json` at the project root, shared with team |
| User | `--scope user` | `~/.claude.json`, available across all your projects |

For a personal home server you almost always want **user scope**:

```bash
claude mcp add --scope user --transport http stock-mcp http://192.168.1.2:39200/mcp
```

## Smoke test from Claude

After registering, in a Claude session:

> stock-mcp の yahoo_quote で NVDA の最新気配を取って

Then progressively:

> analyze_ticker で 7203.jp(stooq) を 1y / RSI と MACD だけ計算して

## Remove or update

```bash
claude mcp remove stock-mcp
claude mcp add --transport http stock-mcp http://192.168.1.2:39200/mcp
```

---

## claude.ai (web / desktop / iOS) — Custom Connector + OAuth

The LAN URL above only works from a Claude Code CLI inside the LAN. To use
stock-mcp from **claude.ai** (web), the desktop app, or the iOS app, the
server has to be publicly reachable over HTTPS with OAuth 2.1.

### One-time server setup

1. **DNS** — point `stockmcp.kitepon.dev` to the home IP (already done).
2. **Caddy** — append `scripts/caddy-stockmcp.snippet` to
   `/home/kite/license-server/Caddyfile` on `192.168.1.2`, then:

   ```bash
   ssh kite@192.168.1.2 'docker exec caddy caddy reload --config /etc/caddy/Caddyfile'
   ```

   Mirrors the existing `ipmcp.kitepon.dev` block (same Caddy pattern).
3. **stock-mcp env** — on the server, edit `~/stock-mcp/.env`:

   ```bash
   MCP_OAUTH_ISSUER_URL=https://stockmcp.kitepon.dev
   MCP_OAUTH_MASTER_PASSWORD=<pick a strong password>
   MCP_OAUTH_DB_PATH=data/oauth.db
   STOCK_MCP_ALLOWED_HOSTS=192.168.1.2:39200,192.168.1.2,stockmcp.kitepon.dev
   STOCK_MCP_ALLOWED_ORIGINS=http://192.168.1.2:39200,https://stockmcp.kitepon.dev
   ```

4. **Restart**:

   ```bash
   ssh kite@192.168.1.2 'cd ~/stock-mcp && docker compose up -d'
   ```

5. **Smoke test** the OAuth discovery endpoint:

   ```bash
   curl -sS https://stockmcp.kitepon.dev/.well-known/oauth-authorization-server | jq .
   ```

   It should return a JSON document with `issuer`, `authorization_endpoint`, `token_endpoint`, etc.

### Register from claude.ai (web)

1. Settings → Connectors → **Add custom connector**
2. URL: `https://stockmcp.kitepon.dev/mcp`
3. Claude.ai performs DCR + OAuth redirect → you land on the stock-mcp
   `/consent` page → enter the master password → approved.
4. The connector turns green and stock-mcp tools become callable from
   claude.ai chats.

Token + DCR client registrations persist in `~/stock-mcp/data/oauth.db`, so
restarting the service does not log Claude out.

### LAN-only mode (skip OAuth)

If you only need Claude Code CLI inside the LAN, leave
`MCP_OAUTH_ISSUER_URL` and `MCP_OAUTH_MASTER_PASSWORD` empty. The server
starts without authentication and the Caddy subdomain is unnecessary.

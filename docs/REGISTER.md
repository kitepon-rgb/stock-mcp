# Register stock-mcp with Claude

## Quick register (user scope, HTTP transport)

```bash
claude mcp add --transport http stock-mcp http://YOUR_SERVER_IP:39200/mcp
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
claude mcp add --scope user --transport http stock-mcp http://YOUR_SERVER_IP:39200/mcp
```

## Smoke test from Claude

After registering, in a Claude session:

> stock-mcp の yahoo_quote で NVDA の最新気配を取って

Then progressively:

> analyze_ticker で 7203.jp(stooq) を 1y / RSI と MACD だけ計算して

## Remove or update

```bash
claude mcp remove stock-mcp
claude mcp add --transport http stock-mcp http://YOUR_SERVER_IP:39200/mcp
```

---

## claude.ai (web / desktop / iOS) — Custom Connector + OAuth

The LAN URL above only works from a Claude Code CLI inside the LAN. To use
stock-mcp from **claude.ai** (web), the desktop app, or the iOS app, the
server has to be publicly reachable over HTTPS with OAuth 2.1.

### One-time server setup

1. **DNS** — point `stock-mcp.example.com` at your server's public IP.
2. **Caddy** — append `scripts/caddy-stockmcp.snippet` to
   `/path/to/Caddyfile` on `YOUR_SERVER_IP`, then:

   ```bash
   ssh youruser@YOUR_SERVER_IP 'docker exec caddy caddy reload --config /etc/caddy/Caddyfile'
   ```

   Mirrors the existing `another-mcp.example.com` block (same Caddy pattern).
3. **stock-mcp env** — on the server, edit `~/stock-mcp/.env`:

   ```bash
   MCP_OAUTH_ISSUER_URL=https://stock-mcp.example.com
   MCP_OAUTH_MASTER_PASSWORD=<pick a strong password>
   MCP_OAUTH_DB_PATH=data/oauth.db
   STOCK_MCP_ALLOWED_HOSTS=YOUR_SERVER_IP:39200,YOUR_SERVER_IP,stock-mcp.example.com
   STOCK_MCP_ALLOWED_ORIGINS=http://YOUR_SERVER_IP:39200,https://stock-mcp.example.com
   ```

4. **Restart**:

   ```bash
   ssh youruser@YOUR_SERVER_IP 'cd ~/stock-mcp && docker compose up -d'
   ```

5. **Smoke test** the OAuth discovery endpoint:

   ```bash
   curl -sS https://stock-mcp.example.com/.well-known/oauth-authorization-server | jq .
   ```

   It should return a JSON document with `issuer`, `authorization_endpoint`, `token_endpoint`, etc.

### Register from claude.ai (web)

1. Settings → Connectors → **Add custom connector**
2. URL: `https://stock-mcp.example.com/mcp`
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

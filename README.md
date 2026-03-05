# ibkr-flex-mcp

MCP server for [Interactive Brokers Flex Web Service](https://www.interactivebrokers.com/en/software/am/am/reports/activityflexqueries.htm) — read-only portfolio data for AI assistants.

No TWS or IB Gateway required. Just a Flex Query token.

## Tools

| Tool | Description |
|---|---|
| `get_portfolio` | Positions, P&L, allocation %, and cash balances |
| `get_lots` | Individual purchase lots (for tax/CGT analysis) |
| `get_cash` | Cash balances, deposits, withdrawals, commissions, dividends |

## Setup

### 1. Create IBKR Flex Query & Token

1. IBKR Client Portal → Performance & Reports → Flex Queries
2. Create an Activity Flex Query with Open Positions + Cash Report sections
3. Enable Flex Web Service → generate a token

### 2. Configure credentials

Create `~/.ibkr_flex_env`:

```
IBKR_FLEX_TOKEN=your_token_here
IBKR_FLEX_QUERY_ID=your_query_id
```

### 3. Add to MCP client

For Kiro CLI (`~/.kiro/settings/mcp.json`):

```json
{
  "ibkr-portfolio": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/ibkr-flex-mcp", "server.py"]
  }
}
```

Or install and run:

```json
{
  "ibkr-portfolio": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/mcp-tools-hub/ibkr-flex-mcp", "ibkr-flex-mcp"]
  }
}
```

## License

MIT

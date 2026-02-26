# ibkr-mcp-server

MCP server for [Interactive Brokers](https://www.interactivebrokers.com/) — expose your portfolio data, market quotes, trading, and analysis to any MCP-compatible AI client.

Built for international/EU investors. Supports UCITS/PRIIPs-aware analysis, multi-currency portfolios, and Estonian/EU tax context.

## Features

### 12 Tools

| Tool | Type | Description |
|------|------|-------------|
| `get_positions` | read | Current positions with P&L |
| `get_account_summary` | read | NAV, buying power, margin |
| `get_nav` | read | Quick net asset value check |
| `get_open_orders` | read | List pending orders |
| `get_quote` | read | Real-time quote for any symbol |
| `get_historical_bars` | read | OHLCV bars (configurable period/size) |
| `search_contracts` | read | Find IBKR contracts by symbol/name |
| `portfolio_snapshot` | read | Full analysis with weights and concentration warnings |
| `concentration_check` | read | Flag positions exceeding a weight threshold |
| `transition_plan` | read | Calculate sell/buy plan for target allocation |
| `place_order` | write | Place a limit order (safety-gated) |
| `cancel_order` | write | Cancel an open order (safety-gated) |

All read tools are annotated with `readOnlyHint=True`. Write tools are annotated with `destructiveHint=True` and require `SAFETY_PAPER_ONLY=false`.

### 4 Resources

| URI | Description |
|-----|-------------|
| `ibkr://positions` | Live positions list |
| `ibkr://account/summary` | Account summary |
| `ibkr://orders/open` | Open orders |
| `ibkr://portfolio/snapshot` | Full portfolio analysis |

### 4 Prompts

| Prompt | Description |
|--------|-------------|
| `portfolio-review` | Analyze portfolio for risks and opportunities |
| `rebalance-plan` | Create a rebalance plan toward target allocation |
| `risk-check` | Check concentration risk and exposure |
| `tax-analysis` | Analyze tax implications (EU/Estonian context) |

## Prerequisites

- **IB Gateway** running (via Docker or standalone)
- **Python 3.12+** with [uv](https://docs.astral.sh/uv/)
- **IBKR account** with API access enabled

### IB Gateway via Docker

```bash
docker run -d \
  --name ib-gateway \
  -p 4003:4003 \
  -p 5900:5900 \
  -e TWS_USERID=your_username \
  -e TWS_PASSWORD=your_password \
  -e TRADING_MODE=live \
  -e TWS_PORT=4003 \
  ghcr.io/gnzsnz/ib-gateway:stable
```

Approve the 2FA prompt on IBKR Mobile after starting.

## Install

```bash
git clone https://github.com/deividi86/ibkr-mcp-server.git
cd ibkr-mcp-server
cp .env.example .env
# Edit .env with your gateway host/port
uv sync
```

## Configure in Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ibkr-mcp-server", "ibkr-mcp"]
    }
  }
}
```

## Configure in Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ibkr-mcp-server", "ibkr-mcp"]
    }
  }
}
```

## Usage

Once configured, ask your AI client things like:

- "What are my current positions?"
- "Analyze my portfolio risk"
- "Create a rebalance plan toward 70% VWCE, 20% AGGG, 10% IBC1"
- "Get a quote for VWCE"
- "Search for Vanguard UCITS ETFs"

## Safety

Trading is disabled by default. The `SAFETY_PAPER_ONLY=true` environment variable blocks `place_order` and `cancel_order`. All read-only tools work regardless.

To enable live trading:

```bash
SAFETY_PAPER_ONLY=false
```

Even with trading enabled, only **limit orders** are supported — no market orders.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IB_GATEWAY_HOST` | `127.0.0.1` | IB Gateway host |
| `IB_GATEWAY_PORT` | `4003` | IB Gateway port |
| `IB_ACCOUNT` | (empty) | Account ID (optional, uses first managed account) |
| `SAFETY_PAPER_ONLY` | `true` | Block trading tools when true |

## Development

```bash
uv sync --dev
uv run pytest -v
```

## License

MIT

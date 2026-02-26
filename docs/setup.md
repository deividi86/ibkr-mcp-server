# Setup Guide

## Prerequisites

1. **IB Gateway** running via Docker (recommended: `gnzsnz/ib-gateway`)
2. **Python 3.12+** with `uv` package manager
3. **IBKR account** with API access enabled

## IB Gateway Docker

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

After starting, approve the 2FA prompt on the IBKR Mobile app.

## Install

```bash
cd ibkr-mcp-server
cp .env.example .env
# Edit .env with your gateway host/port and account ID

uv sync
```

## Run standalone

```bash
uv run ibkr-mcp
```

## Configure in Claude Code

Add to `~/.claude/settings.json`:

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

## Safety

By default, `SAFETY_PAPER_ONLY=true` which blocks all trading tools (`place_order`, `cancel_order`).
All read-only tools (positions, quotes, analysis) work regardless.

To enable live trading, set `SAFETY_PAPER_ONLY=false` in your `.env` file.

## Run tests

```bash
uv run pytest -v
```

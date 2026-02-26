from __future__ import annotations

from typing import Any

from ib_async import Stock
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from ibkr_mcp.server import AppContext, mcp

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False)


@mcp.tool(annotations=READ_ONLY)
async def get_quote(
    symbol: str,
    currency: str = "USD",
    exchange: str = "SMART",
    ctx: Context = None,
) -> dict[str, Any]:
    """Get a real-time quote for a stock or ETF.

    Args:
        symbol: Ticker symbol (e.g. "MSFT", "VWCE")
        currency: Currency of the contract (default: USD)
        exchange: Exchange to route to (default: SMART)

    Returns last price, close, bid, and ask.
    """
    app: AppContext = ctx.request_context.lifespan_context
    contract = Stock(symbol, exchange, currency)
    return await app.broker.get_market_price(contract)


@mcp.tool(annotations=READ_ONLY)
async def get_historical_bars(
    symbol: str,
    duration: str = "1 M",
    bar_size: str = "1 day",
    currency: str = "USD",
    exchange: str = "SMART",
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """Get historical OHLCV bars for a stock or ETF.

    Args:
        symbol: Ticker symbol
        duration: Time span (e.g. "1 M", "3 M", "1 Y", "5 D")
        bar_size: Bar size (e.g. "1 day", "1 hour", "5 mins")
        currency: Currency of the contract (default: USD)
        exchange: Exchange to route to (default: SMART)

    Returns a list of bars with date, open, high, low, close, volume.
    """
    app: AppContext = ctx.request_context.lifespan_context
    contract = Stock(symbol, exchange, currency)
    return await app.broker.get_historical_bars(contract, duration, bar_size)


@mcp.tool(annotations=READ_ONLY)
async def search_contracts(pattern: str, ctx: Context = None) -> list[dict[str, Any]]:
    """Search for IBKR contracts by symbol or name.

    Args:
        pattern: Search string (e.g. "VWCE", "Vanguard", "MSFT")

    Returns matching contracts with conId, symbol, type, exchange, and currency.
    Use the conId to reference specific contracts in other operations.
    """
    app: AppContext = ctx.request_context.lifespan_context
    matches = await app.broker.search_contracts(pattern)
    return [m.to_dict() for m in matches]

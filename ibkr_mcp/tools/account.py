from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from ibkr_mcp.server import AppContext, mcp

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False)


@mcp.tool(annotations=READ_ONLY)
async def get_positions(ctx: Context) -> list[dict[str, Any]]:
    """Get all current portfolio positions with P&L, weights, and market values.

    Returns a list of positions including symbol, shares, average cost,
    market price, market value, unrealized/realized P&L, and P&L percentage.
    """
    app: AppContext = ctx.request_context.lifespan_context
    positions = await app.broker.get_positions()
    return [p.to_dict() for p in positions]


@mcp.tool(annotations=READ_ONLY)
async def get_account_summary(ctx: Context) -> dict[str, Any]:
    """Get account summary including NAV, buying power, available funds, and P&L.

    Returns net asset value (NAV), available funds, buying power,
    unrealized/realized P&L, and base currency.
    """
    app: AppContext = ctx.request_context.lifespan_context
    summary = await app.broker.get_account_summary()
    return summary.to_dict()


@mcp.tool(annotations=READ_ONLY)
async def get_nav(ctx: Context) -> dict[str, float]:
    """Get the current net asset value (NAV) — quick portfolio value check.

    Returns just the NAV number for fast lookups without full account details.
    """
    app: AppContext = ctx.request_context.lifespan_context
    summary = await app.broker.get_account_summary()
    return {"nav": round(summary.nav, 2), "currency": summary.currency}


@mcp.tool(annotations=READ_ONLY)
async def get_open_orders(ctx: Context) -> list[dict[str, Any]]:
    """List all currently open/pending orders.

    Returns order ID, symbol, action (BUY/SELL), quantity, order type,
    limit price, and status for each open order.
    """
    app: AppContext = ctx.request_context.lifespan_context
    orders = await app.broker.get_open_orders()
    return [o.to_dict() for o in orders]

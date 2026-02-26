from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from ibkr_mcp.server import AppContext, mcp

DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)


@mcp.tool(annotations=DESTRUCTIVE)
async def place_order(
    symbol: str,
    action: str,
    quantity: float,
    limit_price: float,
    currency: str = "USD",
    exchange: str = "SMART",
    ctx: Context = None,
) -> dict[str, Any]:
    """Place a limit order to buy or sell a stock/ETF.

    IMPORTANT: This places a REAL order. Only limit orders are supported (no market orders).
    The server must have SAFETY_PAPER_ONLY=false to enable live trading.

    Args:
        symbol: Ticker symbol (e.g. "VWCE", "MSFT")
        action: "BUY" or "SELL"
        quantity: Number of shares
        limit_price: Limit price for the order
        currency: Currency (default: USD)
        exchange: Exchange (default: SMART)

    Returns order confirmation with order_id and status.
    """
    app: AppContext = ctx.request_context.lifespan_context

    if app.config.safety_paper_only:
        return {
            "error": "Trading is disabled. Set SAFETY_PAPER_ONLY=false to enable live trading."
        }

    if action not in ("BUY", "SELL"):
        return {"error": f"Invalid action '{action}'. Must be 'BUY' or 'SELL'."}

    if quantity <= 0:
        return {"error": "Quantity must be positive."}

    if limit_price <= 0:
        return {"error": "Limit price must be positive."}

    return await app.broker.place_limit_order(
        symbol=symbol,
        action=action,
        quantity=quantity,
        limit_price=limit_price,
        currency=currency,
        exchange=exchange,
    )


@mcp.tool(annotations=DESTRUCTIVE)
async def cancel_order(order_id: int, ctx: Context = None) -> dict[str, Any]:
    """Cancel an open order by its order ID.

    Args:
        order_id: The order ID to cancel (from get_open_orders or place_order)

    Returns cancellation status.
    """
    app: AppContext = ctx.request_context.lifespan_context

    if app.config.safety_paper_only:
        return {
            "error": "Trading is disabled. Set SAFETY_PAPER_ONLY=false to enable live trading."
        }

    return await app.broker.cancel_order(order_id)

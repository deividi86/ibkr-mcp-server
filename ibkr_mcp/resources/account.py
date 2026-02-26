from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import Context

from ibkr_mcp.server import AppContext, mcp


@mcp.resource("ibkr://positions")
async def positions_resource(ctx: Context) -> str:
    """Current portfolio positions with P&L and market values."""
    app: AppContext = ctx.request_context.lifespan_context
    positions = await app.broker.get_positions()
    return json.dumps([p.to_dict() for p in positions], indent=2)


@mcp.resource("ibkr://account/summary")
async def account_summary_resource(ctx: Context) -> str:
    """Account summary: NAV, buying power, available funds, and P&L."""
    app: AppContext = ctx.request_context.lifespan_context
    summary = await app.broker.get_account_summary()
    return json.dumps(summary.to_dict(), indent=2)


@mcp.resource("ibkr://orders/open")
async def open_orders_resource(ctx: Context) -> str:
    """Currently open/pending orders."""
    app: AppContext = ctx.request_context.lifespan_context
    orders = await app.broker.get_open_orders()
    return json.dumps([o.to_dict() for o in orders], indent=2)


@mcp.resource("ibkr://portfolio/snapshot")
async def portfolio_snapshot_resource(ctx: Context) -> str:
    """Full portfolio analysis with positions, weights, and concentration warnings."""
    app: AppContext = ctx.request_context.lifespan_context
    positions = await app.broker.get_positions()
    summary = await app.broker.get_account_summary()
    nav = summary.nav or 1.0

    analyzed = []
    for pos in positions:
        weight = pos.market_value / nav
        analyzed.append({
            **pos.to_dict(),
            "weight_pct": round(weight * 100, 2),
        })

    analyzed.sort(key=lambda p: p["weight_pct"], reverse=True)

    snapshot = {
        "positions": analyzed,
        "summary": summary.to_dict(),
        "total_positions": len(analyzed),
    }
    return json.dumps(snapshot, indent=2)

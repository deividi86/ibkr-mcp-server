from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from ibkr_mcp.server import AppContext, mcp

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False)


@mcp.tool(annotations=READ_ONLY)
async def portfolio_snapshot(ctx: Context) -> dict[str, Any]:
    """Get a full portfolio analysis: positions with weights, NAV, P&L, and concentration data.

    Returns positions sorted by weight with percentage of NAV, account summary,
    and flags any positions exceeding 25% concentration.
    """
    app: AppContext = ctx.request_context.lifespan_context
    positions = await app.broker.get_positions()
    summary = await app.broker.get_account_summary()
    nav = summary.nav or 1.0

    analyzed = []
    warnings = []
    for pos in positions:
        weight = pos.market_value / nav
        entry = {
            **pos.to_dict(),
            "weight_pct": round(weight * 100, 2),
        }
        analyzed.append(entry)
        if weight > 0.25:
            warnings.append(
                f"{pos.symbol}: {round(weight * 100, 1)}% of NAV (exceeds 25% limit)"
            )

    analyzed.sort(key=lambda p: p["weight_pct"], reverse=True)

    return {
        "positions": analyzed,
        "summary": summary.to_dict(),
        "total_positions": len(analyzed),
        "concentration_warnings": warnings,
    }


@mcp.tool(annotations=READ_ONLY)
async def concentration_check(
    threshold_pct: float = 25.0,
    ctx: Context = None,
) -> dict[str, Any]:
    """Check portfolio for concentration risk — positions exceeding a weight threshold.

    Args:
        threshold_pct: Maximum allowed weight percentage (default: 25%)

    Returns positions that exceed the threshold with their current weights.
    """
    app: AppContext = ctx.request_context.lifespan_context
    positions = await app.broker.get_positions()
    summary = await app.broker.get_account_summary()
    nav = summary.nav or 1.0
    threshold = threshold_pct / 100.0

    flagged = []
    for pos in positions:
        weight = pos.market_value / nav
        if weight > threshold:
            flagged.append({
                "symbol": pos.symbol,
                "weight_pct": round(weight * 100, 2),
                "market_value": round(pos.market_value, 2),
                "threshold_pct": threshold_pct,
                "excess_pct": round((weight - threshold) * 100, 2),
            })

    return {
        "nav": round(nav, 2),
        "threshold_pct": threshold_pct,
        "flagged_positions": flagged,
        "is_concentrated": len(flagged) > 0,
    }


@mcp.tool(annotations=READ_ONLY)
async def transition_plan(
    targets: dict[str, float],
    ctx: Context = None,
) -> dict[str, Any]:
    """Calculate a sell/buy transition plan from current holdings to target allocation.

    Does NOT execute any trades — just calculates what would need to happen.

    Args:
        targets: Target allocation as {symbol: weight} where weights sum to 1.0
                 Example: {"VWCE": 0.7, "AGGG": 0.2, "IBC1": 0.1}

    Returns sell orders for current positions and buy orders for target ETFs,
    with estimated values and capital gains impact.
    """
    app: AppContext = ctx.request_context.lifespan_context
    positions = await app.broker.get_positions()
    summary = await app.broker.get_account_summary()

    total_weight = sum(targets.values())
    if abs(total_weight - 1.0) > 0.01:
        return {"error": f"Target weights must sum to 1.0, got {total_weight}"}

    sells = []
    total_proceeds = 0.0
    total_capital_gains = 0.0

    for pos in positions:
        if pos.shares <= 0:
            continue
        sells.append({
            "action": "SELL",
            "symbol": pos.symbol,
            "shares": pos.shares,
            "estimated_price": round(pos.market_price, 4),
            "estimated_value": round(pos.market_value, 2),
            "capital_gain": round(pos.unrealized_pnl, 2),
        })
        total_proceeds += pos.market_value
        total_capital_gains += pos.unrealized_pnl

    buys = []
    for symbol, weight in targets.items():
        target_value = total_proceeds * weight
        buys.append({
            "action": "BUY",
            "symbol": symbol,
            "target_weight": weight,
            "estimated_value": round(target_value, 2),
        })

    return {
        "sells": sells,
        "buys": buys,
        "total_proceeds": round(total_proceeds, 2),
        "total_capital_gains": round(total_capital_gains, 2),
        "nav": round(summary.nav, 2),
        "note": "This is a read-only plan. No orders have been placed.",
    }

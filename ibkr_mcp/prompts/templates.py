from __future__ import annotations

from mcp.server.fastmcp.prompts.base import Message, UserMessage

from ibkr_mcp.server import mcp


@mcp.prompt()
def portfolio_review() -> list[Message]:
    """Analyze my current IBKR portfolio for risks and opportunities."""
    return [
        UserMessage(
            "Please analyze my current IBKR portfolio. Use the portfolio_snapshot tool "
            "to get the full picture, then:\n\n"
            "1. Review each position's weight and P&L\n"
            "2. Flag any concentration risks (>25% in one position)\n"
            "3. Identify tax-inefficient holdings (high-dividend US stocks are "
            "tax-inefficient for EU/Estonian companies due to 15% withholding)\n"
            "4. Suggest opportunities for rebalancing\n"
            "5. Note any positions that should be reviewed for stop-losses or profit targets"
        ),
    ]


@mcp.prompt()
def rebalance_plan(target_allocation: str = "VWCE:0.7,AGGG:0.2,IBC1:0.1") -> list[Message]:
    """Create a rebalance plan toward a target UCITS ETF allocation."""
    return [
        UserMessage(
            f"I want to rebalance my portfolio toward this target allocation: "
            f"{target_allocation}\n\n"
            "Please:\n"
            "1. Use portfolio_snapshot to see current holdings\n"
            "2. Use transition_plan to calculate the sell/buy plan\n"
            "3. Estimate the capital gains impact of selling current positions\n"
            "4. Suggest a phased approach (don't sell everything at once)\n"
            "5. Remember: selling and reinvesting is tax-free inside an Estonian company "
            "(0% CIT on retained profits), so the only concern is market timing, "
            "not tax friction"
        ),
    ]


@mcp.prompt()
def risk_check() -> list[Message]:
    """Check portfolio for concentration risk, stop-losses, and exposure analysis."""
    return [
        UserMessage(
            "Please perform a risk check on my IBKR portfolio:\n\n"
            "1. Use concentration_check to flag overweight positions (>25%)\n"
            "2. Use portfolio_snapshot for the full picture\n"
            "3. Check for:\n"
            "   - Single-stock concentration risk\n"
            "   - Sector concentration (are all holdings in tech?)\n"
            "   - Currency exposure (USD vs EUR)\n"
            "   - Dividend tax drag (US stocks paying dividends to an Estonian company)\n"
            "4. Suggest any immediate actions needed"
        ),
    ]


@mcp.prompt()
def tax_analysis(
    positions: str = "all",
    jurisdiction: str = "Estonia",
) -> list[Message]:
    """Analyze tax implications of selling positions in a given jurisdiction."""
    return [
        UserMessage(
            f"Analyze the tax implications of selling {positions} in my portfolio, "
            f"considering {jurisdiction} tax rules:\n\n"
            "1. Use portfolio_snapshot to get current positions and unrealized P&L\n"
            "2. For Estonian company (OÜ) context:\n"
            "   - 0% CIT on retained/reinvested profits\n"
            "   - ~26% CIT only on distributions (24% CIT + 2% defense tax)\n"
            "   - US withholding on dividends: 15% (treaty rate), non-creditable\n"
            "   - Capital gains on selling US stocks: 0% US tax for foreign entities\n"
            "3. Calculate the tax impact of selling vs holding\n"
            "4. Recommend the most tax-efficient approach\n"
            "5. Note: accumulating UCITS ETFs avoid all dividend withholding"
        ),
    ]

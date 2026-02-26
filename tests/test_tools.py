from __future__ import annotations

import pytest

from ibkr_mcp.tools.account import get_account_summary, get_nav, get_open_orders, get_positions
from ibkr_mcp.tools.market import get_historical_bars, get_quote, search_contracts
from ibkr_mcp.tools.trading import cancel_order, place_order
from ibkr_mcp.tools.analysis import concentration_check, portfolio_snapshot, transition_plan


# --- Account tools ---


@pytest.mark.asyncio
async def test_get_positions(mock_ctx):
    result = await get_positions(mock_ctx)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["symbol"] == "MSFT"
    assert "market_value" in result[0]
    assert "pnl_pct" in result[0]


@pytest.mark.asyncio
async def test_get_account_summary(mock_ctx):
    result = await get_account_summary(mock_ctx)
    assert result["nav"] == 147527.00
    assert result["currency"] == "USD"
    assert "buying_power" in result


@pytest.mark.asyncio
async def test_get_nav(mock_ctx):
    result = await get_nav(mock_ctx)
    assert result["nav"] == 147527.00


@pytest.mark.asyncio
async def test_get_open_orders(mock_ctx):
    result = await get_open_orders(mock_ctx)
    assert isinstance(result, list)
    assert len(result) == 0


# --- Market tools ---


@pytest.mark.asyncio
async def test_get_quote(mock_ctx):
    result = await get_quote("MSFT", ctx=mock_ctx)
    assert result["symbol"] == "MSFT"
    assert result["last"] == 426.80


@pytest.mark.asyncio
async def test_get_historical_bars(mock_ctx):
    result = await get_historical_bars("MSFT", ctx=mock_ctx)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["close"] == 426.8


@pytest.mark.asyncio
async def test_search_contracts(mock_ctx):
    result = await search_contracts("MSFT", ctx=mock_ctx)
    assert len(result) == 1
    assert result[0]["symbol"] == "MSFT"
    assert result[0]["con_id"] == 272093


# --- Trading tools ---


@pytest.mark.asyncio
async def test_place_order_blocked_by_safety(mock_ctx):
    result = await place_order("VWCE", "BUY", 10, 95.0, ctx=mock_ctx)
    assert "error" in result
    assert "SAFETY_PAPER_ONLY" in result["error"]


@pytest.mark.asyncio
async def test_place_order_invalid_action(mock_ctx):
    mock_ctx.request_context.lifespan_context.config.safety_paper_only = False
    result = await place_order("VWCE", "HOLD", 10, 95.0, ctx=mock_ctx)
    assert "error" in result
    assert "Invalid action" in result["error"]


@pytest.mark.asyncio
async def test_place_order_success(mock_ctx):
    mock_ctx.request_context.lifespan_context.config.safety_paper_only = False
    result = await place_order("VWCE", "BUY", 10, 95.0, ctx=mock_ctx)
    assert result["order_id"] == 42
    assert result["status"] == "Submitted"


@pytest.mark.asyncio
async def test_cancel_order_blocked_by_safety(mock_ctx):
    result = await cancel_order(42, ctx=mock_ctx)
    assert "error" in result


@pytest.mark.asyncio
async def test_cancel_order_success(mock_ctx):
    mock_ctx.request_context.lifespan_context.config.safety_paper_only = False
    result = await cancel_order(42, ctx=mock_ctx)
    assert result["status"] == "cancel_requested"


# --- Analysis tools ---


@pytest.mark.asyncio
async def test_portfolio_snapshot(mock_ctx):
    result = await portfolio_snapshot(mock_ctx)
    assert "positions" in result
    assert "summary" in result
    assert result["total_positions"] == 3
    # MSFT should be first (highest weight)
    assert result["positions"][0]["symbol"] == "MSFT"
    assert "weight_pct" in result["positions"][0]


@pytest.mark.asyncio
async def test_concentration_check(mock_ctx):
    result = await concentration_check(threshold_pct=25.0, ctx=mock_ctx)
    assert "flagged_positions" in result
    # MSFT is ~31% so should be flagged at 25% threshold
    flagged_symbols = [p["symbol"] for p in result["flagged_positions"]]
    assert "MSFT" in flagged_symbols
    assert result["is_concentrated"] is True


@pytest.mark.asyncio
async def test_concentration_check_high_threshold(mock_ctx):
    result = await concentration_check(threshold_pct=50.0, ctx=mock_ctx)
    assert result["is_concentrated"] is False
    assert len(result["flagged_positions"]) == 0


@pytest.mark.asyncio
async def test_transition_plan(mock_ctx):
    targets = {"VWCE": 0.7, "AGGG": 0.2, "IBC1": 0.1}
    result = await transition_plan(targets, ctx=mock_ctx)
    assert "sells" in result
    assert "buys" in result
    assert len(result["sells"]) == 3
    assert len(result["buys"]) == 3
    assert result["note"].startswith("This is a read-only plan")


@pytest.mark.asyncio
async def test_transition_plan_bad_weights(mock_ctx):
    targets = {"VWCE": 0.5, "AGGG": 0.2}
    result = await transition_plan(targets, ctx=mock_ctx)
    assert "error" in result

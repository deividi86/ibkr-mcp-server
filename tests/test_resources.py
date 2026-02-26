from __future__ import annotations

import json

import pytest

from ibkr_mcp.resources.account import (
    account_summary_resource,
    open_orders_resource,
    portfolio_snapshot_resource,
    positions_resource,
)


@pytest.mark.asyncio
async def test_positions_resource(mock_ctx):
    result = await positions_resource(mock_ctx)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["symbol"] == "MSFT"


@pytest.mark.asyncio
async def test_account_summary_resource(mock_ctx):
    result = await account_summary_resource(mock_ctx)
    data = json.loads(result)
    assert data["nav"] == 147527.00


@pytest.mark.asyncio
async def test_open_orders_resource(mock_ctx):
    result = await open_orders_resource(mock_ctx)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_portfolio_snapshot_resource(mock_ctx):
    result = await portfolio_snapshot_resource(mock_ctx)
    data = json.loads(result)
    assert "positions" in data
    assert "summary" in data
    assert data["total_positions"] == 3

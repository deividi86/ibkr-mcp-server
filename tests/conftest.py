from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from ibkr_mcp.broker import AccountSummary, Broker, ContractMatch, OpenOrder, Position
from ibkr_mcp.config import ServerConfig
from ibkr_mcp.server import AppContext


MOCK_POSITIONS = [
    Position(
        symbol="MSFT",
        sec_type="STK",
        exchange="NASDAQ",
        currency="USD",
        shares=107,
        avg_cost=380.50,
        market_price=426.80,
        market_value=45667.60,
        unrealized_pnl=4954.10,
        realized_pnl=0,
        con_id=272093,
    ),
    Position(
        symbol="ARCC",
        sec_type="STK",
        exchange="NASDAQ",
        currency="USD",
        shares=1643,
        avg_cost=19.50,
        market_price=19.27,
        market_value=31660.61,
        unrealized_pnl=-377.89,
        realized_pnl=0,
        con_id=4812047,
    ),
    Position(
        symbol="NVDA",
        sec_type="STK",
        exchange="NASDAQ",
        currency="USD",
        shares=67,
        avg_cost=195.00,
        market_price=185.45,
        market_value=12425.15,
        unrealized_pnl=-639.85,
        realized_pnl=0,
        con_id=4815747,
    ),
]

MOCK_SUMMARY = AccountSummary(
    nav=147527.00,
    available_funds=12500.00,
    buying_power=25000.00,
    unrealized_pnl=13750.00,
    realized_pnl=0,
    currency="USD",
)


@pytest.fixture
def mock_config() -> ServerConfig:
    return ServerConfig(
        ib_gateway_host="127.0.0.1",
        ib_gateway_port=4003,
        ib_account="U16261491",
        safety_paper_only=True,
    )


@pytest.fixture
def mock_broker(mock_config: ServerConfig) -> Broker:
    broker = Broker(mock_config)
    broker.get_positions = AsyncMock(return_value=MOCK_POSITIONS)
    broker.get_account_summary = AsyncMock(return_value=MOCK_SUMMARY)
    broker.get_open_orders = AsyncMock(return_value=[])
    broker.get_market_price = AsyncMock(return_value={
        "symbol": "MSFT",
        "last": 426.80,
        "close": 425.00,
        "bid": 426.75,
        "ask": 426.85,
    })
    broker.get_historical_bars = AsyncMock(return_value=[
        {"date": "2026-02-25", "open": 420.0, "high": 428.0, "low": 419.0, "close": 426.8, "volume": 1500000},
    ])
    broker.search_contracts = AsyncMock(return_value=[
        ContractMatch(con_id=272093, symbol="MSFT", sec_type="STK", exchange="NASDAQ", currency="USD"),
    ])
    broker.place_limit_order = AsyncMock(return_value={
        "order_id": 42, "symbol": "VWCE", "action": "BUY", "quantity": 10, "limit_price": 95.0, "status": "Submitted",
    })
    broker.cancel_order = AsyncMock(return_value={"order_id": 42, "status": "cancel_requested"})
    return broker


@pytest.fixture
def app_context(mock_broker: Broker, mock_config: ServerConfig) -> AppContext:
    return AppContext(broker=mock_broker, config=mock_config)


@pytest.fixture
def mock_ctx(app_context: AppContext) -> MagicMock:
    """Create a mock MCP Context that provides lifespan_context."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app_context
    return ctx

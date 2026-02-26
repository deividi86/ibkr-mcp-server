from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from ib_async import IB, Contract, LimitOrder, Order, PortfolioItem, Stock, Trade, util

from ibkr_mcp.config import ServerConfig

log = logging.getLogger(__name__)


@dataclass
class Position:
    symbol: str
    sec_type: str
    exchange: str
    currency: str
    shares: float
    avg_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    con_id: int = 0

    @property
    def pnl_pct(self) -> float:
        cost_basis = self.avg_cost * self.shares
        if cost_basis == 0:
            return 0.0
        return self.unrealized_pnl / cost_basis

    @classmethod
    def from_portfolio_item(cls, item: PortfolioItem) -> Position:
        return cls(
            symbol=item.contract.symbol,
            sec_type=item.contract.secType,
            exchange=item.contract.exchange or item.contract.primaryExchange or "",
            currency=item.contract.currency,
            shares=item.position,
            avg_cost=item.averageCost,
            market_price=item.marketPrice,
            market_value=item.marketValue,
            unrealized_pnl=item.unrealizedPNL,
            realized_pnl=item.realizedPNL,
            con_id=item.contract.conId,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "sec_type": self.sec_type,
            "exchange": self.exchange,
            "currency": self.currency,
            "shares": self.shares,
            "avg_cost": round(self.avg_cost, 4),
            "market_price": round(self.market_price, 4),
            "market_value": round(self.market_value, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "pnl_pct": round(self.pnl_pct * 100, 2),
            "con_id": self.con_id,
        }


@dataclass
class AccountSummary:
    nav: float
    available_funds: float
    buying_power: float
    unrealized_pnl: float
    realized_pnl: float
    currency: str = "USD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "nav": round(self.nav, 2),
            "available_funds": round(self.available_funds, 2),
            "buying_power": round(self.buying_power, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "currency": self.currency,
        }


@dataclass
class ContractMatch:
    con_id: int
    symbol: str
    sec_type: str
    exchange: str
    currency: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "con_id": self.con_id,
            "symbol": self.symbol,
            "sec_type": self.sec_type,
            "exchange": self.exchange,
            "currency": self.currency,
            "description": self.description,
        }


@dataclass
class OpenOrder:
    order_id: int
    symbol: str
    action: str
    quantity: float
    order_type: str
    limit_price: float | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "action": self.action,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "limit_price": self.limit_price,
            "status": self.status,
        }


class Broker:
    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._ib = IB()

    async def connect(self) -> None:
        log.info(
            "Connecting to IB Gateway at %s:%s",
            self._config.ib_gateway_host,
            self._config.ib_gateway_port,
        )
        await self._ib.connectAsync(
            host=self._config.ib_gateway_host,
            port=self._config.ib_gateway_port,
            clientId=1,
            readonly=self._config.safety_paper_only,
        )
        log.info("Connected — managed accounts: %s", self._ib.managedAccounts())

    async def disconnect(self) -> None:
        if self._ib.isConnected():
            self._ib.disconnect()
            log.info("Disconnected from IB Gateway")

    @property
    def is_connected(self) -> bool:
        return self._ib.isConnected()

    # --- Account ---

    async def get_positions(self) -> list[Position]:
        portfolio = self._ib.portfolio(self._config.ib_account or None)
        return [Position.from_portfolio_item(item) for item in portfolio]

    async def get_account_summary(self) -> AccountSummary:
        account = self._config.ib_account or ""
        tags = "NetLiquidation,AvailableFunds,BuyingPower,UnrealizedPnL,RealizedPnL,Currency"
        values = await self._ib.accountSummaryAsync(account=account)

        result: dict[str, str] = {}
        for v in values:
            if v.tag in tags.split(","):
                result[v.tag] = v.value

        return AccountSummary(
            nav=float(result.get("NetLiquidation", "0")),
            available_funds=float(result.get("AvailableFunds", "0")),
            buying_power=float(result.get("BuyingPower", "0")),
            unrealized_pnl=float(result.get("UnrealizedPnL", "0")),
            realized_pnl=float(result.get("RealizedPnL", "0")),
            currency=result.get("Currency", "USD"),
        )

    # --- Market Data ---

    async def get_market_price(self, contract: Contract) -> dict[str, Any]:
        self._ib.qualifyContracts(contract)
        ticker = self._ib.reqMktData(contract, snapshot=True)
        for _ in range(50):
            await asyncio.sleep(0.1)
            if util.isNan(ticker.last) and util.isNan(ticker.close):
                continue
            break
        self._ib.cancelMktData(contract)

        last = None if util.isNan(ticker.last) else ticker.last
        close = None if util.isNan(ticker.close) else ticker.close
        bid = None if util.isNan(ticker.bid) else ticker.bid
        ask = None if util.isNan(ticker.ask) else ticker.ask

        return {
            "symbol": contract.symbol,
            "last": last,
            "close": close,
            "bid": bid,
            "ask": ask,
        }

    async def get_historical_bars(
        self,
        contract: Contract,
        duration: str = "1 M",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES",
    ) -> list[dict[str, Any]]:
        self._ib.qualifyContracts(contract)
        bars = await self._ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=True,
        )
        return [
            {
                "date": str(bar.date),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in (bars or [])
        ]

    async def search_contracts(self, pattern: str) -> list[ContractMatch]:
        results = await self._ib.reqMatchingSymbolsAsync(pattern)
        if not results:
            return []
        matches = []
        for cs in results:
            c = cs.contract
            matches.append(
                ContractMatch(
                    con_id=c.conId,
                    symbol=c.symbol,
                    sec_type=c.secType,
                    exchange=c.exchange or c.primaryExchange or "",
                    currency=c.currency,
                    description=getattr(cs, "derivativeSecTypes", ""),
                )
            )
        return matches

    # --- Orders ---

    async def get_open_orders(self) -> list[OpenOrder]:
        trades = self._ib.openTrades()
        return [
            OpenOrder(
                order_id=t.order.orderId,
                symbol=t.contract.symbol,
                action=t.order.action,
                quantity=t.order.totalQuantity,
                order_type=t.order.orderType,
                limit_price=t.order.lmtPrice if t.order.orderType == "LMT" else None,
                status=t.orderStatus.status,
            )
            for t in trades
        ]

    async def place_limit_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        limit_price: float,
        currency: str = "USD",
        exchange: str = "SMART",
    ) -> dict[str, Any]:
        contract = Stock(symbol, exchange, currency)
        self._ib.qualifyContracts(contract)
        order = LimitOrder(action=action, totalQuantity=quantity, lmtPrice=limit_price)
        trade = self._ib.placeOrder(contract, order)
        return {
            "order_id": trade.order.orderId,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "limit_price": limit_price,
            "status": trade.orderStatus.status,
        }

    async def cancel_order(self, order_id: int) -> dict[str, Any]:
        for trade in self._ib.openTrades():
            if trade.order.orderId == order_id:
                self._ib.cancelOrder(trade.order)
                return {"order_id": order_id, "status": "cancel_requested"}
        return {"order_id": order_id, "status": "not_found"}

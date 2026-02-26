from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from ibkr_mcp.broker import Broker
from ibkr_mcp.config import ServerConfig

log = logging.getLogger(__name__)


@dataclass
class AppContext:
    broker: Broker
    config: ServerConfig


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    config = ServerConfig()
    broker = Broker(config)
    await broker.connect()
    try:
        yield AppContext(broker=broker, config=config)
    finally:
        await broker.disconnect()


mcp = FastMCP(
    "IBKR MCP Server",
    lifespan=app_lifespan,
    json_response=True,
)

# Register tools, resources, and prompts by importing the modules.
# Each module uses the `mcp` instance to register its handlers.
import ibkr_mcp.tools.account  # noqa: E402, F401
import ibkr_mcp.tools.market  # noqa: E402, F401
import ibkr_mcp.tools.trading  # noqa: E402, F401
import ibkr_mcp.tools.analysis  # noqa: E402, F401
import ibkr_mcp.resources.account  # noqa: E402, F401
import ibkr_mcp.prompts.templates  # noqa: E402, F401


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

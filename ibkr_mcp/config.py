from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ib_gateway_host: str = "127.0.0.1"
    ib_gateway_port: int = 4003
    ib_account: str = ""
    safety_paper_only: bool = True

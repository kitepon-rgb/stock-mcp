import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    alpha_vantage_key: str | None
    finnhub_key: str | None
    kabu_base_url: str | None
    kabu_api_password: str | None
    kabu_production: bool
    # Marketspeed2 bridge (Windows-side HTTP service that talks to Excel + RSS)
    ms2_bridge_url: str | None
    ms2_bridge_token: str | None
    # Order-execution safety knobs (Marketspeed2 only)
    orders_enabled: bool
    order_max_qty: int
    order_max_notional: float
    confirm_token_secret: str
    confirm_token_ttl_seconds: int


def load() -> Config:
    return Config(
        host=os.environ.get("STOCK_MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("STOCK_MCP_PORT", "39200")),
        alpha_vantage_key=os.environ.get("ALPHA_VANTAGE_API_KEY") or None,
        finnhub_key=os.environ.get("FINNHUB_API_KEY") or None,
        kabu_base_url=os.environ.get("KABU_BASE_URL") or None,
        kabu_api_password=os.environ.get("KABU_API_PASSWORD") or None,
        kabu_production=os.environ.get("KABU_PRODUCTION", "false").lower() == "true",
        ms2_bridge_url=(os.environ.get("MS2_BRIDGE_URL") or "").rstrip("/") or None,
        ms2_bridge_token=os.environ.get("MS2_BRIDGE_TOKEN") or None,
        orders_enabled=os.environ.get("STOCK_MCP_ENABLE_ORDERS", "false").lower() == "true",
        order_max_qty=int(os.environ.get("STOCK_MCP_MAX_ORDER_QTY", "1000")),
        order_max_notional=float(os.environ.get("STOCK_MCP_MAX_ORDER_NOTIONAL", "5000000")),
        confirm_token_secret=os.environ.get("STOCK_MCP_CONFIRM_TOKEN_SECRET") or secrets.token_hex(32),
        confirm_token_ttl_seconds=int(os.environ.get("STOCK_MCP_CONFIRM_TOKEN_TTL", "60")),
    )

#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.client import BinanceFuturesClient  # noqa: E402
from bot.logging_config import LOG_FILE, setup_logging  # noqa: E402
from bot.orders import OrderManager, OrderRequest  # noqa: E402

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_logs")


def fake_market_response(**kwargs):
    return {
        "orderId": 3454832129,
        "symbol": kwargs["symbol"],
        "status": "FILLED",
        "clientOrderId": "sample_market_001",
        "side": kwargs["side"],
        "type": "MARKET",
        "origQty": str(kwargs["quantity"]),
        "executedQty": str(kwargs["quantity"]),
        "avgPrice": "60123.40",
        "updateTime": 1751888888000,
    }


def fake_limit_response(**kwargs):
    return {
        "orderId": 3454832130,
        "symbol": kwargs["symbol"],
        "status": "NEW",
        "clientOrderId": "sample_limit_001",
        "side": kwargs["side"],
        "type": "LIMIT",
        "origQty": str(kwargs["quantity"]),
        "executedQty": "0",
        "price": str(kwargs["price"]),
        "avgPrice": "0.00",
        "timeInForce": kwargs.get("time_in_force", "GTC"),
        "updateTime": 1751888890000,
    }


def run_case(label: str, request: OrderRequest, fake_response) -> None:
    logger = logging.getLogger("trading_bot")
    for h in list(logger.handlers):
        logger.removeHandler(h)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    setup_logging("INFO")
    logging.getLogger("trading_bot").info(
        "=== SAMPLE LOG (%s) — network call mocked, no live Binance request made ===", label
    )

    from binance.client import Client as RawClient  # noqa: E402

    with patch.object(RawClient, "ping", return_value={}), patch.object(
        BinanceFuturesClient, "create_order", side_effect=fake_response
    ):
        client = BinanceFuturesClient(api_key="dummy", api_secret="dummy", testnet=True)
        manager = OrderManager(client)
        response = manager.place_order(request)

    print(f"[{label}] orderId={response.get('orderId')} status={response.get('status')}")

    os.makedirs(SAMPLE_DIR, exist_ok=True)
    dest = os.path.join(SAMPLE_DIR, f"{label}.log")
    shutil.copyfile(LOG_FILE, dest)
    print(f"  -> saved to {dest}")


if __name__ == "__main__":
    run_case(
        "market_order",
        OrderRequest(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.01),
        fake_market_response,
    )
    run_case(
        "limit_order",
        OrderRequest(symbol="BTCUSDT", side="SELL", order_type="LIMIT", quantity=0.01, price=60000.0),
        fake_limit_response,
    )

#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet trading bot.

Examples:
    # Market order
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit order
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000

    # Bonus: stop-limit order
    python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 \\
        --price 60000 --stop-price 59500

    # Validate input only, without sending anything to Binance
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClientError, BinanceFuturesClient
from bot.logging_config import setup_logging
from bot.orders import OrderManager, OrderRequest
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
    validate_time_in_force,
)

logger = logging.getLogger("trading_bot.cli")

# Loads variables from a .env file in the project root (if present) into the
# environment. Works the same way on Windows, macOS, and Linux, so you don't
# need `set` / `$env:` / `export` in every new terminal session.
load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Place MARKET / LIMIT / STOP_LIMIT orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument("--type", dest="order_type", required=True, help="MARKET, LIMIT, or STOP_LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", default=None, help="Required for LIMIT and STOP_LIMIT orders")
    parser.add_argument("--stop-price", dest="stop_price", default=None, help="Required for STOP_LIMIT orders")
    parser.add_argument(
        "--time-in-force",
        dest="time_in_force",
        default="GTC",
        help="GTC / IOC / FOK — applies to LIMIT and STOP_LIMIT (default: GTC)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input and print the request only — does not call the Binance API.",
    )
    parser.add_argument("--log-level", default="INFO", help="Console log level (default: INFO)")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(args.log_level)

    # --- Validation layer ---------------------------------------------------
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type, field_name="price")
        time_in_force = validate_time_in_force(args.time_in_force)
        stop_price = None
        if order_type == "STOP_LIMIT":
            stop_price = validate_price(args.stop_price, order_type, field_name="stop_price")
    except ValidationError as exc:
        print(f"Invalid input: {exc}")
        logger.error("Validation failed: %s", exc)
        return 1

    request = OrderRequest(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        time_in_force=time_in_force,
    )

    print("Order request:")
    print(f"  {request.summary()}")

    if args.dry_run:
        print("Dry run only — no request sent to Binance.")
        logger.info("Dry run complete for: %s", request.summary())
        return 0

    # --- API layer ------------------------------------------------------------
    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")

    try:
        client = BinanceFuturesClient(api_key, api_secret, testnet=True)
        manager = OrderManager(client)
        response = manager.place_order(request)
    except ValueError as exc:  # missing/invalid credentials
        print(f"Configuration error: {exc}")
        logger.error("Configuration error: %s", exc)
        return 1
    except BinanceClientError as exc:  # API or network error
        print(f"Order failed: {exc}")
        logger.error("Order failed: %s", exc)
        return 1
    except Exception as exc:  # anything unforeseen — fail gracefully, never crash silently
        print(f"Unexpected error: {exc}")
        logger.exception("Unexpected error while placing order")
        return 1

    # --- Output ---------------------------------------------------------------
    print("\nOrder response:")
    print(f"  orderId:      {response.get('orderId')}")
    print(f"  status:       {response.get('status')}")
    print(f"  executedQty:  {response.get('executedQty')}")
    print(f"  avgPrice:     {response.get('avgPrice', 'N/A')}")
    print("\nOrder placed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

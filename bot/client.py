from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger("trading_bot.client")

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error or the request fails outright."""


class BinanceFuturesClient:
    """Thin wrapper around python-binance for USDT-M Futures Testnet order placement."""

    def __init__(self, api_key: Optional[str], api_secret: Optional[str], testnet: bool = True) -> None:
        if not api_key or not api_secret:
            raise ValueError(
                "API key and secret must be provided. Set BINANCE_API_KEY and "
                "BINANCE_API_SECRET environment variables (see .env.example)."
            )

        self._client = Client(api_key, api_secret, testnet=testnet)

        if testnet:
            # python-binance sets this internally when testnet=True, but we pin it
            # explicitly so behaviour can't silently change on a library upgrade.
            self._client.FUTURES_URL = f"{FUTURES_TESTNET_BASE_URL}/fapi"

        logger.info("Initialized Binance Futures client (testnet=%s, base_url=%s)", testnet, FUTURES_TESTNET_BASE_URL)

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Submit an order to Binance USDT-M Futures Testnet.

        Args:
            symbol: e.g. "BTCUSDT"
            side: "BUY" or "SELL"
            order_type: "MARKET", "LIMIT", or "STOP_LIMIT"
            quantity: order quantity
            price: required for LIMIT / STOP_LIMIT
            stop_price: required for STOP_LIMIT
            time_in_force: GTC / IOC / FOK (LIMIT / STOP_LIMIT only)

        Returns:
            Parsed JSON response from Binance.

        Raises:
            BinanceClientError: on API errors or network failures.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
        }

        if order_type == "MARKET":
            params["type"] = "MARKET"
        elif order_type == "LIMIT":
            params["type"] = "LIMIT"
            params["price"] = price
            params["timeInForce"] = time_in_force
        elif order_type == "STOP_LIMIT":
            # Binance Futures calls this order type "STOP" (stop-limit behaviour).
            params["type"] = "STOP"
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force
        else:
            raise BinanceClientError(f"Unsupported order type: {order_type}")

        logger.info("Submitting order request: %s", params)

        try:
            response = self._client.futures_create_order(**params)
            logger.info("Order response received: %s", response)
            return response
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Binance API error while placing order %s: %s", params, exc)
            raise BinanceClientError(f"Binance API error: {exc}") from exc
        except Exception as exc:  # network errors, timeouts, DNS failures, etc.
            logger.error("Network/unexpected error while placing order %s: %s", params, exc)
            raise BinanceClientError(f"Network or unexpected error: {exc}") from exc

    def get_account_balance(self) -> Any:
        """Optional helper: fetch futures account balance (useful for manual sanity checks)."""
        try:
            balance = self._client.futures_account_balance()
            logger.info("Fetched account balance.")
            return balance
        except Exception as exc:
            logger.error("Failed to fetch account balance: %s", exc)
            raise BinanceClientError(f"Could not fetch balance: {exc}") from exc

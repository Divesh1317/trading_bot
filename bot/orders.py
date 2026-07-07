from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .client import BinanceClientError, BinanceFuturesClient

logger = logging.getLogger("trading_bot.orders")


@dataclass
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"

    def summary(self) -> str:
        parts = [
            f"symbol={self.symbol}",
            f"side={self.side}",
            f"type={self.order_type}",
            f"quantity={self.quantity}",
        ]
        if self.price is not None:
            parts.append(f"price={self.price}")
        if self.stop_price is not None:
            parts.append(f"stop_price={self.stop_price}")
        if self.order_type != "MARKET":
            parts.append(f"time_in_force={self.time_in_force}")
        return ", ".join(parts)


class OrderManager:
    

    def __init__(self, client: BinanceFuturesClient) -> None:
        self._client = client

    def place_order(self, request: OrderRequest) -> Dict[str, Any]:
        logger.info("Placing order: %s", request.summary())
        try:
            response = self._client.create_order(
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                price=request.price,
                stop_price=request.stop_price,
                time_in_force=request.time_in_force,
            )
            logger.info(
                "Order placed successfully: orderId=%s status=%s executedQty=%s",
                response.get("orderId"),
                response.get("status"),
                response.get("executedQty"),
            )
            return response
        except BinanceClientError:
            logger.error("Order placement failed for: %s", request.summary())
            raise

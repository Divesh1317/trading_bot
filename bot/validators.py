from __future__ import annotations

from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}
VALID_TIME_IN_FORCE = {"GTC", "IOC", "FOK"}


class ValidationError(Exception):
    """Raised when user-supplied order parameters fail validation."""


def validate_symbol(symbol: str) -> str:
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol cannot be empty.")
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValidationError(f"Symbol '{symbol}' must be alphanumeric, e.g. BTCUSDT.")
    if len(symbol) < 5:
        raise ValidationError(f"Symbol '{symbol}' looks too short to be a valid pair, e.g. BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValidationError("Side cannot be empty.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValidationError("Order type cannot be empty.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'.")
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")
    if quantity <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {quantity}.")
    return quantity


def validate_price(price, order_type: str, field_name: str = "price") -> Optional[float]:
    if order_type == "MARKET":
        return None
    if price is None:
        raise ValidationError(f"--{field_name.replace('_', '-')} is required for {order_type} orders.")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a number, got '{price}'.")
    if price <= 0:
        raise ValidationError(f"{field_name} must be greater than 0, got {price}.")
    return price


def validate_time_in_force(tif: str) -> str:
    tif = (tif or "GTC").strip().upper()
    if tif not in VALID_TIME_IN_FORCE:
        raise ValidationError(f"time_in_force must be one of {sorted(VALID_TIME_IN_FORCE)}, got '{tif}'.")
    return tif

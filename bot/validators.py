"""
validators.py
Pure-validation helpers — no network calls, no side-effects.
Raises ValueError with a human-readable message on bad input.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s:
        raise ValueError("Symbol cannot be empty.")
    if not s.isalnum():
        raise ValueError(f"Symbol '{s}' contains invalid characters. Example: BTCUSDT")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(f"Side must be one of {VALID_SIDES}. Got: '{side}'")
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {VALID_ORDER_TYPES}. Got: '{order_type}'"
        )
    return t


def validate_quantity(quantity: str | float) -> float:
    try:
        q = float(quantity)
    except (ValueError, TypeError):
        raise ValueError(f"Quantity must be a positive number. Got: '{quantity}'")
    if q <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got: {q}")
    return q


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """
    Price is required for LIMIT orders.
    For MARKET orders it is ignored (returns None).
    For STOP_MARKET orders it becomes the stopPrice.
    """
    if order_type == "MARKET":
        return None

    if price is None or str(price).strip() == "":
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValueError(f"Price must be a positive number. Got: '{price}'")
    if p <= 0:
        raise ValueError(f"Price must be greater than 0. Got: {p}")
    return p


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
) -> dict:
    """
    Run all validators and return a clean dict ready to pass to the order layer.
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper()),
    }

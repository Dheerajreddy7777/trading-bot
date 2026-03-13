"""
orders.py
High-level order placement logic.
Translates validated user input → Binance API params → structured result dict.
"""

from __future__ import annotations

import logging
from typing import Any

from .client import BinanceFuturesClient, BinanceClientError

logger = logging.getLogger("trading_bot.orders")


def _build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
) -> dict:
    """Build the raw params dict for the Binance /fapi/v1/order endpoint."""
    params: dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("price is required for LIMIT orders")
        params["price"] = price
        params["timeInForce"] = "GTC"          # Good-Till-Cancelled

    elif order_type == "STOP_MARKET":
        if price is None:
            raise ValueError("stopPrice is required for STOP_MARKET orders")
        params["stopPrice"] = price             # price field used as stopPrice in CLI

    return params


def _parse_response(raw: dict) -> dict:
    """Extract the fields we care about from the raw API response."""
    return {
        "orderId": raw.get("orderId"),
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "type": raw.get("type"),
        "status": raw.get("status"),
        "origQty": raw.get("origQty"),
        "executedQty": raw.get("executedQty"),
        "avgPrice": raw.get("avgPrice"),
        "price": raw.get("price"),
        "stopPrice": raw.get("stopPrice"),
        "timeInForce": raw.get("timeInForce"),
        "updateTime": raw.get("updateTime"),
    }


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
) -> dict:
    """
    Place an order and return a parsed result dict.

    Returns
    -------
    dict with keys: orderId, symbol, side, type, status, origQty,
                    executedQty, avgPrice, price, stopPrice, timeInForce, updateTime

    Raises
    ------
    BinanceClientError   – API rejected the order
    requests.Timeout     – network timeout
    requests.ConnectionError – connectivity failure
    ValueError           – bad params (shouldn't reach here if validators ran)
    """
    params = _build_order_params(symbol, side, order_type, quantity, price)

    logger.info(
        "Submitting %s %s order — symbol=%s qty=%s price=%s",
        side, order_type, symbol, quantity, price,
    )

    try:
        raw = client.place_order(**params)
    except BinanceClientError as exc:
        logger.error(
            "Order rejected by Binance — code=%s msg=%s  request_params=%s",
            exc.code, exc.msg, params,
        )
        raise
    except Exception as exc:
        logger.error("Unexpected error during order placement: %s", exc)
        raise

    result = _parse_response(raw)
    logger.info(
        "Order placed successfully — orderId=%s status=%s executedQty=%s avgPrice=%s",
        result["orderId"], result["status"], result["executedQty"], result["avgPrice"],
    )
    return result

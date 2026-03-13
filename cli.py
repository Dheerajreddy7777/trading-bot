#!/usr/bin/env python3
"""
cli.py
Command-line interface for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500

# Stop-Market BUY  (bonus order type)
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --price 60000

API credentials are read from environment variables (recommended) or can be
passed via --api-key / --api-secret flags.
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap

import requests

from bot.client import BinanceFuturesClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import validate_all

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BANNER = """
╔══════════════════════════════════════════╗
║   Binance Futures Testnet Trading Bot    ║
╚══════════════════════════════════════════╝
"""


def _print_summary(params: dict) -> None:
    print("\n📋  Order Request Summary")
    print("─" * 40)
    print(f"  Symbol   : {params['symbol']}")
    print(f"  Side     : {params['side']}")
    print(f"  Type     : {params['order_type']}")
    print(f"  Quantity : {params['quantity']}")
    if params["price"] is not None:
        label = "Stop Price" if params["order_type"] == "STOP_MARKET" else "Price"
        print(f"  {label:<9}: {params['price']}")
    print("─" * 40)


def _print_result(result: dict) -> None:
    print("\n✅  Order Placed Successfully!")
    print("─" * 40)
    print(f"  Order ID     : {result['orderId']}")
    print(f"  Symbol       : {result['symbol']}")
    print(f"  Side         : {result['side']}")
    print(f"  Type         : {result['type']}")
    print(f"  Status       : {result['status']}")
    print(f"  Orig Qty     : {result['origQty']}")
    print(f"  Executed Qty : {result['executedQty']}")
    avg = result.get("avgPrice")
    if avg and float(avg) > 0:
        print(f"  Avg Price    : {avg}")
    lmt = result.get("price")
    if lmt and float(lmt) > 0:
        print(f"  Limit Price  : {lmt}")
    stp = result.get("stopPrice")
    if stp and float(stp) > 0:
        print(f"  Stop Price   : {stp}")
    tif = result.get("timeInForce")
    if tif:
        print(f"  Time-In-Force: {tif}")
    print("─" * 40)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Binance Futures Testnet — order placement CLI.

            Credentials (pick ONE method):
              1. Environment variables  BINANCE_API_KEY  and  BINANCE_API_SECRET  (recommended)
              2. --api-key / --api-secret flags (avoid in shared environments)
        """),
        epilog=textwrap.dedent("""\
            Examples:
              python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
              python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.01 --price 3500
              python cli.py --symbol BTCUSDT --side BUY  --type STOP_MARKET --quantity 0.001 --price 60000
        """),
    )

    # --- credentials ---
    creds = parser.add_argument_group("credentials (env vars preferred)")
    creds.add_argument("--api-key",    metavar="KEY",    help="Binance API key")
    creds.add_argument("--api-secret", metavar="SECRET", help="Binance API secret")

    # --- order params ---
    order = parser.add_argument_group("order parameters")
    order.add_argument("--symbol",   required=True, help="Trading pair, e.g. BTCUSDT")
    order.add_argument("--side",     required=True, choices=["BUY", "SELL"],
                       help="Order side")
    order.add_argument("--type",     required=True, dest="order_type",
                       choices=["MARKET", "LIMIT", "STOP_MARKET"],
                       help="Order type")
    order.add_argument("--quantity", required=True, type=float,
                       help="Order quantity in base asset")
    order.add_argument("--price",    type=float, default=None,
                       help="Limit price (LIMIT) or stop trigger price (STOP_MARKET)")

    # --- misc ---
    parser.add_argument("--log-level", default="DEBUG",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="File log level (default: DEBUG)")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Set up logging before anything else
    logger = setup_logging(args.log_level)
    logger.info("=" * 60)
    logger.info("Trading bot started")

    print(BANNER)

    # --- resolve credentials ---
    api_key    = args.api_key    or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            "❌  Error: API credentials not found.\n"
            "    Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
            "    or pass --api-key and --api-secret flags."
        )
        logger.error("Missing API credentials — aborting.")
        return 1

    # --- validate user input ---
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValueError as exc:
        print(f"❌  Validation Error: {exc}")
        logger.error("Input validation failed: %s", exc)
        return 1

    _print_summary(params)

    # --- connect and place order ---
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

    # quick connectivity check
    try:
        st = client.get_server_time()
        logger.debug("Server time: %s", st)
    except (requests.ConnectionError, requests.Timeout) as exc:
        print(f"❌  Cannot reach Binance testnet: {exc}")
        logger.error("Connectivity check failed: %s", exc)
        return 1

    try:
        result = place_order(
            client=client,
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
        )
    except BinanceClientError as exc:
        print(f"\n❌  Order Failed (Binance error {exc.code}): {exc.msg}")
        logger.error("Order failed: %s", exc)
        return 1
    except (requests.ConnectionError, requests.Timeout) as exc:
        print(f"\n❌  Network error: {exc}")
        logger.error("Network error during order: %s", exc)
        return 1
    except Exception as exc:
        print(f"\n❌  Unexpected error: {exc}")
        logger.exception("Unexpected error: %s", exc)
        return 1

    _print_result(result)
    logger.info("Trading bot finished successfully")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

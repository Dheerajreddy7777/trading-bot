"""
client.py
Low-level Binance Futures Testnet REST client.
Handles authentication (HMAC-SHA256), request signing, and HTTP calls.
All raw request/response details are logged at DEBUG level.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any

import requests

logger = logging.getLogger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # ms


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"Binance API error {code}: {msg}")


class BinanceFuturesClient:
    """
    Minimal Binance USDT-M Futures REST client.

    Parameters
    ----------
    api_key    : your testnet API key
    api_secret : your testnet API secret
    base_url   : override if you ever want to point at mainnet (careful!)
    timeout    : request timeout in seconds
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
    ):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")

        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceFuturesClient initialised — base_url=%s", self._base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        """Return HMAC-SHA256 hex signature for the given params dict."""
        query = urllib.parse.urlencode(params)
        sig = hmac.new(self._api_secret, query.encode(), hashlib.sha256).hexdigest()
        return sig

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        """
        Fire an HTTP request and return the parsed JSON body.

        Raises
        ------
        BinanceClientError  on API-level errors  (HTTP 4xx / 5xx with Binance JSON)
        requests.Timeout    on network timeouts
        requests.ConnectionError on connectivity problems
        """
        params = params or {}

        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = RECV_WINDOW
            params["signature"] = self._sign(params)

        url = f"{self._base_url}{path}"

        logger.debug("→ %s %s  params=%s", method.upper(), url, params)

        try:
            if method.upper() == "GET":
                resp = self._session.get(url, params=params, timeout=self._timeout)
            else:
                resp = self._session.post(url, data=params, timeout=self._timeout)
        except requests.Timeout as exc:
            logger.error("Request timed out: %s %s", method, url)
            raise
        except requests.ConnectionError as exc:
            logger.error("Connection error: %s %s — %s", method, url, exc)
            raise

        logger.debug("← HTTP %s  body=%s", resp.status_code, resp.text[:500])

        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()
            return resp.text

        # Binance error responses carry a numeric 'code' < 0
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceClientError(data["code"], data.get("msg", "unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> dict:
        """Sanity-check connectivity."""
        return self._request("GET", "/fapi/v1/time")

    def get_exchange_info(self) -> dict:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **kwargs) -> dict:
        """
        Place a new order.  kwargs are passed straight to the Binance API.
        Required keys (at minimum): symbol, side, type, quantity.
        """
        logger.debug("Placing order with params: %s", kwargs)
        return self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

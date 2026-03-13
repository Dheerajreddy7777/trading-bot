# Binance Futures Testnet Trading Bot

A lightweight Python CLI for placing orders on **Binance USDT-M Futures Testnet**.  
Supports Market, Limit, and Stop-Market orders with clean logging and error handling.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Low-level Binance REST client (auth, signing, HTTP)
│   ├── orders.py          # Order-placement logic & response parsing
│   ├── validators.py      # Input validation (no side-effects)
│   └── logging_config.py  # Rotating file + console logging setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   └── trading_bot.log    # Sample log file (auto-created on first run)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in (GitHub account works)
3. Click **API Key** in the top-right → Generate a new key pair
4. Copy your **API Key** and **Secret Key** — the secret is only shown once

### 2. Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Set Credentials

**Recommended — environment variables (never commit keys to git):**

```bash
# Linux / macOS
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"

# Windows PowerShell
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

**Alternative — pass via flags (avoid on shared machines):**

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET ...
```

---

## How to Run

### Market Order — BUY 0.001 BTC

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Expected output:**
```
╔══════════════════════════════════════════╗
║   Binance Futures Testnet Trading Bot    ║
╚══════════════════════════════════════════╝

📋  Order Request Summary
────────────────────────────────────────
  Symbol   : BTCUSDT
  Side     : BUY
  Type     : MARKET
  Quantity : 0.001
────────────────────────────────────────

✅  Order Placed Successfully!
────────────────────────────────────────
  Order ID     : 4029653960
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : FILLED
  Orig Qty     : 0.001
  Executed Qty : 0.001
  Avg Price    : 62314.50
────────────────────────────────────────
```

---

### Limit Order — SELL 0.01 ETH at $3,500

```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500
```

---

### Stop-Market Order (Bonus) — BUY 0.001 BTC if price reaches $63,000

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --price 63000
```

---

### Get Help

```bash
python cli.py --help
```

---

## Logging

Logs are written to `logs/trading_bot.log` automatically.  
The file rotates at 5 MB and keeps 3 backups.

| Destination | Level | What you see |
|-------------|-------|--------------|
| Console     | INFO  | Order summaries, success/failure |
| Log file    | DEBUG | Full request params, raw API responses, errors |

Sample log entries are included in `logs/trading_bot.log`.

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Missing API credentials | Clear error message + exit code 1 |
| Invalid symbol / qty / price | Validation error before any network call |
| Binance API rejection (e.g. bad precision) | Error code + message from Binance |
| Network timeout | Informative message, logged as ERROR |
| Connection failure | Informative message, logged as ERROR |

---

## Assumptions

- All orders are placed on **USDT-M Futures Testnet** (`https://testnet.binancefuture.com`)
- Minimum quantity / price tick sizes are enforced server-side by Binance; the bot surfaces those errors clearly
- LIMIT orders use `timeInForce = GTC` (Good-Till-Cancelled) by default
- STOP_MARKET orders use the `--price` flag as the `stopPrice` trigger
- Credentials are expected as environment variables; flag-based passing is supported but discouraged

---

## Requirements

- Python 3.8+
- `requests` (see `requirements.txt`)

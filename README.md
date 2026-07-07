# Binance Futures Testnet Trading Bot

A small CLI application for placing MARKET, LIMIT, and STOP_LIMIT orders on
**Binance Futures Testnet (USDT-M)**, with input validation, structured
logging, and clean separation between the API layer and the CLI layer.

## Project structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # Binance client wrapper (API layer)
    orders.py          # Order placement logic (sits between CLI and client)
    validators.py       # Input validation
    logging_config.py   # Logging setup (console + rotating file handler)
  cli.py                 # CLI entry point (argparse)
  scripts/
    generate_sample_logs.py  # Generates sample_logs/ (see note below)
  sample_logs/            # Example log output (see "About sample_logs/" below)
  logs/                    # Real logs land here when you run cli.py
  requirements.txt
  .env.example
  README.md
```

## Setup

1. **Create a Binance Futures Testnet account** at
   https://testnet.binancefuture.com and generate an API key/secret from
   the testnet dashboard.

2. **Install dependencies** (Python 3.9+):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   **Windows — pick whichever matches your setup:**

   - **Command Prompt (cmd.exe)** — sets the variable for that window only:
     ```cmd
     set BINANCE_API_KEY=your_testnet_api_key_here
     set BINANCE_API_SECRET=your_testnet_api_secret_here
     ```

   - **Persist it permanently (Windows System Properties)** — so you don't
     have to re-set it every session:
     1. Press `Win`, search **"Environment Variables"**, open
        *"Edit the system environment variables"*.
     2. Click **Environment Variables...** → under *User variables*, click
        **New...**.
     3. Add `BINANCE_API_KEY` and its value; repeat for `BINANCE_API_SECRET`.
     4. Click OK on all dialogs, then **open a new** Command
        Prompt/PowerShell/terminal window (existing ones won't pick it up).

   - **Load automatically from a `.env` file (recommended for Windows — no
     `set`/`$env:` every session):** this is already wired up in `cli.py`
     via `python-dotenv` (included in `requirements.txt`). Just:
     1. `pip install -r requirements.txt` (installs `python-dotenv` too)
     2. Copy `.env.example` to `.env` and fill in your real key/secret:
        ```cmd
        copy .env.example .env
        ```
     3. Edit `.env` in Notepad/VS Code and fill in the two values.
     4. Run `python cli.py ...` as normal — `cli.py` calls `load_dotenv()`
        on startup, which reads `.env` from the project root and loads
        `BINANCE_API_KEY` / `BINANCE_API_SECRET` into the environment
        automatically. No manual `set` or `$env:` needed, and it works the
        same on Windows, macOS, and Linux.

   Verify it's set correctly before running the bot:
   ```powershell
   # PowerShell
   echo $env:BINANCE_API_KEY
   ```
   ```cmd
   :: Command Prompt
   echo %BINANCE_API_KEY%
   ```

## Running

All commands are run from the project root.

**Market order:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

**Limit order:**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

**Stop-limit order (bonus order type):**
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 \
    --price 60000 --stop-price 59500
```

**Validate input without sending anything to Binance:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
```

### CLI arguments

| Flag               | Required for      | Description                          |
|---------------------|--------------------|---------------------------------------|
| `--symbol`          | all                | e.g. `BTCUSDT`                        |
| `--side`             | all                | `BUY` or `SELL`                       |
| `--type`             | all                | `MARKET`, `LIMIT`, `STOP_LIMIT`       |
| `--quantity`         | all                | order quantity                        |
| `--price`            | LIMIT / STOP_LIMIT | limit price                           |
| `--stop-price`       | STOP_LIMIT         | stop trigger price                    |
| `--time-in-force`    | optional           | `GTC` / `IOC` / `FOK` (default `GTC`) |
| `--dry-run`          | optional           | validate + print only, no API call    |
| `--log-level`        | optional           | console log level (default `INFO`)    |

On success the CLI prints the order request summary, then the response
(`orderId`, `status`, `executedQty`, `avgPrice`). On failure — bad input,
Binance API error, or network failure — it prints a clear error message and
exits with a non-zero status code. Every request, response, and error is
also written to `logs/trading_bot.log`.

## About `sample_logs/`

This environment I used to write the code has no network access to Binance
(only package registries are reachable), so I could not personally execute
a live order against the real testnet API. To still demonstrate the logging
format and the full request → response → log flow, `sample_logs/` contains
output from `scripts/generate_sample_logs.py`, which runs the **real**
validation, `OrderManager`, and logging code, with only the network call
mocked. Each sample log file says so explicitly in its first line.

**Before you submit this task under your own name**, please replace these
with genuine logs: run the two commands above with your own testnet API
keys, and copy the resulting entries from `logs/trading_bot.log`. That's
the actual deliverable the evaluation criteria asks for.

## Assumptions

- **STOP_LIMIT** is implemented as Binance Futures' `STOP` order type,
  which is a stop-limit order (triggers at `stop_price`, then places a
  limit order at `price`) — this is the bonus order type chosen.
- Quantity/price precision (`LOT_SIZE`, `PRICE_FILTER`) is left to Binance
  to validate and reject if out of range; the app validates presence,
  type, and positivity but does not duplicate exchange-specific tick/step
  size rules. `BinanceFuturesClient.get_symbol_info()` is included as a
  hook for anyone who wants to add that check.
- Only USDT-M Futures is in scope, per the task spec — no Coin-M or Spot
  support.
- Credentials are read from environment variables rather than a config
  file, to avoid ever committing secrets to source control.
- `python-binance`'s `testnet=True` flag is used and the futures URL is
  additionally pinned explicitly in `client.py`, so behavior can't
  silently change if the library's defaults change in a future release.

## Error handling summary

| Failure type              | Where caught                  | Result                          |
|-----------------------------|-------------------------------|----------------------------------|
| Invalid CLI input            | `validators.py`               | Printed error, exit 1, no API call |
| Missing/invalid API keys     | `client.py` (`ValueError`)     | Printed error, exit 1            |
| Binance API error (e.g. insufficient margin, bad symbol) | `client.py` → `BinanceClientError` | Printed error, exit 1, logged |
| Network failure / timeout    | `client.py` → `BinanceClientError` | Printed error, exit 1, logged |
| Anything unforeseen          | `cli.py` catch-all             | Printed error, exit 1, full traceback logged |

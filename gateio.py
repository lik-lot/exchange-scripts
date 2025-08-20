"""
TradingView tvDatafeed v2.x  Multi-Timeframe Data Collection (GATE.IO)
- Auto-collect all tradeable symbols from Gate.io REST API /api/v4/spot/currency_pairs
- Extracts multiple timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- Rate-limit (4 calls/sec), random jitter, exponential back-off retry included
"""

import os, time, random, logging
from collections import deque
from datetime import datetime
from typing import List
import pandas as pd
from tvDatafeed import TvDatafeed, Interval

# ▼ Dependencies for automatic GATE.IO symbol collection
import requests
from urllib.parse import urljoin

# ─────────────────── 0. Configuration ────────────────────
USERNAME = os.getenv("TV_USER")          # TradingView login (environment variables recommended)
PASSWORD = os.getenv("TV_PASS")

MAX_REQ_PER_SEC = 4                      # Maximum calls per second
JITTER_RANGE    = (0.05, 0.15)           # Random delay before/after each call (seconds)
MAX_RETRIES     = 4                      # Maximum retries (0.5→1→2→4 s)
N_BARS          = 5_000                  # Number of bars to fetch
GATEIO          = "GATEIO"               # TradingView exchange code

# Timeframes to collect with their respective intervals and save directories
TIMEFRAMES = [
    {"interval": Interval.in_1_minute,  "suffix": "1m",  "dir": "data_gateio_1m"},
    {"interval": Interval.in_5_minute,  "suffix": "5m",  "dir": "data_gateio_5m"},
    {"interval": Interval.in_15_minute, "suffix": "15m", "dir": "data_gateio_15m"},
    {"interval": Interval.in_1_hour,    "suffix": "1h",  "dir": "data_gateio_1h"},
    {"interval": Interval.in_4_hour,    "suffix": "4h",  "dir": "data_gateio_4h"},
    {"interval": Interval.in_daily,     "suffix": "1d",  "dir": "data_gateio_1d"},
]

# (Optional) Include only specific quote currencies (empty list = all)
QUOTE_FILTER = []                        # Empty = include all quote currencies

# (Optional) Manual mapping: "GATE.IO API symbol" → "TradingView symbol"
MANUAL_MAP = {
    # Example mappings (adjust if needed)
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S"
)

# ─────────────────── 1. Load Symbols (Direct query from GATE.IO) ─────────────────
GATEIO_API = "https://api.gateio.ws"
CURRENCY_PAIRS_ENDPOINT = "/api/v4/spot/currency_pairs"

def gateio_to_tv_symbol(gateio_symbol: str) -> str:
    """Convert Gate.io symbol format to TradingView format"""
    # Remove underscores: 10SET_USDT → 10SETUSDT
    return gateio_symbol.replace("_", "").upper()

def fetch_gateio_all_spot_symbols() -> List[str]:
    """
    Return all tradeable symbols from Gate.io.
    """
    url = urljoin(GATEIO_API, CURRENCY_PAIRS_ENDPOINT)

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        # Gate.io returns array directly
        if not isinstance(data, list):
            logging.error(f"Gate.io API unexpected response format")
            return []

        symbols_data = data

    except Exception as e:
        logging.error(f"Failed to fetch Gate.io symbols: {e}")
        return []

    syms = []
    for s in symbols_data:
        # Check trade status - should be 'tradable'
        if s.get("trade_status") != "tradable":
            continue

        # Get the symbol name (Gate.io uses 'id' field for currency_pair)
        sym = s.get("id", "")
        if not sym:
            continue

        # Apply quote currency filter if specified
        if QUOTE_FILTER:
            quote = s.get("quote", "")
            if quote not in QUOTE_FILTER:
                continue

        # Convert to TradingView format (remove underscores)
        tv_symbol = gateio_to_tv_symbol(sym)
        
        # Apply manual mapping (handle exception cases)
        tv_symbol = MANUAL_MAP.get(tv_symbol, tv_symbol)

        syms.append(tv_symbol)

    # Remove duplicates and sort
    unique_syms = sorted(set(syms))

    logging.info(f"Found {len(unique_syms)} unique tradeable symbols from Gate.io")

    # Log sample symbols for verification
    if unique_syms:
        logging.info(f"Sample symbols: {unique_syms[:10]}")

    return unique_syms

# Fetch symbols
logging.info("Fetching Gate.io symbols...")
symbols = fetch_gateio_all_spot_symbols()

if not symbols:
    logging.error("No symbols found. Exiting.")
    exit(1)

logging.info(f"Symbol collection complete: Total {len(symbols)} symbols")

# ─────────────────── 2. Start Session & Create Directories ────────────────
try:
    tv = TvDatafeed(USERNAME, PASSWORD)      # v2.x: no auto_login argument
    logging.info("TradingView session established")
except Exception as e:
    logging.error(f"Failed to establish TradingView session: {e}")
    exit(1)

# Create all timeframe directories
for tf in TIMEFRAMES:
    os.makedirs(tf["dir"], exist_ok=True)

# ──────────────── 3. Token-Bucket Rate Limiting ──────────────
recent_calls = deque()                   # Store call times within last 1 second

def wait_for_slot():
    """Wait to not exceed MAX_REQ_PER_SEC per second + jitter"""
    now = time.perf_counter()
    while recent_calls and now - recent_calls[0] > 1:
        recent_calls.popleft()           # Remove calls older than 1 second

    if len(recent_calls) >= MAX_REQ_PER_SEC:
        sleep_time = 1 - (now - recent_calls[0])   # Wait until 1 second passes
        sleep_time += random.uniform(*JITTER_RANGE)
        time.sleep(max(0, sleep_time))

    recent_calls.append(time.perf_counter())
    time.sleep(random.uniform(*JITTER_RANGE))       # Additional jitter

# ─────────────────── 4. Main Loop ────────────────
# Track statistics
stats = {tf["suffix"]: {"successful": 0, "failed": []} for tf in TIMEFRAMES}
total_operations = len(symbols) * len(TIMEFRAMES)
current_operation = 0

logging.info(f"Starting collection for {len(symbols)} symbols across {len(TIMEFRAMES)} timeframes")
logging.info(f"Total operations: {total_operations}")

for idx, sym in enumerate(symbols, 1):
    logging.info(f"\n{'='*50}")
    logging.info(f"Processing symbol {idx}/{len(symbols)}: {sym}")
    logging.info(f"{'='*50}")

    for tf in TIMEFRAMES:
        current_operation += 1
        progress_pct = (current_operation / total_operations) * 100

        out_path = os.path.join(tf["dir"], f"{sym}_{tf['suffix']}.csv")

        # Skip if already exists
        if os.path.exists(out_path):
            logging.info(f"  [{tf['suffix']}] Already exists, skipping")
            stats[tf["suffix"]]["successful"] += 1
            continue

        retry = 0
        while retry <= MAX_RETRIES:
            try:
                wait_for_slot()

                logging.info(f"  [{tf['suffix']}] Fetching data... (Overall progress: {progress_pct:.1f}%)")

                df = tv.get_hist(
                    symbol=sym,
                    exchange=GATEIO,
                    interval=tf["interval"],
                    n_bars=N_BARS
                )

                if df is None or df.empty:
                    logging.warning(f"  [{tf['suffix']}] Empty data")
                    stats[tf["suffix"]]["failed"].append(sym)
                    break

                df.to_csv(out_path)
                logging.info(f"  [{tf['suffix']}] ✓ Saved {len(df)} bars → {out_path}")
                stats[tf["suffix"]]["successful"] += 1
                break

            except Exception as e:
                retry += 1
                if retry > MAX_RETRIES:
                    logging.error(f"  [{tf['suffix']}] ✗ Failed after {MAX_RETRIES} retries: {e}")
                    stats[tf["suffix"]]["failed"].append(sym)
                    break
                wait_sec = 0.5 * (2 ** (retry - 1))
                logging.warning(f"  [{tf['suffix']}] Error: {e} – Retry {retry}/{MAX_RETRIES} in {wait_sec:.1f}s")
                time.sleep(wait_sec)

# ─────────────────── 5. Summary Report ────────────────
print("\n" + "="*70)
print("=== COLLECTION COMPLETE ===")
print("="*70)
print(f"\nProcessed {len(symbols)} symbols across {len(TIMEFRAMES)} timeframes")
print(f"Total operations attempted: {total_operations}")

print("\n--- Statistics by Timeframe ---")
for tf in TIMEFRAMES:
    suffix = tf["suffix"]
    successful = stats[suffix]["successful"]
    failed_count = len(stats[suffix]["failed"])
    total = successful + failed_count
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"\n{suffix.upper()} timeframe:")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {failed_count}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Data directory: {tf['dir']}/")

    # Save failed symbols for this timeframe
    if stats[suffix]["failed"]:
        failed_file = os.path.join(tf["dir"], f"_failed_symbols_{suffix}.txt")
        with open(failed_file, "w") as f:
            for sym in stats[suffix]["failed"]:
                f.write(f"{sym}\n")
        print(f"  Failed symbols saved to: {failed_file}")

# Overall summary
total_successful = sum(stats[tf["suffix"]]["successful"] for tf in TIMEFRAMES)
total_failed = sum(len(stats[tf["suffix"]]["failed"]) for tf in TIMEFRAMES)
overall_success_rate = (total_successful / total_operations * 100) if total_operations > 0 else 0

print("\n--- Overall Summary ---")
print(f"Total successful downloads: {total_successful}")
print(f"Total failures: {total_failed}")
print(f"Overall success rate: {overall_success_rate:.1f}%")

# Create a summary file
summary_file = "gateio_collection_summary.txt"
with open(summary_file, "w") as f:
    f.write(f"Gate.io Collection Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*70 + "\n\n")
    f.write(f"Exchange: GATE.IO\n")
    f.write(f"Total symbols: {len(symbols)}\n")
    f.write(f"Timeframes: {', '.join(tf['suffix'] for tf in TIMEFRAMES)}\n")
    f.write(f"Bars per symbol: {N_BARS}\n\n")

    for tf in TIMEFRAMES:
        suffix = tf["suffix"]
        f.write(f"\n{suffix.upper()} Timeframe:\n")
        f.write(f"  Successful: {stats[suffix]['successful']}\n")
        f.write(f"  Failed: {len(stats[suffix]['failed'])}\n")
        if stats[suffix]["failed"]:
            f.write(f"  Failed symbols: {', '.join(stats[suffix]['failed'][:10])}")
            if len(stats[suffix]["failed"]) > 10:
                f.write(f" ... and {len(stats[suffix]['failed']) - 10} more")
            f.write("\n")

print(f"\nSummary saved to: {summary_file}")
print("="*70)

# Display estimated data coverage
print("\n--- Data Coverage (with 5,000 bars) ---")
print("1-minute:  ~3.5 days")
print("5-minute:  ~17 days")
print("15-minute: ~52 days")
print("1-hour:    ~208 days (6.9 months)")
print("4-hour:    ~833 days (2.3 years)")
print("Daily:     ~13.7 years")
print("="*70)
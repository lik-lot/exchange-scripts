#!/usr/bin/env python3
"""
Universal Exchange Format Tester for TradingView
Tests different exchange names and symbol formats to find working combinations
Run this for any exchange before using the main data collection script
"""

import os
import time
import logging
from tvDatafeed import TvDatafeed, Interval

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

USERNAME = os.getenv("TV_USER")
PASSWORD = os.getenv("TV_PASS")

def test_exchange_formats(exchange_info):
    """
    Test different exchange names and symbol formats
    
    exchange_info format:
    {
        "name": "BTSE",
        "possible_exchanges": ["BTSE", "BTSE_SPOT", "BTSE_FUTURES", etc.],
        "test_symbols": [
            ("API_SYMBOL", ["TV_FORMAT1", "TV_FORMAT2", etc.])
        ]
    }
    """
    
    print(f"\n{'='*60}")
    print(f"🧪 TESTING {exchange_info['name']} EXCHANGE FORMATS")
    print(f"{'='*60}")
    
    # Initialize TradingView
    try:
        tv = TvDatafeed(USERNAME, PASSWORD) if USERNAME and PASSWORD else TvDatafeed()
        logging.info("✅ TradingView session established")
    except Exception as e:
        logging.error(f"❌ TradingView connection failed: {e}")
        return None, None
    
    # Test each possible exchange name
    for exchange in exchange_info["possible_exchanges"]:
        logging.info(f"\n🔍 Testing exchange: {exchange}")
        working_count = 0
        working_format = None
        
        for api_symbol, tv_formats in exchange_info["test_symbols"]:
            logging.info(f"\n  Testing {api_symbol}:")
            
            for tv_format in tv_formats:
                try:
                    logging.info(f"    {api_symbol} -> {tv_format}")
                    time.sleep(1)  # Rate limiting
                    
                    df = tv.get_hist(
                        symbol=tv_format,
                        exchange=exchange,
                        interval=Interval.in_daily,
                        n_bars=3
                    )
                    
                    if df is not None and not df.empty and len(df) > 0:
                        logging.info(f"    ✅ SUCCESS! {tv_format} works on {exchange}")
                        working_count += 1
                        
                        # Determine format pattern
                        if "-" in api_symbol:
                            if tv_format == api_symbol.replace("-", ""):
                                working_format = "remove_dash"
                            elif tv_format == api_symbol:
                                working_format = "keep_dash"
                            elif "/" in tv_format:
                                working_format = "use_slash"
                        
                        break  # Found working format for this symbol
                    else:
                        logging.info(f"    ❌ No data")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    if "no data" in error_msg or "timeout" in error_msg:
                        logging.info(f"    ❌ {e}")
                    else:
                        logging.warning(f"    ⚠️  Error: {e}")
        
        # If we found multiple working symbols on this exchange, it's good
        if working_count >= 2:
            logging.info(f"\n🎉 FOUND WORKING CONFIGURATION:")
            logging.info(f"   Exchange: {exchange}")
            logging.info(f"   Format: {working_format or 'keep_original'}")
            logging.info(f"   Working symbols: {working_count}")
            return exchange, working_format or "keep_original"
        elif working_count == 1:
            logging.info(f"\n⚠️  Only 1 symbol worked on {exchange} - might work but not reliable")
    
    logging.error(f"\n❌ No working exchange found for {exchange_info['name']}")
    return None, None

def main():
    # Test remaining exchanges (excluding already working ones: BTSE, BYBIT, BINANCE, KRAKEN, GATEIO, COINBASE, BITGET)
    exchanges_to_test = [
        {
            "name": "KUCOIN",
            "possible_exchanges": ["KUCOIN", "KUCOIN_SPOT", "KCS"],
            "test_symbols": [
                ("BTC-USDT", ["BTCUSDT", "BTC-USDT", "BTCUSD"]),
                ("ETH-USDT", ["ETHUSDT", "ETH-USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "OKX",
            "possible_exchanges": ["OKX", "OKB", "OKEX"],
            "test_symbols": [
                ("BTC-USDT", ["BTCUSDT", "BTC-USDT", "BTCUSD"]),
                ("ETH-USDT", ["ETHUSDT", "ETH-USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "MEXC",
            "possible_exchanges": ["MEXC", "MEXC_GLOBAL", "MX"],
            "test_symbols": [
                ("BTCUSDT", ["BTCUSDT", "BTCUSD", "BTC/USDT"]),
                ("ETHUSDT", ["ETHUSDT", "ETHUSD", "ETH/USDT"]),
            ]
        },
        {
            "name": "HTX",
            "possible_exchanges": ["HTX", "HUOBI", "HUOBI_GLOBAL"],
            "test_symbols": [
                ("btcusdt", ["BTCUSDT", "btcusdt", "BTCUSD"]),
                ("ethusdt", ["ETHUSDT", "ethusdt", "ETHUSD"]),
            ]
        },
        {
            "name": "BITMART",
            "possible_exchanges": ["BITMART", "BMX"],
            "test_symbols": [
                ("BTC_USDT", ["BTCUSDT", "BTC_USDT", "BTCUSD"]),
                ("ETH_USDT", ["ETHUSDT", "ETH_USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "GEMINI",
            "possible_exchanges": ["GEMINI", "GEMINI_EXCHANGE"],
            "test_symbols": [
                ("BTCUSD", ["BTCUSD", "BTC/USD", "BTC-USD"]),
                ("ETHUSD", ["ETHUSD", "ETH/USD", "ETH-USD"]),
            ]
        },
        {
            "name": "CRYPTOCOM",
            "possible_exchanges": ["CRYPTOCOM", "CRYPTO_COM", "CRO"],
            "test_symbols": [
                ("BTC_USD", ["BTCUSD", "BTC_USD", "BTC/USD"]),
                ("ETH_USD", ["ETHUSD", "ETH_USD", "ETH/USD"]),
            ]
        },
        {
            "name": "BITRUE",
            "possible_exchanges": ["BITRUE", "BTR"],
            "test_symbols": [
                ("BTCUSDT", ["BTCUSDT", "BTCUSD", "BTC/USDT"]),
                ("ETHUSDT", ["ETHUSDT", "ETHUSD", "ETH/USDT"]),
            ]
        },
        {
            "name": "COINEX",
            "possible_exchanges": ["COINEX", "CET"],
            "test_symbols": [
                ("BTCUSDT", ["BTCUSDT", "BTCUSD", "BTC/USDT"]),
                ("ETHUSDT", ["ETHUSDT", "ETHUSD", "ETH/USDT"]),
            ]
        },
        {
            "name": "LBANK",
            "possible_exchanges": ["LBANK", "LBK"],
            "test_symbols": [
                ("btc_usdt", ["BTCUSDT", "btc_usdt", "BTCUSD"]),
                ("eth_usdt", ["ETHUSDT", "eth_usdt", "ETHUSD"]),
            ]
        },
        {
            "name": "WHITEBIT",
            "possible_exchanges": ["WHITEBIT", "WBT"],
            "test_symbols": [
                ("BTC_USDT", ["BTCUSDT", "BTC_USDT", "BTCUSD"]),
                ("ETH_USDT", ["ETHUSDT", "ETH_USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "DIGIFINEX",
            "possible_exchanges": ["DIGIFINEX", "DFT"],
            "test_symbols": [
                ("btc_usdt", ["BTCUSDT", "btc_usdt", "BTCUSD"]),
                ("eth_usdt", ["ETHUSDT", "eth_usdt", "ETHUSD"]),
            ]
        },
        {
            "name": "TOOBIT",
            "possible_exchanges": ["TOOBIT", "TBT"],
            "test_symbols": [
                ("BTCUSDT", ["BTCUSDT", "BTCUSD", "BTC/USDT"]),
                ("ETHUSDT", ["ETHUSDT", "ETHUSD", "ETH/USDT"]),
            ]
        },
        {
            "name": "DEEPCOIN",
            "possible_exchanges": ["DEEPCOIN", "DC"],
            "test_symbols": [
                ("BTC-USDT", ["BTCUSDT", "BTC-USDT", "BTCUSD"]),
                ("ETH-USDT", ["ETHUSDT", "ETH-USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "PIONEX",
            "possible_exchanges": ["PIONEX", "PNX"],
            "test_symbols": [
                ("BTC_USDT", ["BTCUSDT", "BTC_USDT", "BTCUSD"]),
                ("ETH_USDT", ["ETHUSDT", "ETH_USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "COINW",
            "possible_exchanges": ["COINW", "CW"],
            "test_symbols": [
                ("BTCUSDT", ["BTCUSDT", "BTCUSD", "BTC/USDT"]),
                ("ETHUSDT", ["ETHUSDT", "ETHUSD", "ETH/USDT"]),
            ]
        },
        {
            "name": "BIGONE",
            "possible_exchanges": ["BIGONE", "BIG"],
            "test_symbols": [
                ("BTC-USDT", ["BTCUSDT", "BTC-USDT", "BTCUSD"]),
                ("ETH-USDT", ["ETHUSDT", "ETH-USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "BICONOMY",
            "possible_exchanges": ["BICONOMY", "BICO"],
            "test_symbols": [
                ("BTC_USDT", ["BTCUSDT", "BTC_USDT", "BTCUSD"]),
                ("ETH_USDT", ["ETHUSDT", "ETH_USDT", "ETHUSD"]),
            ]
        },
        {
            "name": "HASHKEYGLOBAL",
            "possible_exchanges": ["HASHKEYGLOBAL", "HASHKEY", "HSK"],
            "test_symbols": [
                ("BTC-USDT", ["BTCUSDT", "BTC-USDT", "BTCUSD"]),
                ("ETH-USDT", ["ETHUSDT", "ETH-USDT", "ETHUSD"]),
            ]
        }
    ]
    
    results = {}
    
    for exchange_info in exchanges_to_test:
        working_exchange, working_format = test_exchange_formats(exchange_info)
        results[exchange_info["name"]] = {
            "exchange": working_exchange,
            "format": working_format
        }
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 TESTING SUMMARY")
    print(f"{'='*60}")
    
    for name, result in results.items():
        if result["exchange"]:
            print(f"✅ {name:10} -> {result['exchange']:15} (format: {result['format']})")
        else:
            print(f"❌ {name:10} -> No working configuration found")
    
    print(f"\n💡 Next steps:")
    print("1. Update your exchange scripts with the working configurations above")
    print("2. Use the identified exchange names and symbol formats")
    print("3. Add symbol validation like the Coinbase script")

if __name__ == "__main__":
    main()
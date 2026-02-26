"""Async mass downloader for crypto OHLCV data via ccxt."""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import ccxt.async_support as ccxt_async
import pandas as pd

from .cache import DataCache


class CryptoDownloader:
    """Downloads historical OHLCV candles using ccxt with automatic pagination."""

    OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, config: dict):
        ing_cfg = config["ingestion"]
        self.exchange_id = ing_cfg.get("exchange", "binance")
        self.symbols = ing_cfg.get("symbols", [])
        self.timeframe = ing_cfg.get("timeframe", "1m")
        self.lookback_days = ing_cfg.get("lookback_days", 30)
        self.rate_limit_ms = ing_cfg.get("rate_limit_ms", 100)

        cache_cfg = ing_cfg.get("cache", {})
        self.cache_enabled = cache_cfg.get("enabled", True)
        self.cache = DataCache(
            cache_dir=cache_cfg.get("directory", "data/cache"),
            fmt=cache_cfg.get("format", "parquet"),
        )

    def _create_exchange(self):
        exchange_class = getattr(ccxt_async, self.exchange_id)
        return exchange_class(
            {"enableRateLimit": True, "rateLimit": self.rate_limit_ms}
        )

    def _to_dataframe(self, raw_ohlcv: list) -> pd.DataFrame:
        df = pd.DataFrame(raw_ohlcv, columns=self.OHLCV_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        df = df.astype(
            {
                "open": "float64",
                "high": "float64",
                "low": "float64",
                "close": "float64",
                "volume": "float64",
            }
        )
        return df

    async def _fetch_symbol(self, exchange, symbol: str) -> pd.DataFrame:
        """Fetch all candles for a single symbol with pagination."""
        now = datetime.now(timezone.utc)
        since = int((now - timedelta(days=self.lookback_days)).timestamp() * 1000)
        limit = 1000  # max candles per request for most exchanges

        all_ohlcv = []
        fetch_since = since

        while True:
            try:
                ohlcv = await exchange.fetch_ohlcv(
                    symbol,
                    timeframe=self.timeframe,
                    since=fetch_since,
                    limit=limit,
                )
            except Exception as e:
                print(f"  [WARN] Error fetching {symbol} at {fetch_since}: {e}")
                break

            if not ohlcv:
                break

            all_ohlcv.extend(ohlcv)
            last_ts = ohlcv[-1][0]

            # Move past the last candle
            fetch_since = last_ts + 1

            if len(ohlcv) < limit:
                break

            await asyncio.sleep(self.rate_limit_ms / 1000.0)

        if not all_ohlcv:
            return pd.DataFrame(columns=self.OHLCV_COLUMNS).set_index("timestamp")

        df = self._to_dataframe(all_ohlcv)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        print(f"  [OK] {symbol}: {len(df)} candles downloaded")
        return df

    async def download_all_async(self) -> Dict[str, pd.DataFrame]:
        """Download data for all configured symbols."""
        exchange = self._create_exchange()
        results = {}

        try:
            for symbol in self.symbols:
                # Check cache first
                if self.cache_enabled and self.cache.has_cache(
                    symbol, self.timeframe
                ):
                    cached = self.cache.load(symbol, self.timeframe)
                    if cached is not None and len(cached) > 0:
                        last_cached = cached.index.max()
                        now = datetime.now(timezone.utc)
                        gap_minutes = (now - last_cached).total_seconds() / 60

                        if gap_minutes < 2:
                            print(f"  [CACHE] {symbol}: {len(cached)} candles (fresh)")
                            results[symbol] = cached
                            continue

                        # Incremental update: only fetch missing data
                        print(f"  [CACHE] {symbol}: updating from {last_cached}...")

                df = await self._fetch_symbol(exchange, symbol)

                if self.cache_enabled and len(df) > 0:
                    df = self.cache.update(df, symbol, self.timeframe)

                results[symbol] = df

        finally:
            await exchange.close()

        return results

    def download_all(self) -> Dict[str, pd.DataFrame]:
        """Synchronous wrapper around download_all_async."""
        return asyncio.run(self.download_all_async())

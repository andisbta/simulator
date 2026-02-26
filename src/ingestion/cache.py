"""Parquet/CSV caching layer for OHLCV data."""

import os
from pathlib import Path
from typing import Optional

import pandas as pd


class DataCache:
    """Manages local caching of OHLCV data to avoid redundant API calls."""

    def __init__(self, cache_dir: str = "data/cache", fmt: str = "parquet"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.fmt = fmt

    def _cache_path(self, symbol: str, timeframe: str) -> Path:
        safe_symbol = symbol.replace("/", "_")
        return self.cache_dir / f"{safe_symbol}_{timeframe}.{self.fmt}"

    def has_cache(self, symbol: str, timeframe: str) -> bool:
        return self._cache_path(symbol, timeframe).exists()

    def load(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        path = self._cache_path(symbol, timeframe)
        if not path.exists():
            return None

        if self.fmt == "parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, parse_dates=["timestamp"])

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp") if "timestamp" in df.columns else df
        return df

    def save(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Path:
        path = self._cache_path(symbol, timeframe)
        out = df.copy()

        if out.index.name == "timestamp":
            out = out.reset_index()

        if self.fmt == "parquet":
            out.to_parquet(path, index=False)
        else:
            out.to_csv(path, index=False)

        return path

    def update(
        self, new_df: pd.DataFrame, symbol: str, timeframe: str
    ) -> pd.DataFrame:
        """Append new rows to an existing cache (deduplicated by timestamp)."""
        existing = self.load(symbol, timeframe)

        if existing is not None:
            combined = pd.concat([existing, new_df])
            combined = combined[~combined.index.duplicated(keep="last")]
            combined = combined.sort_index()
        else:
            combined = new_df

        self.save(combined, symbol, timeframe)
        return combined

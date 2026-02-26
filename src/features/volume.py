"""Volume analysis: VWAP, Volume Spikes.

Implemented with pure pandas/numpy — no external TA library required.
"""

import numpy as np
import pandas as pd


def _vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Compute VWAP (Volume Weighted Average Price).

    Resets cumulatively each day for intraday data.
    """
    typical_price = (high + low + close) / 3.0
    tp_volume = typical_price * volume

    # Group by date for daily VWAP reset
    dates = high.index.date
    cum_tp_vol = tp_volume.groupby(dates).cumsum()
    cum_vol = volume.groupby(dates).cumsum()

    return cum_tp_vol / cum_vol.replace(0, np.nan)


def compute_volume_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Add volume-based indicators to the DataFrame based on config."""
    vol_cfg = config.get("features", {}).get("volume", {})

    # VWAP
    if vol_cfg.get("vwap", {}).get("enabled", True):
        df["VWAP"] = _vwap(df["high"], df["low"], df["close"], df["volume"])

    # Volume Spikes
    spike_cfg = vol_cfg.get("volume_spike", {})
    ma_period = spike_cfg.get("ma_period", 20)
    threshold = spike_cfg.get("threshold", 3.0)

    vol_ma = df["volume"].rolling(window=ma_period).mean()
    df[f"volume_ma_{ma_period}"] = vol_ma
    df[f"volume_ratio_{ma_period}"] = df["volume"] / vol_ma.replace(0, np.nan)
    df[f"volume_spike_{ma_period}_{threshold}"] = (
        df[f"volume_ratio_{ma_period}"] >= threshold
    )

    return df

"""Volatility indicators: ATR, Bollinger Bands Width, Z-Scores.

Implemented with pure pandas/numpy — no external TA library required.
"""

import numpy as np
import pandas as pd


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Compute Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def _bollinger_bands(
    series: pd.Series, period: int, std_dev: float
) -> pd.DataFrame:
    """Compute Bollinger Bands (upper, mid, lower)."""
    mid = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std

    return pd.DataFrame(
        {
            f"BBU_{period}_{std_dev}": upper,
            f"BBM_{period}_{std_dev}": mid,
            f"BBL_{period}_{std_dev}": lower,
        }
    )


def compute_volatility(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Add volatility indicators to the DataFrame based on config."""
    vol_cfg = config.get("features", {}).get("volatility", {})

    # ATR
    for period in vol_cfg.get("atr", {}).get("periods", [14]):
        df[f"ATR_{period}"] = _atr(df["high"], df["low"], df["close"], period)

    # Bollinger Bands
    for bb_params in vol_cfg.get("bollinger", [{"period": 20, "std_dev": 2.0}]):
        period = bb_params["period"]
        std = bb_params["std_dev"]
        bb = _bollinger_bands(df["close"], period, std)
        df = pd.concat([df, bb], axis=1)

        # Bollinger Band Width
        upper_col = f"BBU_{period}_{std}"
        lower_col = f"BBL_{period}_{std}"
        mid_col = f"BBM_{period}_{std}"
        if upper_col in df.columns and lower_col in df.columns:
            df[f"BBW_{period}_{std}"] = (
                (df[upper_col] - df[lower_col]) / df[mid_col]
            )

    # Z-Score of price changes
    for period in vol_cfg.get("zscore", {}).get("periods", [20]):
        pct_change = df["close"].pct_change()
        rolling_mean = pct_change.rolling(window=period).mean()
        rolling_std = pct_change.rolling(window=period).std()
        df[f"zscore_{period}"] = (pct_change - rolling_mean) / rolling_std.replace(
            0, np.nan
        )

    return df

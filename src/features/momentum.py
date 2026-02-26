"""Momentum & oscillator indicators: RSI, MACD, ROC.

Implemented with pure pandas/numpy — no external TA library required.
"""

import numpy as np
import pandas as pd


def _rsi(series: pd.Series, period: int) -> pd.Series:
    """Compute RSI (Relative Strength Index) using Wilder's smoothing."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(
    series: pd.Series, fast: int, slow: int, signal: int
) -> pd.DataFrame:
    """Compute MACD line, signal line, and histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    suffix = f"{fast}_{slow}_{signal}"
    return pd.DataFrame(
        {
            f"MACD_{suffix}": macd_line,
            f"MACDs_{suffix}": signal_line,
            f"MACDh_{suffix}": histogram,
        }
    )


def _roc(series: pd.Series, period: int) -> pd.Series:
    """Compute Rate of Change (percent)."""
    return series.pct_change(periods=period) * 100.0


def compute_momentum(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Add momentum indicators to the DataFrame based on config."""
    mom_cfg = config.get("features", {}).get("momentum", {})

    # RSI
    for period in mom_cfg.get("rsi", {}).get("periods", [14]):
        df[f"RSI_{period}"] = _rsi(df["close"], period)

    # MACD
    for macd_params in mom_cfg.get("macd", [{"fast": 12, "slow": 26, "signal": 9}]):
        fast = macd_params["fast"]
        slow = macd_params["slow"]
        signal = macd_params["signal"]
        macd_result = _macd(df["close"], fast, slow, signal)
        df = pd.concat([df, macd_result], axis=1)

        # Generate _prev columns for crossover detection
        hist_col = f"MACDh_{fast}_{slow}_{signal}"
        if hist_col in df.columns:
            df[f"{hist_col}_prev"] = df[hist_col].shift(1)

    # Rate of Change
    for period in mom_cfg.get("roc", {}).get("periods", [10]):
        df[f"ROC_{period}"] = _roc(df["close"], period)

    return df

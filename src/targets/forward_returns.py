"""Forward returns and target variable calculation."""

import numpy as np
import pandas as pd


class ForwardReturnsCalculator:
    """Calculates forward-looking return metrics for each timestamp.

    Uses vectorized shift operations to compute what happens AFTER
    each candle across multiple time horizons.
    """

    def __init__(self, config: dict):
        fr_cfg = config.get("forward_returns", {})
        self.horizons = fr_cfg.get("horizons_minutes", [5, 15, 30, 60])
        self.metrics = fr_cfg.get("metrics", ["return"])

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add forward return columns to the DataFrame."""
        df = df.copy()
        close = df["close"]
        high = df["high"]
        low = df["low"]

        for horizon in self.horizons:
            if "return" in self.metrics:
                # Simple forward return: (future_close - current_close) / current_close
                future_close = close.shift(-horizon)
                df[f"return_{horizon}m"] = (future_close - close) / close

            if "max_drawdown" in self.metrics:
                # Maximum drawdown within the forward window
                df[f"max_drawdown_{horizon}m"] = self._rolling_max_drawdown(
                    low, close, horizon
                )

            if "max_runup" in self.metrics:
                # Maximum run-up within the forward window
                df[f"max_runup_{horizon}m"] = self._rolling_max_runup(
                    high, close, horizon
                )

        return df

    @staticmethod
    def _rolling_max_drawdown(
        low: pd.Series, close: pd.Series, horizon: int
    ) -> pd.Series:
        """Compute the worst (most negative) drawdown in the next N bars.

        For each bar i, looks at the minimum low in bars [i+1, i+horizon]
        relative to close[i].
        """
        # Shift low forward by 1 so we look at future bars only
        future_low_min = (
            low.shift(-1)
            .rolling(window=horizon, min_periods=1)
            .min()
            .shift(-(horizon - 1))
        )
        # Alternative approach: iterate-free using rolling on reversed series
        # For correctness, use a simpler forward-looking approach
        result = pd.Series(np.nan, index=close.index)
        low_vals = low.values
        close_vals = close.values
        n = len(close_vals)

        for i in range(n - 1):
            end = min(i + 1 + horizon, n)
            if end <= i + 1:
                continue
            window_low = np.min(low_vals[i + 1 : end])
            result.iloc[i] = (window_low - close_vals[i]) / close_vals[i]

        return result

    @staticmethod
    def _rolling_max_runup(
        high: pd.Series, close: pd.Series, horizon: int
    ) -> pd.Series:
        """Compute the best (most positive) run-up in the next N bars."""
        result = pd.Series(np.nan, index=close.index)
        high_vals = high.values
        close_vals = close.values
        n = len(close_vals)

        for i in range(n - 1):
            end = min(i + 1 + horizon, n)
            if end <= i + 1:
                continue
            window_high = np.max(high_vals[i + 1 : end])
            result.iloc[i] = (window_high - close_vals[i]) / close_vals[i]

        return result

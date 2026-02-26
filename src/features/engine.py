"""Feature Engineering Orchestrator – composes all feature modules."""

import pandas as pd

from .momentum import compute_momentum
from .volatility import compute_volatility
from .volume import compute_volume_features
from .time_features import compute_time_features
from .rolling import compute_rolling_features


class FeatureEngine:
    """Orchestrates feature generation from raw OHLCV data.

    Takes a config dict and applies all enabled feature modules
    in sequence, returning the enriched DataFrame.
    """

    def __init__(self, config: dict):
        self.config = config

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature modules to the OHLCV DataFrame."""
        df = df.copy()

        df = compute_momentum(df, self.config)
        df = compute_volatility(df, self.config)
        df = compute_volume_features(df, self.config)
        df = compute_time_features(df, self.config)
        df = compute_rolling_features(df, self.config)

        return df

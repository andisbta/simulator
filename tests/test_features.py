"""Tests for the feature engineering modules."""

import numpy as np
import pandas as pd
import pytest

from src.features.engine import FeatureEngine
from src.features.momentum import compute_momentum
from src.features.rolling import compute_rolling_features
from src.features.time_features import compute_time_features
from src.features.volatility import compute_volatility
from src.features.volume import compute_volume_features


@pytest.fixture
def sample_ohlcv():
    """Create a synthetic OHLCV DataFrame with 200 1-minute bars."""
    np.random.seed(42)
    n = 200
    timestamps = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")

    close = 100 + np.cumsum(np.random.randn(n) * 0.1)
    high = close + np.abs(np.random.randn(n) * 0.05)
    low = close - np.abs(np.random.randn(n) * 0.05)
    open_ = close + np.random.randn(n) * 0.03
    volume = np.abs(np.random.randn(n) * 1000) + 500

    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=timestamps,
    )
    df.index.name = "timestamp"
    return df


@pytest.fixture
def config():
    """Minimal config for testing."""
    return {
        "features": {
            "momentum": {
                "rsi": {"periods": [14]},
                "macd": [{"fast": 12, "slow": 26, "signal": 9}],
                "roc": {"periods": [10]},
            },
            "volatility": {
                "atr": {"periods": [14]},
                "bollinger": [{"period": 20, "std_dev": 2.0}],
                "zscore": {"periods": [20]},
            },
            "volume": {
                "vwap": {"enabled": True},
                "volume_spike": {"ma_period": 20, "threshold": 3.0},
            },
            "time": {
                "features": ["day_of_week", "hour", "minute", "minute_of_day"]
            },
            "rolling": {
                "windows": [5, 15],
                "metrics": ["min", "max", "mean"],
                "columns": ["close"],
            },
        }
    }


class TestMomentum:
    def test_rsi_created(self, sample_ohlcv, config):
        result = compute_momentum(sample_ohlcv, config)
        assert "RSI_14" in result.columns
        # RSI should be between 0 and 100 (ignoring NaN warmup)
        valid = result["RSI_14"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_macd_columns_created(self, sample_ohlcv, config):
        result = compute_momentum(sample_ohlcv, config)
        assert "MACDh_12_26_9" in result.columns
        assert "MACDh_12_26_9_prev" in result.columns

    def test_roc_created(self, sample_ohlcv, config):
        result = compute_momentum(sample_ohlcv, config)
        assert "ROC_10" in result.columns


class TestVolatility:
    def test_atr_created(self, sample_ohlcv, config):
        result = compute_volatility(sample_ohlcv, config)
        assert "ATR_14" in result.columns
        valid = result["ATR_14"].dropna()
        assert (valid >= 0).all()

    def test_bollinger_width(self, sample_ohlcv, config):
        result = compute_volatility(sample_ohlcv, config)
        assert "BBW_20_2.0" in result.columns

    def test_zscore(self, sample_ohlcv, config):
        result = compute_volatility(sample_ohlcv, config)
        assert "zscore_20" in result.columns


class TestVolume:
    def test_vwap(self, sample_ohlcv, config):
        result = compute_volume_features(sample_ohlcv, config)
        assert "VWAP" in result.columns

    def test_volume_spike(self, sample_ohlcv, config):
        result = compute_volume_features(sample_ohlcv, config)
        assert "volume_spike_20_3.0" in result.columns
        assert result["volume_spike_20_3.0"].dtype == bool


class TestTimeFeatures:
    def test_time_columns(self, sample_ohlcv, config):
        result = compute_time_features(sample_ohlcv, config)
        assert "day_of_week" in result.columns
        assert "hour" in result.columns
        assert "minute" in result.columns
        assert "minute_of_day" in result.columns

    def test_minute_of_day_range(self, sample_ohlcv, config):
        result = compute_time_features(sample_ohlcv, config)
        assert result["minute_of_day"].min() >= 0
        assert result["minute_of_day"].max() < 1440


class TestRolling:
    def test_rolling_columns(self, sample_ohlcv, config):
        result = compute_rolling_features(sample_ohlcv, config)
        assert "close_rolling_min_5" in result.columns
        assert "close_rolling_max_15" in result.columns
        assert "close_rolling_mean_5" in result.columns


class TestFeatureEngine:
    def test_full_pipeline(self, sample_ohlcv, config):
        engine = FeatureEngine(config)
        result = engine.compute(sample_ohlcv)
        # Should have significantly more columns than the original 5
        assert len(result.columns) > 20
        # Original columns should still be there
        for col in ["open", "high", "low", "close", "volume"]:
            assert col in result.columns

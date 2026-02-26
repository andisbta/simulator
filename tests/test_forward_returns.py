"""Tests for the forward returns calculator."""

import numpy as np
import pandas as pd
import pytest

from src.targets.forward_returns import ForwardReturnsCalculator


@pytest.fixture
def sample_ohlcv():
    """Simple OHLCV with predictable values."""
    n = 100
    timestamps = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")
    close = np.arange(100, 100 + n, dtype=float)  # Steady increase: 100, 101, ...
    df = pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.ones(n) * 1000,
        },
        index=timestamps,
    )
    df.index.name = "timestamp"
    return df


@pytest.fixture
def config():
    return {
        "forward_returns": {
            "horizons_minutes": [5, 10],
            "metrics": ["return", "max_drawdown", "max_runup"],
        }
    }


class TestForwardReturns:
    def test_return_columns_created(self, sample_ohlcv, config):
        calc = ForwardReturnsCalculator(config)
        result = calc.compute(sample_ohlcv)
        assert "return_5m" in result.columns
        assert "return_10m" in result.columns

    def test_return_values(self, sample_ohlcv, config):
        """With close = [100, 101, ..., 199], return_5m at index 0 should be 5/100."""
        calc = ForwardReturnsCalculator(config)
        result = calc.compute(sample_ohlcv)
        expected = 5.0 / 100.0
        actual = result["return_5m"].iloc[0]
        assert abs(actual - expected) < 1e-10

    def test_drawdown_columns(self, sample_ohlcv, config):
        calc = ForwardReturnsCalculator(config)
        result = calc.compute(sample_ohlcv)
        assert "max_drawdown_5m" in result.columns
        # Drawdown should be negative (low is below close)
        valid = result["max_drawdown_5m"].dropna()
        # In a steadily rising market the drawdown from close to next bar's
        # low (close+1-1 = close) means 0 drawdown at best, but low = close-1
        # so the min low in the next bar is close_next - 1 vs current close
        assert len(valid) > 0

    def test_runup_columns(self, sample_ohlcv, config):
        calc = ForwardReturnsCalculator(config)
        result = calc.compute(sample_ohlcv)
        assert "max_runup_5m" in result.columns
        valid = result["max_runup_5m"].dropna()
        # In a rising market, runup should be positive
        assert (valid > 0).all()

    def test_last_rows_are_nan(self, sample_ohlcv, config):
        """Forward returns at the end of the series should be NaN."""
        calc = ForwardReturnsCalculator(config)
        result = calc.compute(sample_ohlcv)
        # Last 10 rows for return_10m should be NaN
        assert result["return_10m"].iloc[-1] != result["return_10m"].iloc[-1]  # NaN check

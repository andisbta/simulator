"""Tests for the statistical analyzer."""

import numpy as np
import pandas as pd
import pytest

from src.rules.parser import EvaluationTarget, Pattern, Condition
from src.stats.analyzer import StatisticalAnalyzer


@pytest.fixture
def config():
    return {
        "statistics": {
            "min_sample_size": 10,
            "confidence_level": 0.95,
            "report": {"format": "csv", "output_dir": "output/results"},
        }
    }


@pytest.fixture
def sample_df():
    """DataFrame with known forward returns."""
    np.random.seed(42)
    n = 200
    timestamps = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {
            "close": np.linspace(100, 110, n),
            "return_15m": np.random.randn(n) * 0.005 + 0.001,  # Slight positive bias
        },
        index=timestamps,
    )
    df.index.name = "timestamp"
    return df


@pytest.fixture
def pattern():
    return Pattern(
        name="Test Pattern",
        description="",
        conditions=[],
        evaluate=EvaluationTarget(target="return_15m", direction="long"),
    )


class TestStatisticalAnalyzer:
    def test_basic_analysis(self, config, sample_df, pattern):
        analyzer = StatisticalAnalyzer(config)
        mask = pd.Series(True, index=sample_df.index)

        result = analyzer.analyze_pattern(
            df=sample_df,
            mask=mask,
            pattern_name="Test",
            target_column="return_15m",
            direction="long",
        )

        assert result is not None
        assert result.sample_size == 200
        assert 0 <= result.win_rate <= 1
        assert result.std_return > 0
        assert isinstance(result.t_statistic, float)
        assert isinstance(result.p_value, float)

    def test_insufficient_sample(self, sample_df, pattern):
        config = {
            "statistics": {"min_sample_size": 300, "confidence_level": 0.95}
        }
        analyzer = StatisticalAnalyzer(config)
        mask = pd.Series(True, index=sample_df.index)

        result = analyzer.analyze_pattern(
            df=sample_df,
            mask=mask,
            pattern_name="Test",
            target_column="return_15m",
        )
        assert result is None

    def test_short_direction_flips(self, config, sample_df, pattern):
        analyzer = StatisticalAnalyzer(config)
        mask = pd.Series(True, index=sample_df.index)

        long_result = analyzer.analyze_pattern(
            sample_df, mask, "Test", "return_15m", direction="long"
        )
        short_result = analyzer.analyze_pattern(
            sample_df, mask, "Test", "return_15m", direction="short"
        )

        assert long_result is not None
        assert short_result is not None
        # Mean returns should be approximately opposite
        assert abs(long_result.mean_return + short_result.mean_return) < 1e-10

    def test_to_dataframe(self, config, sample_df, pattern):
        analyzer = StatisticalAnalyzer(config)
        mask = pd.Series(True, index=sample_df.index)

        result = analyzer.analyze_pattern(
            sample_df, mask, "Test", "return_15m"
        )
        summary = analyzer.to_dataframe([result])

        assert len(summary) == 1
        assert "Pattern" in summary.columns
        assert "Win Rate (%)" in summary.columns
        assert "P-Value" in summary.columns
        assert "Significant" in summary.columns

    def test_empty_stats_list(self, config):
        analyzer = StatisticalAnalyzer(config)
        summary = analyzer.to_dataframe([])
        assert len(summary) == 0

    def test_analyze_all(self, config, sample_df):
        analyzer = StatisticalAnalyzer(config)

        patterns = [
            Pattern(
                name="P1",
                description="",
                conditions=[],
                evaluate=EvaluationTarget(target="return_15m", direction="long"),
            ),
            Pattern(
                name="P2",
                description="",
                conditions=[],
                evaluate=EvaluationTarget(target="return_15m", direction="short"),
            ),
        ]
        masks = {
            "P1": pd.Series(True, index=sample_df.index),
            "P2": pd.Series(True, index=sample_df.index),
        }

        results = analyzer.analyze_all(sample_df, masks, patterns)
        assert len(results) == 2

    def test_save_report_csv(self, config, sample_df, tmp_path):
        analyzer = StatisticalAnalyzer(config)
        mask = pd.Series(True, index=sample_df.index)
        result = analyzer.analyze_pattern(
            sample_df, mask, "Test", "return_15m"
        )

        path = analyzer.save_report([result], str(tmp_path), fmt="csv")
        assert path.endswith(".csv")

        loaded = pd.read_csv(path)
        assert len(loaded) == 1
        assert "Pattern" in loaded.columns

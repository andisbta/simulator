"""Tests for the rules engine (parser + evaluator)."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.rules.evaluator import RuleEvaluator
from src.rules.parser import Condition, EvaluationTarget, Pattern, PatternParser


@pytest.fixture
def sample_df():
    """DataFrame with known values for rule testing."""
    n = 100
    timestamps = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {
            "RSI_14": np.linspace(20, 80, n),
            "volume_spike_20_3.0": [True if i % 10 == 0 else False for i in range(n)],
            "minute": [i % 60 for i in range(n)],
            "close": np.linspace(100, 110, n),
            "return_15m": np.random.randn(n) * 0.01,
        },
        index=timestamps,
    )
    df.index.name = "timestamp"
    return df


@pytest.fixture
def simple_pattern():
    """A simple test pattern."""
    return Pattern(
        name="Test RSI Low",
        description="RSI below 30",
        conditions=[
            Condition(column="RSI_14", operator="<", value=30),
        ],
        evaluate=EvaluationTarget(target="return_15m", direction="long"),
    )


@pytest.fixture
def multi_condition_pattern():
    """Pattern with multiple conditions."""
    return Pattern(
        name="RSI + Volume Spike",
        description="RSI low with volume spike",
        conditions=[
            Condition(column="RSI_14", operator="<", value=40),
            Condition(column="volume_spike_20_3.0", operator="==", value=True),
        ],
        evaluate=EvaluationTarget(target="return_15m", direction="long"),
    )


class TestPatternParser:
    def test_parse_file(self):
        pattern_data = {
            "name": "Test Pattern",
            "description": "A test",
            "conditions": [
                {"column": "RSI_14", "operator": "<", "value": 30},
                {"column": "minute", "operator": "==", "value": 0},
            ],
            "evaluate": {"target": "return_15m", "direction": "long"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(pattern_data, f)
            f.flush()
            parser = PatternParser()
            pattern = parser.parse_file(f.name)

        assert pattern.name == "Test Pattern"
        assert len(pattern.conditions) == 2
        assert pattern.conditions[0].column == "RSI_14"
        assert pattern.evaluate.target == "return_15m"

    def test_invalid_operator_raises(self):
        pattern_data = {
            "name": "Bad Pattern",
            "description": "",
            "conditions": [
                {"column": "RSI_14", "operator": "LIKE", "value": 30},
            ],
            "evaluate": {"target": "return_15m"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(pattern_data, f)
            f.flush()
            parser = PatternParser()
            with pytest.raises(ValueError, match="Invalid operator"):
                parser.parse_file(f.name)

    def test_parse_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                data = {
                    "name": f"Pattern {i}",
                    "description": "",
                    "conditions": [
                        {"column": "RSI_14", "operator": "<", "value": 30 + i},
                    ],
                    "evaluate": {"target": "return_15m"},
                }
                with open(Path(tmpdir) / f"pattern_{i}.yaml", "w") as f:
                    yaml.dump(data, f)

            parser = PatternParser()
            patterns = parser.parse_directory(tmpdir)
            assert len(patterns) == 3

    def test_percentile_value_type(self):
        pattern_data = {
            "name": "Percentile Pattern",
            "description": "",
            "conditions": [
                {
                    "column": "RSI_14",
                    "operator": "<",
                    "value": 20,
                    "value_type": "percentile",
                },
            ],
            "evaluate": {"target": "return_15m"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(pattern_data, f)
            f.flush()
            parser = PatternParser()
            pattern = parser.parse_file(f.name)

        assert pattern.conditions[0].value_type == "percentile"


class TestRuleEvaluator:
    def test_simple_condition(self, sample_df, simple_pattern):
        evaluator = RuleEvaluator()
        mask = evaluator.evaluate_pattern(sample_df, simple_pattern)

        # RSI goes from 20 to 80, so some early values should be < 30
        assert mask.sum() > 0
        assert mask.sum() < len(sample_df)

        # All matching rows should indeed have RSI < 30
        assert (sample_df.loc[mask, "RSI_14"] < 30).all()

    def test_multi_condition(self, sample_df, multi_condition_pattern):
        evaluator = RuleEvaluator()
        mask = evaluator.evaluate_pattern(sample_df, multi_condition_pattern)

        matched = sample_df[mask]
        assert (matched["RSI_14"] < 40).all()
        assert (matched["volume_spike_20_3.0"] == True).all()

    def test_missing_column_raises(self, sample_df):
        pattern = Pattern(
            name="Missing Col",
            description="",
            conditions=[
                Condition(column="NONEXISTENT", operator=">", value=0),
            ],
            evaluate=EvaluationTarget(target="return_15m"),
        )
        evaluator = RuleEvaluator()
        with pytest.raises(KeyError):
            evaluator.evaluate_pattern(sample_df, pattern)

    def test_percentile_condition(self, sample_df):
        pattern = Pattern(
            name="Percentile Test",
            description="",
            conditions=[
                Condition(
                    column="RSI_14",
                    operator="<",
                    value=25,
                    value_type="percentile",
                ),
            ],
            evaluate=EvaluationTarget(target="return_15m"),
        )
        evaluator = RuleEvaluator()
        mask = evaluator.evaluate_pattern(sample_df, pattern)
        # Should match roughly 25% of rows
        assert 15 < mask.sum() < 35

    def test_evaluate_all_patterns(self, sample_df, simple_pattern, multi_condition_pattern):
        evaluator = RuleEvaluator()
        results = evaluator.evaluate_all_patterns(
            sample_df, [simple_pattern, multi_condition_pattern]
        )
        assert len(results) == 2
        assert "Test RSI Low" in results
        assert "RSI + Volume Spike" in results

    def test_get_matching_rows(self, sample_df, simple_pattern):
        evaluator = RuleEvaluator()
        matched = evaluator.get_matching_rows(sample_df, simple_pattern)
        assert len(matched) > 0
        assert (matched["RSI_14"] < 30).all()

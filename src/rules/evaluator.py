"""Vectorized rule evaluator – applies pattern conditions to DataFrames."""

import operator as op
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .parser import Condition, Pattern


class RuleEvaluator:
    """Evaluates pattern conditions against a DataFrame using vectorized operations."""

    OPERATOR_MAP = {
        "<": op.lt,
        "<=": op.le,
        ">": op.gt,
        ">=": op.ge,
        "==": op.eq,
        "!=": op.ne,
    }

    def evaluate_pattern(
        self, df: pd.DataFrame, pattern: Pattern
    ) -> pd.Series:
        """Evaluate all conditions and return a boolean mask of matching rows.

        Returns a pd.Series of booleans (True where all conditions are met).
        """
        mask = pd.Series(True, index=df.index)

        for condition in pattern.conditions:
            cond_mask = self._evaluate_condition(df, condition)
            mask = mask & cond_mask

        return mask

    def evaluate_all_patterns(
        self, df: pd.DataFrame, patterns: List[Pattern]
    ) -> Dict[str, pd.Series]:
        """Evaluate multiple patterns, returning a dict of {pattern_name: mask}."""
        results = {}
        for pattern in patterns:
            try:
                mask = self.evaluate_pattern(df, pattern)
                results[pattern.name] = mask
            except KeyError as e:
                print(
                    f"  [WARN] Pattern '{pattern.name}' skipped – "
                    f"missing column: {e}"
                )
            except Exception as e:
                print(f"  [WARN] Pattern '{pattern.name}' failed: {e}")
        return results

    def _evaluate_condition(
        self, df: pd.DataFrame, condition: Condition
    ) -> pd.Series:
        """Evaluate a single condition against the DataFrame."""
        if condition.column not in df.columns:
            raise KeyError(condition.column)

        series = df[condition.column]
        op_func = self.OPERATOR_MAP[condition.operator]

        # Resolve the comparison value
        if condition.value_type == "percentile":
            # Dynamic threshold: compute the percentile of the column
            threshold = np.nanpercentile(series.dropna(), condition.value)
            return op_func(series, threshold)
        else:
            return op_func(series, condition.value)

    def get_matching_rows(
        self, df: pd.DataFrame, pattern: Pattern
    ) -> pd.DataFrame:
        """Return only the rows where the pattern matches."""
        mask = self.evaluate_pattern(df, pattern)
        return df[mask]

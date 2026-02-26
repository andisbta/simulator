"""Statistical analysis of pattern performance."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class PatternStats:
    """Statistical summary for a single pattern."""

    pattern_name: str
    target_column: str
    direction: str
    sample_size: int
    win_rate: float
    mean_return: float
    median_return: float
    std_return: float
    min_return: float
    max_return: float
    sharpe_ratio: float
    t_statistic: float
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    significant: bool


class StatisticalAnalyzer:
    """Computes comprehensive statistics for pattern matches."""

    def __init__(self, config: dict):
        stats_cfg = config.get("statistics", {})
        self.min_sample_size = stats_cfg.get("min_sample_size", 30)
        self.confidence_level = stats_cfg.get("confidence_level", 0.95)

    def analyze_pattern(
        self,
        df: pd.DataFrame,
        mask: pd.Series,
        pattern_name: str,
        target_column: str,
        direction: str = "long",
    ) -> Optional[PatternStats]:
        """Compute statistics for a single pattern's forward returns."""
        matched = df.loc[mask, target_column].dropna()
        n = len(matched)

        if n < self.min_sample_size:
            print(
                f"  [SKIP] '{pattern_name}': N={n} < {self.min_sample_size} "
                f"(insufficient sample size)"
            )
            return None

        returns = matched.values

        # Flip sign for short direction
        if direction == "short":
            returns = -returns

        mean_ret = np.mean(returns)
        std_ret = np.std(returns, ddof=1)
        median_ret = np.median(returns)

        # Win rate
        win_rate = np.mean(returns > 0)

        # Sharpe ratio (annualized assuming 1-min bars, ~525600 bars/year)
        sharpe = (mean_ret / std_ret) if std_ret > 0 else 0.0

        # T-test: is the mean significantly different from zero?
        t_stat, p_val = stats.ttest_1samp(returns, 0)

        # Confidence interval
        alpha = 1 - self.confidence_level
        ci = stats.t.interval(
            self.confidence_level, df=n - 1, loc=mean_ret, scale=std_ret / np.sqrt(n)
        )

        return PatternStats(
            pattern_name=pattern_name,
            target_column=target_column,
            direction=direction,
            sample_size=n,
            win_rate=win_rate,
            mean_return=mean_ret,
            median_return=median_ret,
            std_return=std_ret,
            min_return=np.min(returns),
            max_return=np.max(returns),
            sharpe_ratio=sharpe,
            t_statistic=t_stat,
            p_value=p_val,
            confidence_interval_lower=ci[0],
            confidence_interval_upper=ci[1],
            significant=p_val < alpha,
        )

    def analyze_all(
        self,
        df: pd.DataFrame,
        pattern_masks: Dict[str, pd.Series],
        patterns: list,
    ) -> List[PatternStats]:
        """Analyze all patterns and return list of stats."""
        results = []
        pattern_lookup = {p.name: p for p in patterns}

        for name, mask in pattern_masks.items():
            pattern = pattern_lookup.get(name)
            if pattern is None:
                continue

            result = self.analyze_pattern(
                df=df,
                mask=mask,
                pattern_name=name,
                target_column=pattern.evaluate.target,
                direction=pattern.evaluate.direction,
            )
            if result is not None:
                results.append(result)

        return results

    @staticmethod
    def to_dataframe(stats_list: List[PatternStats]) -> pd.DataFrame:
        """Convert a list of PatternStats to a summary DataFrame."""
        if not stats_list:
            return pd.DataFrame()

        records = []
        for s in stats_list:
            records.append(
                {
                    "Pattern": s.pattern_name,
                    "Target": s.target_column,
                    "Direction": s.direction,
                    "N": s.sample_size,
                    "Win Rate (%)": round(s.win_rate * 100, 2),
                    "Mean Return (%)": round(s.mean_return * 100, 4),
                    "Median Return (%)": round(s.median_return * 100, 4),
                    "Std Dev (%)": round(s.std_return * 100, 4),
                    "Min (%)": round(s.min_return * 100, 4),
                    "Max (%)": round(s.max_return * 100, 4),
                    "Sharpe": round(s.sharpe_ratio, 4),
                    "T-Stat": round(s.t_statistic, 4),
                    "P-Value": round(s.p_value, 6),
                    "CI Lower (%)": round(s.confidence_interval_lower * 100, 4),
                    "CI Upper (%)": round(s.confidence_interval_upper * 100, 4),
                    "Significant": s.significant,
                }
            )

        return pd.DataFrame(records)

    def save_report(
        self, stats_list: List[PatternStats], output_dir: str, fmt: str = "csv"
    ) -> str:
        """Save the results DataFrame to file."""
        from pathlib import Path

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        summary = self.to_dataframe(stats_list)

        if fmt == "csv":
            path = str(Path(output_dir) / "pattern_results.csv")
            summary.to_csv(path, index=False)
        elif fmt == "html":
            path = str(Path(output_dir) / "pattern_results.html")
            summary.to_html(path, index=False)
        else:
            path = str(Path(output_dir) / "pattern_results.csv")
            summary.to_csv(path, index=False)

        return path

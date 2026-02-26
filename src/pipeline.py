"""Pipeline orchestrator – ties all stages together."""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .features.engine import FeatureEngine
from .ingestion.downloader import CryptoDownloader
from .rules.evaluator import RuleEvaluator
from .rules.parser import Pattern, PatternParser
from .stats.analyzer import PatternStats, StatisticalAnalyzer
from .targets.forward_returns import ForwardReturnsCalculator


class Pipeline:
    """Main orchestrator: Download -> Features -> Targets -> Rules -> Stats.

    Each stage is independently testable and configurable via the
    config dict loaded from config.yaml.
    """

    def __init__(self, config: dict):
        self.config = config
        self.downloader = CryptoDownloader(config)
        self.feature_engine = FeatureEngine(config)
        self.forward_returns = ForwardReturnsCalculator(config)
        self.pattern_parser = PatternParser()
        self.rule_evaluator = RuleEvaluator()
        self.analyzer = StatisticalAnalyzer(config)

        # State
        self.raw_data: Dict[str, pd.DataFrame] = {}
        self.enriched_data: Dict[str, pd.DataFrame] = {}
        self.patterns: List[Pattern] = []
        self.results: Dict[str, List[PatternStats]] = {}

    # ------------------------------------------------------------------
    # Stage 1: Data Ingestion
    # ------------------------------------------------------------------
    def ingest(self) -> Dict[str, pd.DataFrame]:
        """Download or load cached OHLCV data for all symbols."""
        print("\n=== STAGE 1: Data Ingestion ===")
        self.raw_data = self.downloader.download_all()

        for symbol, df in self.raw_data.items():
            print(f"  {symbol}: {len(df)} rows, "
                  f"{df.index.min()} to {df.index.max()}")

        return self.raw_data

    # ------------------------------------------------------------------
    # Stage 2: Feature Engineering
    # ------------------------------------------------------------------
    def compute_features(self) -> Dict[str, pd.DataFrame]:
        """Apply all feature modules to each symbol's data."""
        print("\n=== STAGE 2: Feature Engineering ===")

        for symbol, df in self.raw_data.items():
            enriched = self.feature_engine.compute(df)
            feature_count = len(enriched.columns) - len(df.columns)
            print(f"  {symbol}: +{feature_count} features "
                  f"({len(enriched.columns)} total columns)")
            self.enriched_data[symbol] = enriched

        return self.enriched_data

    # ------------------------------------------------------------------
    # Stage 3: Forward Returns
    # ------------------------------------------------------------------
    def compute_targets(self) -> Dict[str, pd.DataFrame]:
        """Calculate forward return targets for each symbol."""
        print("\n=== STAGE 3: Forward Returns ===")

        for symbol, df in self.enriched_data.items():
            self.enriched_data[symbol] = self.forward_returns.compute(df)
            horizons = self.config.get("forward_returns", {}).get(
                "horizons_minutes", []
            )
            print(f"  {symbol}: forward returns for {horizons} minutes")

        return self.enriched_data

    # ------------------------------------------------------------------
    # Stage 4: Load Pattern Definitions
    # ------------------------------------------------------------------
    def load_patterns(self, patterns_dir: str = "config/patterns") -> List[Pattern]:
        """Parse all pattern YAML files."""
        print("\n=== STAGE 4: Loading Patterns ===")
        self.patterns = self.pattern_parser.parse_directory(patterns_dir)
        for p in self.patterns:
            print(f"  Loaded: '{p.name}' ({len(p.conditions)} conditions)")
        return self.patterns

    # ------------------------------------------------------------------
    # Stage 5: Evaluate Patterns & Statistics
    # ------------------------------------------------------------------
    def evaluate(self) -> Dict[str, List[PatternStats]]:
        """Run all patterns against all symbols and compute statistics."""
        print("\n=== STAGE 5: Pattern Evaluation & Statistics ===")

        for symbol, df in self.enriched_data.items():
            print(f"\n  --- {symbol} ---")

            # Apply rules
            masks = self.rule_evaluator.evaluate_all_patterns(df, self.patterns)

            for name, mask in masks.items():
                n_matches = mask.sum()
                print(f"  Pattern '{name}': {n_matches} matches")

            # Statistics
            stats_list = self.analyzer.analyze_all(df, masks, self.patterns)
            self.results[symbol] = stats_list

        return self.results

    # ------------------------------------------------------------------
    # Stage 6: Report Generation
    # ------------------------------------------------------------------
    def generate_report(self) -> Optional[str]:
        """Generate and save the final report."""
        print("\n=== STAGE 6: Report Generation ===")

        report_cfg = self.config.get("statistics", {}).get("report", {})
        output_dir = report_cfg.get("output_dir", "output/results")
        fmt = report_cfg.get("format", "csv")

        all_stats = []
        for symbol, stats_list in self.results.items():
            for s in stats_list:
                # Tag with symbol
                s.pattern_name = f"[{symbol}] {s.pattern_name}"
            all_stats.extend(stats_list)

        if not all_stats:
            print("  No significant patterns found.")
            return None

        path = self.analyzer.save_report(all_stats, output_dir, fmt)
        print(f"  Report saved: {path}")

        # Print summary table
        summary = self.analyzer.to_dataframe(all_stats)
        print(f"\n{'=' * 80}")
        print("RESULTS SUMMARY")
        print(f"{'=' * 80}")
        print(summary.to_string(index=False))

        return path

    # ------------------------------------------------------------------
    # Full Run
    # ------------------------------------------------------------------
    def run(self, patterns_dir: str = "config/patterns") -> Optional[str]:
        """Execute the complete pipeline end-to-end."""
        self.ingest()
        self.compute_features()
        self.compute_targets()
        self.load_patterns(patterns_dir)
        self.evaluate()
        return self.generate_report()

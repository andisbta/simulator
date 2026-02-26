#!/usr/bin/env python3
"""Entry point for the Pattern Recognition Pipeline.

Usage:
    python main.py                          # Use default config
    python main.py --config path/to/config.yaml
    python main.py --patterns path/to/patterns/
"""

import argparse
import sys
from pathlib import Path

import yaml

from src.pipeline import Pipeline


def load_config(config_path: str) -> dict:
    """Load and return the YAML configuration."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Pattern Recognition & Statistical Backtesting Pipeline"
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the main configuration YAML file",
    )
    parser.add_argument(
        "--patterns",
        default="config/patterns",
        help="Directory containing pattern YAML files",
    )
    args = parser.parse_args()

    # Load config
    print(f"Loading config from: {args.config}")
    config = load_config(args.config)

    # Run pipeline
    pipeline = Pipeline(config)
    report_path = pipeline.run(patterns_dir=args.patterns)

    if report_path:
        print(f"\nDone. Report at: {report_path}")
    else:
        print("\nDone. No patterns met the minimum sample size threshold.")


if __name__ == "__main__":
    main()

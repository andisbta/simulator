"""Rolling window statistics: min, max, mean, std over configurable windows."""

import pandas as pd


def compute_rolling_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Add rolling window statistics to the DataFrame based on config."""
    roll_cfg = config.get("features", {}).get("rolling", {})
    windows = roll_cfg.get("windows", [5, 15, 60])
    metrics = roll_cfg.get("metrics", ["min", "max"])
    columns = roll_cfg.get("columns", ["close"])

    for col in columns:
        if col not in df.columns:
            continue
        for window in windows:
            roller = df[col].rolling(window=window)
            for metric in metrics:
                col_name = f"{col}_rolling_{metric}_{window}"
                if metric == "min":
                    df[col_name] = roller.min()
                elif metric == "max":
                    df[col_name] = roller.max()
                elif metric == "mean":
                    df[col_name] = roller.mean()
                elif metric == "std":
                    df[col_name] = roller.std()

    return df

"""Time-based features: day of week, hour, minute, minute of day."""

import pandas as pd


def compute_time_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Add time-based features to the DataFrame based on config."""
    time_cfg = config.get("features", {}).get("time", {})
    features = time_cfg.get("features", ["day_of_week", "hour", "minute"])

    idx = df.index

    for feat in features:
        if feat == "day_of_week":
            df["day_of_week"] = idx.dayofweek
        elif feat == "hour":
            df["hour"] = idx.hour
        elif feat == "minute":
            df["minute"] = idx.minute
        elif feat == "minute_of_day":
            df["minute_of_day"] = idx.hour * 60 + idx.minute

    return df

from datetime import date, timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd


def _fit_linear(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    if len(x) < 2:
        return 0.0, float(y[-1]) if len(y) else 0.0
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def forecast_metric(
    df: pd.DataFrame, metric: str, periods: int = 6
) -> Tuple[List[Tuple[date, float]], List[Tuple[date, float]]]:
    if df.empty or metric not in df.columns:
        return [], []

    df = df.sort_values("timestamp")
    history = list(zip(df["timestamp"], df[metric]))

    x = np.arange(len(df))
    y = df[metric].to_numpy(dtype=float)

    slope, intercept = _fit_linear(x, y)
    last_date = df["timestamp"].iloc[-1]

    forecast = []
    for i in range(1, periods + 1):
        next_index = len(df) - 1 + i
        value = slope * next_index + intercept
        forecast.append((last_date + timedelta(days=30 * i), float(value)))

    return history, forecast

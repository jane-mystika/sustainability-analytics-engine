from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sample_data.csv"
OUTPUT = ROOT / "sample_data_daily.csv"


def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main():
    df = pd.read_csv(SOURCE, parse_dates=["timestamp"])
    df["timestamp"] = df["timestamp"].dt.date

    facilities = df["facility_id"].unique().tolist()
    metric_cols = [c for c in df.columns if c not in ("timestamp", "facility_id", "facility_name")]

    daily_rows = []
    for facility_id in facilities:
        facility_df = df[df["facility_id"] == facility_id].sort_values("timestamp")
        facility_name = facility_df["facility_name"].iloc[0]

        # Build a daily date index across the available range
        start = facility_df["timestamp"].min()
        end = facility_df["timestamp"].max()
        full_index = list(daterange(start, end))

        # Reindex and interpolate linearly for numeric metrics
        tmp = facility_df.set_index("timestamp")[metric_cols].reindex(full_index)
        tmp = tmp.interpolate(method="linear").ffill().bfill()

        for ts, row in tmp.iterrows():
            daily_rows.append(
                {
                    "timestamp": ts,
                    "facility_id": facility_id,
                    "facility_name": facility_name,
                    **{col: round(float(row[col]), 2) for col in metric_cols},
                }
            )

    daily_df = pd.DataFrame(daily_rows)
    daily_df.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(daily_df)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()

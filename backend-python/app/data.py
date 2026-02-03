import os
from functools import lru_cache
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine


def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["timestamp"] = df["timestamp"].dt.date
    return df


def _load_mysql(mysql_url: str) -> pd.DataFrame:
    engine = create_engine(mysql_url)
    query = """
        SELECT
            m.timestamp,
            m.facility_id,
            COALESCE(f.facility_name, m.facility_name) AS facility_name,
            m.energy_kwh_per_wafer,
            m.cleanroom_energy_kwh,
            m.equipment_utilization,
            m.peak_energy_pct,
            m.hazardous_waste_kg,
            m.chemical_recycling_rate,
            m.solvent_recovery_rate,
            m.waste_compliance_pct,
            m.air_filtration_efficiency,
            m.particle_count,
            m.temp_humidity_energy_kwh,
            m.cleanroom_class,
            m.upw_consumption_m3,
            m.water_recycling_rate,
            m.wastewater_treatment_efficiency,
            m.water_per_wafer_l,
            m.scope1_tco2e,
            m.scope2_tco2e,
            m.scope3_tco2e,
            m.renewable_pct
        FROM metrics m
        LEFT JOIN facilities f ON f.facility_id = m.facility_id
    """
    df = pd.read_sql(query, engine)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.date
    return df


@lru_cache(maxsize=1)
def get_dataset() -> pd.DataFrame:
    data_source = os.getenv("DATA_SOURCE", "csv").lower().strip()
    if data_source == "mysql":
        mysql_url = os.getenv("MYSQL_URL")
        if not mysql_url:
            raise ValueError("MYSQL_URL not set for MySQL data source.")
        return _load_mysql(mysql_url)

    csv_path = os.getenv("DATA_CSV_PATH", "../database-mysql/seed/sample_data.csv")
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"CSV not found at {csv_path}. Set DATA_CSV_PATH or place the sample file."
        )
    return _load_csv(csv_path)


def filter_dataset(
    facility_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    df = get_dataset().copy()

    if facility_id:
        df = df[df["facility_id"] == facility_id]

    if start:
        df = df[df["timestamp"] >= pd.to_datetime(start).date()]

    if end:
        df = df[df["timestamp"] <= pd.to_datetime(end).date()]

    return df

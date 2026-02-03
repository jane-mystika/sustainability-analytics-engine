import numpy as np
import pandas as pd


def _normalize_inverse(value: float, low: float, high: float) -> float:
    if high == low:
        return 50.0
    value = np.clip(value, low, high)
    return 100.0 * (high - value) / (high - low)


def _normalize_direct(value: float, low: float, high: float) -> float:
    if high == low:
        return 50.0
    value = np.clip(value, low, high)
    return 100.0 * (value - low) / (high - low)


def compute_scores(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"overall": 0.0, "components": {}}

    row = df.mean(numeric_only=True)

    energy = np.mean(
        [
            _normalize_inverse(row["energy_kwh_per_wafer"], 220, 420),
            _normalize_inverse(row["cleanroom_energy_kwh"], 30000, 80000),
            _normalize_direct(row["equipment_utilization"], 60, 95),
            _normalize_inverse(row["peak_energy_pct"], 10, 45),
            _normalize_direct(row["renewable_pct"], 5, 45),
        ]
    )

    water = np.mean(
        [
            _normalize_inverse(row["upw_consumption_m3"], 1200, 2600),
            _normalize_direct(row["water_recycling_rate"], 35, 85),
            _normalize_direct(row["wastewater_treatment_efficiency"], 70, 98),
            _normalize_inverse(row["water_per_wafer_l"], 220, 480),
        ]
    )

    waste = np.mean(
        [
            _normalize_inverse(row["hazardous_waste_kg"], 2800, 6200),
            _normalize_direct(row["chemical_recycling_rate"], 30, 85),
            _normalize_direct(row["solvent_recovery_rate"], 40, 90),
            _normalize_direct(row["waste_compliance_pct"], 85, 100),
        ]
    )

    carbon = np.mean(
        [
            _normalize_inverse(row["scope1_tco2e"], 800, 2400),
            _normalize_inverse(row["scope2_tco2e"], 1200, 3800),
            _normalize_inverse(row["scope3_tco2e"], 8000, 18000),
        ]
    )

    cleanroom = np.mean(
        [
            _normalize_direct(row["air_filtration_efficiency"], 95, 99.9),
            _normalize_inverse(row["particle_count"], 20, 120),
            _normalize_inverse(row["temp_humidity_energy_kwh"], 15000, 42000),
            _normalize_inverse(row["cleanroom_class"], 1, 1000),
        ]
    )

    overall = float(np.mean([energy, water, waste, carbon, cleanroom]))

    return {
        "overall": overall,
        "components": {
            "energy": float(energy),
            "water": float(water),
            "waste": float(waste),
            "carbon": float(carbon),
            "cleanroom": float(cleanroom),
        },
    }


def score_tier(score: float) -> str:
    if score >= 85:
        return "Platinum"
    if score >= 75:
        return "Gold"
    if score >= 60:
        return "Silver"
    return "Bronze"

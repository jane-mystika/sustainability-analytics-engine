# Sample Data Load (MySQL)

This project ships with a CSV at `database-mysql/seed/sample_data.csv`.

## Option A: Manual import (MySQL Workbench)
1. Create the schema using `database-mysql/schema.sql`.
2. Use the Import Wizard to load the CSV into the `metrics` table.
3. (Optional) Populate the `facilities` table for cleaner joins.

## Option B: LOAD DATA INFILE
```sql
LOAD DATA INFILE 'C:/Users/JANE MYSTIKA/Desktop/placement/mini/database-mysql/seed/sample_data.csv'
INTO TABLE sustainability.metrics
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(timestamp, facility_id, facility_name, energy_kwh_per_wafer, cleanroom_energy_kwh, equipment_utilization,
 peak_energy_pct, hazardous_waste_kg, chemical_recycling_rate, solvent_recovery_rate, waste_compliance_pct,
 air_filtration_efficiency, particle_count, temp_humidity_energy_kwh, cleanroom_class, upw_consumption_m3,
 water_recycling_rate, wastewater_treatment_efficiency, water_per_wafer_l, scope1_tco2e, scope2_tco2e,
 scope3_tco2e, renewable_pct);

-- Optional: Populate facilities table from metrics
INSERT INTO facilities (facility_id, facility_name)
SELECT DISTINCT facility_id, facility_name FROM metrics
ON DUPLICATE KEY UPDATE facility_name = VALUES(facility_name);
```

Note: You may need to enable `local_infile` or adjust file permissions.

CREATE DATABASE IF NOT EXISTS sustainability;
USE sustainability;

CREATE TABLE IF NOT EXISTS facilities (
  facility_id VARCHAR(16) PRIMARY KEY,
  facility_name VARCHAR(100) NOT NULL,
  region VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATE NOT NULL,
  facility_id VARCHAR(16) NOT NULL,
  facility_name VARCHAR(100),
  energy_kwh_per_wafer DECIMAL(10,2),
  cleanroom_energy_kwh DECIMAL(12,2),
  equipment_utilization DECIMAL(5,2),
  peak_energy_pct DECIMAL(5,2),
  hazardous_waste_kg DECIMAL(10,2),
  chemical_recycling_rate DECIMAL(5,2),
  solvent_recovery_rate DECIMAL(5,2),
  waste_compliance_pct DECIMAL(5,2),
  air_filtration_efficiency DECIMAL(6,2),
  particle_count DECIMAL(10,2),
  temp_humidity_energy_kwh DECIMAL(12,2),
  cleanroom_class DECIMAL(10,2),
  upw_consumption_m3 DECIMAL(12,2),
  water_recycling_rate DECIMAL(5,2),
  wastewater_treatment_efficiency DECIMAL(5,2),
  water_per_wafer_l DECIMAL(10,2),
  scope1_tco2e DECIMAL(10,2),
  scope2_tco2e DECIMAL(10,2),
  scope3_tco2e DECIMAL(12,2),
  renewable_pct DECIMAL(5,2),
  CONSTRAINT fk_facility FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
);

# Software Requirements Specification (SRS)
## Semiconductor/Electronics Manufacturing Sustainability Analytics Engine

## 1. Introduction
### 1.1 Purpose
Define the functional and non-functional requirements for a sustainability analytics engine that tracks energy, water, waste, carbon, and cleanroom performance across semiconductor/electronics manufacturing facilities.

### 1.2 Scope
The system provides multi-facility monitoring, analytics, scoring, alerting, and reporting through a web-based dashboard with API support. It includes a sample dataset for demonstration and supports integration with a relational database.

### 1.3 Intended Audience
- Product stakeholders and sponsors
- Sustainability analysts and operations teams
- Software engineers and DevOps teams
- QA and testing teams

### 1.4 Document Objective
Specify what the system must do, the constraints it must respect, and the quality attributes it must achieve.

## 2. Overall Description
### 2.1 Product Functions
- Collect and store sustainability metrics.
- Compute sustainability scores and performance tiers.
- Provide trend analysis, forecasting, and anomaly detection.
- Generate alerts for threshold breaches.
- Provide comparative analytics across facilities and time ranges.
- Produce reports for export and audit readiness.

### 2.2 User Classes
- Employer (operations leadership / sustainability owner)
- Support staff (data entry, monitoring, and reporting)
- Manager/Admin (system configuration, access control, audit oversight)

### 2.3 Operating Environments
- Web-based dashboard (Streamlit frontend)
- API services (FastAPI backend)
- Database (MySQL)
- Deployment on local infrastructure or AWS cloud

### 2.4 Constraints
- Must support multi-facility data model.
- Must respect data privacy and access control for user roles.
- Must operate with limited network latency for near real-time dashboards.
- Must allow CSV import for legacy data.

### 2.5 Assumptions
- Metrics are collected on a consistent cadence (daily or monthly).
- Data quality is adequate for scoring and forecasting.
- Facilities share common metric definitions.

## 3. System Modules
### 3.1 Authentication and Role Management Module
- User login and session handling.
- Role-based access: Employer, Support Staff, Manager/Admin.
- Permission control for reporting, alerts, and configuration.

### 3.2 Creation Module
- Facility creation and configuration.
- Metric definitions and threshold settings.

### 3.3 Assignment Module
- Assign facilities to users or teams.
- Assign metric ownership and escalation contacts.

### 3.4 Resolution Module
- Track alert resolution status.
- Audit trail for corrective actions.

### 3.5 Reporting and Analytics Module
- KPI dashboards, score computation, and forecasting.
- Export reports in CSV/PDF.

### 3.6 Notification Module
- Email/SMS/app notifications for alerts.
- Escalation workflow for unresolved issues.

## 4. User Interface Design Requirements
### 4.1 General UI Guidelines
- Clean, data-first layout with minimal clutter.
- Responsive design for desktop and tablet use.
- Consistent color coding for performance tiers.

### 4.2 Employer UI
- Executive summary dashboard.
- Facility benchmarking and high-level KPIs.
- Downloadable sustainability reports.

### 4.3 Support Staff Interface
- Detailed metric tables.
- Data entry and import workflows.
- Alert monitoring and resolution tools.

### 4.4 Manager/Admin Interface
- User and role management.
- Threshold configuration.
- Audit logs and compliance summaries.

## 5. Functional Requirements
1. The system shall ingest data from CSV and MySQL sources.
2. The system shall compute sustainability scores (0-100).
3. The system shall assign performance tiers (Platinum, Gold, Silver, Bronze).
4. The system shall display near real-time KPI cards based on the latest available data.
5. The system shall provide trend graphs for all tracked metrics.
6. The system shall generate basic statistical forecasts (e.g., trend-based projections) for selected metrics.
7. The system shall detect threshold breaches and create alerts.
8. The system shall allow filtering by facility and date range.
9. The system shall support multi-facility comparisons.
10. The system shall allow report downloads.
11. The system shall provide visibility into the weighting and calculation logic used for sustainability scores.

## 6. Non-Functional Requirements
- Performance: Dashboard loads in under 3 seconds for typical queries.
- Reliability: API uptime target of 99.5% in production.
- Security: Role-based access control and secure credential storage.
- Usability: Intuitive navigation and clear data visualization.
- Maintainability: Modular code structure with documented APIs.

## 6.1 Analytics Layer (Scoring and Forecasting)
### Scoring Method
The analytics layer calculates a sustainability score (0–100) by normalizing each metric and averaging category scores.

Normalization logic:
- Direct normalization (higher is better): scores increase as values approach the upper benchmark.
- Inverse normalization (lower is better): scores increase as values approach the lower benchmark.

Category composition:
- Energy = average of energy per wafer, cleanroom energy, equipment utilization, peak energy %, renewable %
- Water = average of UPW usage, recycling rate, treatment efficiency, water per wafer
- Waste = average of hazardous waste, chemical recycling, solvent recovery, compliance %
- Carbon = average of Scope 1, Scope 2, Scope 3 emissions
- Cleanroom = average of filtration efficiency, particle count, temp/humidity energy, class

Overall score:
Overall = average(Energy, Water, Waste, Carbon, Cleanroom)

Tiering:
- Platinum ≥ 85
- Gold ≥ 75
- Silver ≥ 60
- Bronze < 60

### Forecasting Method
The system uses a basic statistical forecast:
- Sort time-series data by timestamp
- Fit a linear trend line
- Project forward for a fixed number of periods

This provides a simple, explainable trend-based forecast suitable for demo and baseline planning.

### Analytics Flow Diagram (High-Level)
```
Data Source (CSV / DB)
        |
        v
Analytics Layer (FastAPI)
  - KPI aggregation
  - Score calculation
  - Alerts + Forecasts
        |
        v
Dashboard (Streamlit)
  - KPI cards
  - Trend charts
  - Admin modules
```

## 7. Future Enhancements
- Full anomaly detection using ML models.
- Real-time ingestion with streaming data pipelines.
- Integration with ERP/SCADA systems.
- Advanced report templates and automated emailing.
- ESG compliance mapping and audit readiness scoring.

## 8. Conclusion
This SRS defines the scope, structure, and requirements for the sustainability analytics engine. It provides a foundation for implementation, testing, and future expansion while ensuring alignment with operational sustainability goals.

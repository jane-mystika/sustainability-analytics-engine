## INDIVIDUAL CONTRIBUTION
**Project Title:** Sustainability Analytics Cloud (Semiconductor/Electronics Manufacturing Sustainability Analytics Engine)  
**Student Name:** [Your Name]  
**Register Number:** [Your Register Number]  

- Designed and developed the Streamlit dashboard UI for multi-facility sustainability monitoring (KPI cards, trend charts, filters, and comparison views).
- Implemented navigation and role-aware access (Employer, Support Staff, Manager/Admin) to restrict sensitive actions such as configuration, alerts, and reporting.
- Built RESTful APIs using FastAPI for authentication, facility management, metric ingestion (CSV/DB), analytics queries, and report/export endpoints.
- Designed and integrated the MySQL data model for facilities and time-series sustainability metrics, ensuring consistent keys, timestamps, and query performance.
- Developed the sustainability scoring logic (0–100) with metric normalization, category-wise aggregation (Energy/Water/Waste/Carbon/Cleanroom), and tier assignment (Platinum/Gold/Silver/Bronze).
- Implemented forecasting workflow for selected metrics using a simple, explainable trend-based method and exposed results through API endpoints for dashboard visualization.
- Implemented alerting logic for threshold breaches, including alert creation, status transitions (New/Acknowledged/In Progress/Resolved/Closed), and audit-friendly timestamps.
- Integrated end-to-end data flow between dashboard, backend services, and database to support near real-time updates and consistent analytics outputs.
- Validated core workflows with sample/demo data and handled common error scenarios (invalid payloads, missing data ranges, unauthorized access).


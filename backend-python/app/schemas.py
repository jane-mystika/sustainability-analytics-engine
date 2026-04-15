from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


# Shared request/response models keep FastAPI validation and OpenAPI docs aligned.
class Facility(BaseModel):
    facility_id: str
    facility_name: str


class FacilityCreate(BaseModel):
    facility_id: str
    facility_name: str
    region: str | None = None


class FacilityUpdate(BaseModel):
    facility_name: str | None = None
    region: str | None = None


class User(BaseModel):
    user_id: str
    name: str
    role: str
    email: str | None = None


class UserCreate(BaseModel):
    user_id: str
    name: str
    role: str
    email: str | None = None
    password: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    email: str | None = None
    password: str | None = None


class Assignment(BaseModel):
    assignment_id: str
    user_id: str
    facility_id: str
    metric_owner: str | None = None
    escalation_contact: str | None = None


class AssignmentCreate(BaseModel):
    assignment_id: str
    user_id: str
    facility_id: str
    metric_owner: str | None = None
    escalation_contact: str | None = None


class AlertResolution(BaseModel):
    alert_id: str
    facility_id: str
    metric: str
    value: float
    status: str
    assigned_to: str | None = None
    assignment_id: str | None = None
    escalation_contact: str | None = None
    resolution_note: str | None = None
    resolved_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AlertCreate(BaseModel):
    alert_id: str
    facility_id: str
    metric: str
    value: float
    status: str = "open"
    resolution_note: str | None = None
    resolved_by: str | None = None


class AlertResolutionUpdate(BaseModel):
    status: str
    resolution_note: str | None = None
    resolved_by: str | None = None


class AlertHistoryEvent(BaseModel):
    # History entries capture who changed an alert and how the status moved over time.
    event_id: str
    alert_id: str
    event_type: str
    previous_status: str | None = None
    new_status: str | None = None
    actor_user_id: str | None = None
    actor_role: str | None = None
    note: str | None = None
    created_at: datetime


class Notification(BaseModel):
    notification_id: str
    channel: str
    recipient: str
    message: str
    status: str


class NotificationCreate(BaseModel):
    notification_id: str
    channel: str
    recipient: str
    message: str


class LoginRequest(BaseModel):
    user_id: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    role: str


class MetricRow(BaseModel):
    # This schema reflects the normalized sustainability dataset used throughout the app.
    timestamp: date
    facility_id: str
    facility_name: str
    energy_kwh_per_wafer: float
    cleanroom_energy_kwh: float
    equipment_utilization: float
    peak_energy_pct: float
    hazardous_waste_kg: float
    chemical_recycling_rate: float
    solvent_recovery_rate: float
    waste_compliance_pct: float
    air_filtration_efficiency: float
    particle_count: float
    temp_humidity_energy_kwh: float
    cleanroom_class: float
    upw_consumption_m3: float
    water_recycling_rate: float
    wastewater_treatment_efficiency: float
    water_per_wafer_l: float
    scope1_tco2e: float
    scope2_tco2e: float
    scope3_tco2e: float
    renewable_pct: float


class ScoreResponse(BaseModel):
    facility_id: Optional[str]
    facility_name: Optional[str]
    start: Optional[date]
    end: Optional[date]
    score: float
    tier: str
    components: dict


class ForecastPoint(BaseModel):
    timestamp: date
    value: float


class ForecastResponse(BaseModel):
    # History plus forecast points are returned together for simpler chart rendering.
    facility_id: Optional[str]
    metric: str
    history: List[ForecastPoint]
    forecast: List[ForecastPoint]

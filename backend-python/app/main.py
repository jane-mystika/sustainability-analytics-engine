import os
import secrets
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from app.data import filter_dataset, get_dataset
from app.forecast import forecast_metric
from app.scoring import compute_scores, score_tier
from app.schemas import (
    AlertResolution,
    AlertResolutionUpdate,
    Assignment,
    AssignmentCreate,
    Facility,
    FacilityCreate,
    ForecastPoint,
    ForecastResponse,
    LoginRequest,
    LoginResponse,
    MetricRow,
    Notification,
    NotificationCreate,
    ScoreResponse,
    User,
    UserCreate,
)

app = FastAPI(title="Sustainability Analytics API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory MVP stores
USERS: Dict[str, User] = {}
PASSWORDS: Dict[str, str] = {}
TOKENS: Dict[str, str] = {}
FACILITIES: Dict[str, FacilityCreate] = {}
ASSIGNMENTS: Dict[str, Assignment] = {}
ALERTS: Dict[str, AlertResolution] = {}
NOTIFICATIONS: Dict[str, Notification] = {}


def _seed_facilities_from_data():
    try:
        df = get_dataset()
        for _, row in df[["facility_id", "facility_name"]].drop_duplicates().iterrows():
            FACILITIES[row["facility_id"]] = FacilityCreate(
                facility_id=row["facility_id"], facility_name=row["facility_name"], region=None
            )
    except Exception:
        return


def _seed_demo_data():
    USERS["admin"] = User(user_id="admin", name="Admin User", role="Manager/Admin", email="admin@demo.com")
    USERS["employer1"] = User(
        user_id="employer1", name="Employer One", role="Employer", email="employer@demo.com"
    )
    USERS["support1"] = User(
        user_id="support1", name="Support One", role="Support Staff", email="support@demo.com"
    )
    PASSWORDS["admin"] = "admin123"
    PASSWORDS["employer1"] = "employer123"
    PASSWORDS["support1"] = "support123"

    if FACILITIES:
        for facility_id in list(FACILITIES.keys())[:2]:
            assignment_id = f"assign-{facility_id}"
            ASSIGNMENTS[assignment_id] = Assignment(
                assignment_id=assignment_id,
                user_id="support1",
                facility_id=facility_id,
                metric_owner="support1",
                escalation_contact="admin",
            )

    ALERTS["alert-001"] = AlertResolution(
        alert_id="alert-001",
        facility_id=list(FACILITIES.keys())[0] if FACILITIES else "F1",
        metric="energy_kwh_per_wafer",
        value=410.0,
        status="open",
        resolution_note=None,
        resolved_by=None,
    )
    NOTIFICATIONS["notif-001"] = Notification(
        notification_id="notif-001",
        channel="email",
        recipient="admin@demo.com",
        message="Energy threshold exceeded at Phoenix Fab.",
        status="queued",
    )


def _seed_on_startup():
    _seed_facilities_from_data()
    _seed_demo_data()


_seed_on_startup()


def _get_user_from_token(auth_header: Optional[str]) -> Optional[User]:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    user_id = TOKENS.get(token)
    if not user_id:
        return None
    return USERS.get(user_id)


def _require_admin(auth_header: Optional[str]) -> User:
    user = _get_user_from_token(auth_header)
    if not user or user.role != "Manager/Admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = USERS.get(payload.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if PASSWORDS.get(payload.user_id) != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(16)
    TOKENS[token] = user.user_id
    return LoginResponse(token=token, user_id=user.user_id, role=user.role)


@app.get("/facilities", response_model=List[Facility])
def facilities():
    base = [
        {"facility_id": f.facility_id, "facility_name": f.facility_name}
        for f in FACILITIES.values()
    ]
    return sorted(base, key=lambda x: x["facility_name"])


@app.get("/metrics", response_model=List[MetricRow])
def metrics(
    facility_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    df = filter_dataset(facility_id, start, end)
    return df.sort_values("timestamp").to_dict(orient="records")


@app.get("/score", response_model=ScoreResponse)
def score(
    facility_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    df = filter_dataset(facility_id, start, end)
    scores = compute_scores(df)
    tier = score_tier(scores["overall"])

    facility_name = None
    if facility_id and not df.empty:
        facility_name = df["facility_name"].iloc[0]

    return ScoreResponse(
        facility_id=facility_id,
        facility_name=facility_name,
        start=start,
        end=end,
        score=round(scores["overall"], 2),
        tier=tier,
        components={k: round(v, 2) for k, v in scores["components"].items()},
    )


@app.get("/forecast", response_model=ForecastResponse)
def forecast(
    metric: str,
    facility_id: Optional[str] = None,
    periods: int = 6,
):
    df = filter_dataset(facility_id)
    history, future = forecast_metric(df, metric, periods=periods)
    if not history:
        raise HTTPException(status_code=404, detail="No data for metric")

    return ForecastResponse(
        facility_id=facility_id,
        metric=metric,
        history=[ForecastPoint(timestamp=t, value=float(v)) for t, v in history],
        forecast=[ForecastPoint(timestamp=t, value=float(v)) for t, v in future],
    )


@app.get("/alerts")
def alerts(
    facility_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    energy_threshold: float = 380,
    water_threshold: float = 430,
    waste_threshold: float = 5200,
):
    df = filter_dataset(facility_id, start, end)
    if df.empty:
        return []

    alerts = []
    for _, row in df.iterrows():
        if row["energy_kwh_per_wafer"] > energy_threshold:
            alerts.append(
                {
                    "timestamp": row["timestamp"],
                    "facility_id": row["facility_id"],
                    "metric": "energy_kwh_per_wafer",
                    "value": row["energy_kwh_per_wafer"],
                }
            )
        if row["water_per_wafer_l"] > water_threshold:
            alerts.append(
                {
                    "timestamp": row["timestamp"],
                    "facility_id": row["facility_id"],
                    "metric": "water_per_wafer_l",
                    "value": row["water_per_wafer_l"],
                }
            )
        if row["hazardous_waste_kg"] > waste_threshold:
            alerts.append(
                {
                    "timestamp": row["timestamp"],
                    "facility_id": row["facility_id"],
                    "metric": "hazardous_waste_kg",
                    "value": row["hazardous_waste_kg"],
                }
            )

    return alerts


# --- Admin MVP modules ---
@app.get("/admin/users", response_model=List[User])
def list_users(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return list(USERS.values())


@app.post("/admin/users", response_model=User)
def create_user(payload: UserCreate, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    user = User(**payload.model_dump())
    USERS[user.user_id] = user
    if payload.password:
        PASSWORDS[user.user_id] = payload.password
    return user


@app.get("/admin/facilities", response_model=List[FacilityCreate])
def list_facilities(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return list(FACILITIES.values())


@app.post("/admin/facilities", response_model=FacilityCreate)
def create_facility(payload: FacilityCreate, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    FACILITIES[payload.facility_id] = payload
    return payload


@app.get("/admin/assignments", response_model=List[Assignment])
def list_assignments(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return list(ASSIGNMENTS.values())


@app.post("/admin/assignments", response_model=Assignment)
def create_assignment(payload: AssignmentCreate, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    assignment = Assignment(**payload.model_dump())
    ASSIGNMENTS[assignment.assignment_id] = assignment
    return assignment


@app.get("/admin/alerts", response_model=List[AlertResolution])
def list_alerts(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return list(ALERTS.values())


@app.post("/admin/alerts", response_model=AlertResolution)
def create_alert(payload: AlertResolution, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    ALERTS[payload.alert_id] = payload
    return payload


@app.patch("/admin/alerts/{alert_id}", response_model=AlertResolution)
def resolve_alert(
    alert_id: str,
    payload: AlertResolutionUpdate,
    authorization: Optional[str] = Header(default=None),
):
    _require_admin(authorization)
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    current = ALERTS[alert_id]
    updated = current.model_copy(
        update={
            "status": payload.status,
            "resolution_note": payload.resolution_note,
            "resolved_by": payload.resolved_by,
        }
    )
    ALERTS[alert_id] = updated
    return updated


@app.get("/admin/notifications", response_model=List[Notification])
def list_notifications(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return list(NOTIFICATIONS.values())


@app.post("/admin/notifications", response_model=Notification)
def create_notification(payload: NotificationCreate, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    notification = Notification(
        notification_id=payload.notification_id,
        channel=payload.channel,
        recipient=payload.recipient,
        message=payload.message,
        status="queued",
    )
    NOTIFICATIONS[notification.notification_id] = notification
    return notification

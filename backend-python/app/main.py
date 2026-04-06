import re
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.data import filter_dataset, get_dataset, reset_dataset_cache
from app.forecast import forecast_metric
from app.scoring import compute_scores, score_tier
from app.schemas import (
    AlertCreate,
    AlertHistoryEvent,
    AlertResolution,
    AlertResolutionUpdate,
    Assignment,
    AssignmentCreate,
    Facility,
    FacilityCreate,
    FacilityUpdate,
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
    UserUpdate,
)

settings = get_settings()


USERS: Dict[str, User] = {}
PASSWORDS: Dict[str, str] = {}
TOKENS: Dict[str, str] = {}
FACILITIES: Dict[str, FacilityCreate] = {}
ASSIGNMENTS: Dict[str, Assignment] = {}
ALERTS: Dict[str, AlertResolution] = {}
ALERT_HISTORY: List[AlertHistoryEvent] = []
NOTIFICATIONS: Dict[str, Notification] = {}


def _reset_state() -> None:
    USERS.clear()
    PASSWORDS.clear()
    TOKENS.clear()
    FACILITIES.clear()
    ASSIGNMENTS.clear()
    ALERTS.clear()
    ALERT_HISTORY.clear()
    NOTIFICATIONS.clear()


def _seed_facilities_from_data() -> None:
    df = get_dataset()
    for _, row in df[["facility_id", "facility_name"]].drop_duplicates().iterrows():
        FACILITIES[row["facility_id"]] = FacilityCreate(
            facility_id=row["facility_id"],
            facility_name=row["facility_name"],
            region=None,
        )


def _bootstrap_admin_user() -> None:
    USERS[settings.admin_user_id] = User(
        user_id=settings.admin_user_id,
        name=settings.admin_name,
        role="Manager/Admin",
        email=settings.admin_email,
    )
    PASSWORDS[settings.admin_user_id] = settings.admin_password


def _seed_demo_data() -> None:
    _bootstrap_admin_user()
    USERS["employer1"] = User(
        user_id="employer1",
        name="Employer One",
        role="Employer",
        email="employer@demo.com",
    )
    USERS["support1"] = User(
        user_id="support1",
        name="Support One",
        role="Support Staff",
        email="support@demo.com",
    )
    USERS["support2"] = User(
        user_id="support2",
        name="Support Two",
        role="Support Staff",
        email="support2@demo.com",
    )
    PASSWORDS["employer1"] = "employer123"
    PASSWORDS["support1"] = "support123"
    PASSWORDS["support2"] = "support123"

    if FACILITIES:
        seeded_facilities = list(FACILITIES.keys())[:2]
        seeded_supports = ["support1", "support2"]
        for index, facility_id in enumerate(seeded_facilities):
            support_user = seeded_supports[index % len(seeded_supports)]
            assignment_id = f"assign-{facility_id}"
            ASSIGNMENTS[assignment_id] = Assignment(
                assignment_id=assignment_id,
                user_id=support_user,
                facility_id=facility_id,
                metric_owner=support_user,
                escalation_contact=settings.admin_user_id,
            )

    ALERTS["alert-001"] = AlertResolution(
        alert_id="alert-001",
        facility_id=list(FACILITIES.keys())[0] if FACILITIES else "F1",
        metric="energy_kwh_per_wafer",
        value=410.0,
        status="open",
        assigned_to="support1",
        assignment_id=(list(ASSIGNMENTS.keys())[0] if ASSIGNMENTS else None),
        escalation_contact=settings.admin_user_id,
        resolution_note=None,
        resolved_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    NOTIFICATIONS["notif-001"] = Notification(
        notification_id="notif-001",
        channel="email",
        recipient=settings.admin_email,
        message="Energy threshold exceeded at Phoenix Fab.",
        status="queued",
    )


def _seed_on_startup() -> None:
    _reset_state()
    reset_dataset_cache()
    _seed_facilities_from_data()
    if settings.seed_demo_data:
        _seed_demo_data()
    else:
        _bootstrap_admin_user()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _seed_on_startup()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

if settings.trusted_hosts and settings.trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


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


def _require_user(auth_header: Optional[str]) -> User:
    user = _get_user_from_token(auth_header)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _record_alert_event(
    alert_id: str,
    event_type: str,
    previous_status: Optional[str],
    new_status: Optional[str],
    actor: Optional[User],
    note: Optional[str] = None,
) -> None:
    ALERT_HISTORY.append(
        AlertHistoryEvent(
            event_id=secrets.token_hex(8),
            alert_id=alert_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            actor_user_id=actor.user_id if actor else None,
            actor_role=actor.role if actor else None,
            note=note,
            created_at=_now_utc(),
        )
    )


def _admin_users() -> List[User]:
    return [user for user in USERS.values() if user.role == "Manager/Admin"]


def _notify_admins(message: str, channel: str = "app") -> None:
    for admin in _admin_users():
        recipient = admin.email or admin.user_id
        notification_id = f"notif-{secrets.token_hex(6)}"
        NOTIFICATIONS[notification_id] = Notification(
            notification_id=notification_id,
            channel=channel,
            recipient=recipient,
            message=message,
            status="queued",
        )


def _support_workload(user_id: str) -> int:
    active_statuses = {"open", "in_progress", "needs_info", "unresolved", "escalated"}
    return sum(
        1
        for alert in ALERTS.values()
        if alert.assigned_to == user_id and alert.status in active_statuses
    )


def _support_assignment_count(user_id: str) -> int:
    return sum(1 for assignment in ASSIGNMENTS.values() if assignment.user_id == user_id)


def _staff_for_facility(facility_id: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    support_users = {user.user_id: user for user in USERS.values() if user.role == "Support Staff"}
    if not support_users:
        return None, None, None

    candidate_assignments = [
        assignment
        for assignment in ASSIGNMENTS.values()
        if assignment.facility_id == facility_id and assignment.user_id in support_users
    ]
    if candidate_assignments:
        best = min(candidate_assignments, key=lambda assignment: _support_workload(assignment.user_id))
        return best.user_id, best.assignment_id, best.escalation_contact

    fallback_user_id = min(
        support_users.keys(),
        key=lambda user_id: (_support_workload(user_id), _support_assignment_count(user_id), user_id),
    )
    assignment_id = f"assign-auto-{facility_id}-{fallback_user_id}"
    if assignment_id not in ASSIGNMENTS:
        ASSIGNMENTS[assignment_id] = Assignment(
            assignment_id=assignment_id,
            user_id=fallback_user_id,
            facility_id=facility_id,
            metric_owner=fallback_user_id,
            escalation_contact=settings.admin_user_id,
        )
    return fallback_user_id, assignment_id, settings.admin_user_id


def _threshold_alert_id(facility_id: str, metric: str, timestamp_value: object) -> str:
    metric_slug = re.sub(r"[^a-zA-Z0-9]+", "_", metric).strip("_").lower()
    return f"auto-{facility_id}-{metric_slug}-{timestamp_value}"


def _create_operational_alert(
    *,
    alert_id: str,
    facility_id: str,
    metric: str,
    value: float,
    status: str,
    actor: Optional[User],
    note: Optional[str] = None,
    resolution_note: Optional[str] = None,
    resolved_by: Optional[str] = None,
) -> bool:
    if alert_id in ALERTS:
        return False

    assigned_to, assignment_id, escalation_contact = _staff_for_facility(facility_id)
    now = _now_utc()
    created = AlertResolution(
        alert_id=alert_id,
        facility_id=facility_id,
        metric=metric,
        value=value,
        status=status,
        assigned_to=assigned_to,
        assignment_id=assignment_id,
        escalation_contact=escalation_contact,
        resolution_note=resolution_note,
        resolved_by=resolved_by,
        created_at=now,
        updated_at=now,
    )
    ALERTS[alert_id] = created
    _record_alert_event(
        alert_id=alert_id,
        event_type="created",
        previous_status=None,
        new_status=status,
        actor=actor,
        note=note or f"Auto-assigned to {assigned_to or 'unassigned'}",
    )
    if assigned_to:
        _notify_admins(
            f"Alert {alert_id} for facility {facility_id} auto-assigned to {assigned_to}."
        )
    else:
        _notify_admins(
            f"No support staff available for facility {facility_id}; alert {alert_id} requires manual action."
        )
    return True


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": _now_utc().isoformat(),
    }


@app.get("/ready")
def ready():
    dataset = get_dataset()
    return {
        "status": "ready",
        "records": int(len(dataset)),
        "facilities": len(FACILITIES),
        "data_source": settings.data_source,
    }


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = USERS.get(payload.user_id)
    if not user or PASSWORDS.get(payload.user_id) != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(16)
    TOKENS[token] = user.user_id
    return LoginResponse(token=token, user_id=user.user_id, role=user.role)


@app.get("/facilities", response_model=List[Facility])
def facilities():
    base = [
        {"facility_id": facility.facility_id, "facility_name": facility.facility_name}
        for facility in FACILITIES.values()
    ]
    return sorted(base, key=lambda item: item["facility_name"])


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
        components={key: round(value, 2) for key, value in scores["components"].items()},
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
        history=[ForecastPoint(timestamp=timestamp, value=float(value)) for timestamp, value in history],
        forecast=[ForecastPoint(timestamp=timestamp, value=float(value)) for timestamp, value in future],
    )


@app.get("/alerts")
def alerts(
    facility_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    energy_threshold: float = 380,
    water_threshold: float = 430,
    waste_threshold: float = 5200,
    limit: int = 500,
    auto_create_workflow: bool = True,
):
    df = filter_dataset(facility_id, start, end)
    if df.empty:
        return []

    energy_alerts = df[df["energy_kwh_per_wafer"] > energy_threshold][
        ["timestamp", "facility_id", "energy_kwh_per_wafer"]
    ].rename(columns={"energy_kwh_per_wafer": "value"})
    if not energy_alerts.empty:
        energy_alerts["metric"] = "energy_kwh_per_wafer"

    water_alerts = df[df["water_per_wafer_l"] > water_threshold][
        ["timestamp", "facility_id", "water_per_wafer_l"]
    ].rename(columns={"water_per_wafer_l": "value"})
    if not water_alerts.empty:
        water_alerts["metric"] = "water_per_wafer_l"

    waste_alerts = df[df["hazardous_waste_kg"] > waste_threshold][
        ["timestamp", "facility_id", "hazardous_waste_kg"]
    ].rename(columns={"hazardous_waste_kg": "value"})
    if not waste_alerts.empty:
        waste_alerts["metric"] = "hazardous_waste_kg"

    combined = [frame for frame in [energy_alerts, water_alerts, waste_alerts] if not frame.empty]
    if not combined:
        return []

    output = combined[0] if len(combined) == 1 else pd.concat(combined, ignore_index=True)
    output = output.sort_values("timestamp", ascending=False)
    if limit > 0:
        output = output.head(limit)
    rows = output.to_dict(orient="records")

    if auto_create_workflow:
        for row in rows:
            auto_id = _threshold_alert_id(
                facility_id=row["facility_id"],
                metric=row["metric"],
                timestamp_value=row["timestamp"],
            )
            _create_operational_alert(
                alert_id=auto_id,
                facility_id=row["facility_id"],
                metric=row["metric"],
                value=float(row["value"]),
                status="open",
                actor=None,
                note=f"Auto-generated from threshold breach at {row['timestamp']}",
            )

    return rows


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


@app.patch("/admin/users/{user_id}", response_model=User)
def update_user(
    user_id: str,
    payload: UserUpdate,
    authorization: Optional[str] = Header(default=None),
):
    _require_admin(authorization)
    current = USERS.get(user_id)
    if not current:
        raise HTTPException(status_code=404, detail="User not found")
    updates = payload.model_dump(exclude_none=True)
    password = updates.pop("password", None)
    updated = current.model_copy(update=updates)
    USERS[user_id] = updated
    if password is not None:
        PASSWORDS[user_id] = password
    return updated


@app.delete("/admin/users/{user_id}")
def delete_user(user_id: str, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    user = USERS.pop(user_id, None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    PASSWORDS.pop(user_id, None)
    token_keys = [token for token, uid in TOKENS.items() if uid == user_id]
    for token in token_keys:
        TOKENS.pop(token, None)
    return {"deleted": True, "user_id": user_id}


@app.get("/admin/facilities", response_model=List[FacilityCreate])
def list_facilities(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return list(FACILITIES.values())


@app.post("/admin/facilities", response_model=FacilityCreate)
def create_facility(payload: FacilityCreate, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    FACILITIES[payload.facility_id] = payload
    return payload


@app.patch("/admin/facilities/{facility_id}", response_model=FacilityCreate)
def update_facility(
    facility_id: str,
    payload: FacilityUpdate,
    authorization: Optional[str] = Header(default=None),
):
    _require_admin(authorization)
    current = FACILITIES.get(facility_id)
    if not current:
        raise HTTPException(status_code=404, detail="Facility not found")
    updates = payload.model_dump(exclude_none=True)
    updated = current.model_copy(update=updates)
    FACILITIES[facility_id] = updated
    return updated


@app.delete("/admin/facilities/{facility_id}")
def delete_facility(facility_id: str, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    facility = FACILITIES.pop(facility_id, None)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return {"deleted": True, "facility_id": facility_id}


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
def create_alert(payload: AlertCreate, authorization: Optional[str] = Header(default=None)):
    actor = _require_admin(authorization)
    created = _create_operational_alert(
        alert_id=payload.alert_id,
        facility_id=payload.facility_id,
        metric=payload.metric,
        value=payload.value,
        status=payload.status,
        actor=actor,
        resolution_note=payload.resolution_note,
        resolved_by=payload.resolved_by,
    )
    if not created:
        raise HTTPException(status_code=409, detail="Alert already exists")
    return ALERTS[payload.alert_id]


@app.patch("/admin/alerts/{alert_id}", response_model=AlertResolution)
def resolve_alert(
    alert_id: str,
    payload: AlertResolutionUpdate,
    authorization: Optional[str] = Header(default=None),
):
    actor = _require_admin(authorization)
    current = ALERTS.get(alert_id)
    if not current:
        raise HTTPException(status_code=404, detail="Alert not found")
    previous_status = current.status
    updated = current.model_copy(
        update={
            "status": payload.status,
            "resolution_note": payload.resolution_note,
            "resolved_by": payload.resolved_by,
            "updated_at": _now_utc(),
        }
    )
    ALERTS[alert_id] = updated
    _record_alert_event(
        alert_id=alert_id,
        event_type="admin_update",
        previous_status=previous_status,
        new_status=payload.status,
        actor=actor,
        note=payload.resolution_note,
    )
    if payload.status == "resolved":
        _notify_admins(
            f"Alert {alert_id} resolved by {payload.resolved_by or actor.user_id}. History has been updated."
        )
    if payload.status in {"needs_info", "unresolved", "escalated"}:
        _notify_admins(f"Alert {alert_id} moved to '{payload.status}'. Admin review required.")
    return updated


@app.get("/admin/alerts/history", response_model=List[AlertHistoryEvent])
def list_alert_history(
    alert_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
):
    _require_admin(authorization)
    if alert_id:
        return [event for event in ALERT_HISTORY if event.alert_id == alert_id]
    return ALERT_HISTORY


@app.get("/staff/assignments", response_model=List[Assignment])
def staff_assignments(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    if user.role not in {"Support Staff", "Manager/Admin"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    if user.role == "Manager/Admin":
        return list(ASSIGNMENTS.values())
    return [assignment for assignment in ASSIGNMENTS.values() if assignment.user_id == user.user_id]


@app.get("/staff/alerts", response_model=List[AlertResolution])
def staff_alerts(
    status: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
):
    user = _require_user(authorization)
    if user.role not in {"Support Staff", "Manager/Admin"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    alerts_list = list(ALERTS.values())
    if user.role == "Support Staff":
        alerts_list = [alert for alert in alerts_list if alert.assigned_to == user.user_id]
    if status:
        alerts_list = [alert for alert in alerts_list if alert.status == status]
    return alerts_list


@app.patch("/staff/alerts/{alert_id}", response_model=AlertResolution)
def staff_update_alert(
    alert_id: str,
    payload: AlertResolutionUpdate,
    authorization: Optional[str] = Header(default=None),
):
    user = _require_user(authorization)
    if user.role not in {"Support Staff", "Manager/Admin"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    current = ALERTS.get(alert_id)
    if not current:
        raise HTTPException(status_code=404, detail="Alert not found")
    if user.role == "Support Staff" and current.assigned_to != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    previous_status = current.status
    resolved_by = payload.resolved_by or (
        user.user_id if payload.status == "resolved" else current.resolved_by
    )
    updated = current.model_copy(
        update={
            "status": payload.status,
            "resolution_note": payload.resolution_note,
            "resolved_by": resolved_by,
            "updated_at": _now_utc(),
        }
    )
    ALERTS[alert_id] = updated
    _record_alert_event(
        alert_id=alert_id,
        event_type="staff_update",
        previous_status=previous_status,
        new_status=payload.status,
        actor=user,
        note=payload.resolution_note,
    )

    if payload.status == "resolved":
        _notify_admins(
            f"Alert {alert_id} resolved by {user.user_id}. Resolution note: {payload.resolution_note or 'N/A'}"
        )
    if payload.status in {"needs_info", "unresolved", "escalated"}:
        _notify_admins(f"Alert {alert_id} requires admin attention (status: {payload.status}).")
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

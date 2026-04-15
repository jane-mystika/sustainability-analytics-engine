import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# The dashboard can talk to the API or fall back to a local CSV for read-only exploration.
def _resolve_api_url() -> str:
    env_url = os.getenv("API_URL")
    if env_url:
        return env_url.rstrip("/")
    secrets_url = st.secrets.get("API_URL")
    if secrets_url:
        return str(secrets_url).rstrip("/")
    return "http://localhost:8000"


API_URL = _resolve_api_url()
DATA_CSV_PATH = os.getenv("DATA_CSV_PATH", "../backend-python/data/sample_data.csv")
DEMO_ADMIN_USER = os.getenv("ADMIN_USER_ID", "admin")
DEMO_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")

st.set_page_config(page_title="Semiconductor Sustainability Analytics", layout="wide")

PLOTLY_TEMPLATE = "plotly_white"

CHART_LINE_COLORS = ["#5B8FF9", "#61CDBB", "#F6BD16", "#E8684A", "#9270CA"]
CHART_GRID_COLOR = "rgba(44, 62, 80, 0.10)"
CHART_PAPER_BG = "#F9FBFC"
CHART_PLOT_BG = "#FFFFFF"


def fetch_json(path: str, params=None):
    # All API helpers fail soft so the UI can keep rendering even if the backend is offline.
    try:
        headers = _auth_headers()
        normalized_path = path if path.startswith("/") else f"/{path}"
        resp = requests.get(
            f"{API_URL}{normalized_path}",
            params=params,
            headers=headers,
            timeout=3,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def post_json(path: str, payload: dict):
    try:
        headers = _auth_headers()
        normalized_path = path if path.startswith("/") else f"/{path}"
        resp = requests.post(
            f"{API_URL}{normalized_path}",
            json=payload,
            headers=headers,
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def patch_json(path: str, payload: dict):
    try:
        headers = _auth_headers()
        normalized_path = path if path.startswith("/") else f"/{path}"
        resp = requests.patch(
            f"{API_URL}{normalized_path}",
            json=payload,
            headers=headers,
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def delete_json(path: str):
    try:
        headers = _auth_headers()
        normalized_path = path if path.startswith("/") else f"/{path}"
        resp = requests.delete(f"{API_URL}{normalized_path}", headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _auth_headers():
    # Logged-in API calls reuse the bearer token stored in Streamlit session state.
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def style_time_series_chart(fig, title: str):
    # Keep every trend chart visually consistent with a light dashboard theme.
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=dict(text=title, font=dict(size=18, color="#243447")),
        hovermode="x unified",
        paper_bgcolor=CHART_PAPER_BG,
        plot_bgcolor=CHART_PLOT_BG,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.65)",
        ),
        colorway=CHART_LINE_COLORS,
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=CHART_GRID_COLOR,
        linecolor="rgba(44, 62, 80, 0.18)",
        tickfont=dict(color="#51606F"),
        rangeselector=dict(
            bgcolor="rgba(255,255,255,0.95)",
            activecolor="#DCE8FF",
            buttons=list(
                [
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
        ),
        rangeslider=dict(visible=True, bgcolor="rgba(91,143,249,0.08)", borderwidth=0),
        type="date",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=CHART_GRID_COLOR,
        zeroline=False,
        tickfont=dict(color="#51606F"),
    )
    fig.update_traces(
        line=dict(width=2),
        marker=dict(size=5, line=dict(width=0)),
        selector=dict(type="scatter"),
    )


def compact_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    # Show only the fields that help the user scan the workflow quickly.
    available_columns = [column for column in columns if column in df.columns]
    return df.loc[:, available_columns] if available_columns else df


@st.cache_data(ttl=60)
def load_data():
    # Prefer live API data, but keep a local fallback so the dashboard can still open in demo mode.
    data = fetch_json("/metrics")
    if data is not None:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    df = pd.read_csv(DATA_CSV_PATH, parse_dates=["timestamp"])
    return df


df = load_data()

st.title("Semiconductor/Electronics Manufacturing Sustainability Analytics")
st.caption("Multi-facility dashboard with scoring, trends, forecasting, and alerts.")

with st.sidebar:
    st.markdown("### Login")
    st.caption(f"API: `{API_URL}`")
    if st.session_state.get("auth_token"):
        st.success(
            f"Signed in as {st.session_state.get('auth_user_id')} ({st.session_state.get('auth_role')})"
        )
        if st.button("Sign Out"):
            st.session_state.pop("auth_token", None)
            st.session_state.pop("auth_user_id", None)
            st.session_state.pop("auth_role", None)
            st.rerun()
    else:
        with st.form("login_form"):
            user_id = st.text_input("User ID")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                result = post_json("/auth/login", {"user_id": user_id, "password": password})
                if result:
                    st.session_state["auth_token"] = result["token"]
                    st.session_state["auth_user_id"] = result["user_id"]
                    st.session_state["auth_role"] = result["role"]
                    st.success("Signed in.")
                    st.rerun()
                else:
                    # Distinguish a real auth failure from the API being offline.
                    if fetch_json("/health") is None:
                        st.error(
                            f"Backend not reachable at `{API_URL}`. "
                            "If running locally, start the API on `http://localhost:8000`. "
                            "If deployed, set `API_URL` to your backend service URL."
                        )
                    else:
                        st.error("Invalid credentials.")
        # Keep the login hint aligned with the backend bootstrap credentials.
        st.caption(f"Demo admin: `{DEMO_ADMIN_USER}` / `{DEMO_ADMIN_PASSWORD}`")

tabs = st.tabs(
    [
        "Dashboard",
        "Users & Roles",
        "Facilities",
        "Assignments (Auto)",
        "Alerts Resolution",
        "Notifications (Auto)",
    ]
)

with tabs[0]:
    # Facility choices combine API-managed facilities with whatever exists in the loaded dataset.
    admin_facilities = fetch_json("/admin/facilities") or []
    admin_names = [f.get("facility_name") for f in admin_facilities if f.get("facility_name")]
    data_names = df["facility_name"].dropna().unique().tolist()
    facility_options = ["All Facilities"] + sorted(set(admin_names + data_names))
    selected_facility = st.sidebar.selectbox("Facility", facility_options)

    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    start_date, end_date = min_date, max_date
    date_range = st.sidebar.date_input(
        "Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )

    energy_threshold = st.sidebar.slider(
        "Energy Alert Threshold (kWh/wafer)", 250, 450, 380
    )
    water_threshold = st.sidebar.slider("Water Alert Threshold (L/wafer)", 250, 520, 430)
    waste_threshold = st.sidebar.slider("Waste Alert Threshold (kg)", 3000, 7000, 5200)

    filtered = df.copy()
    if selected_facility != "All Facilities":
        filtered = filtered[filtered["facility_name"] == selected_facility]

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered["timestamp"].dt.date >= start_date)
            & (filtered["timestamp"].dt.date <= end_date)
        ]

    facility_id_param = None
    if selected_facility != "All Facilities" and not filtered.empty:
        facility_id_param = filtered["facility_id"].iloc[0]

    score_data = fetch_json(
        "/score",
        params={
            "facility_id": facility_id_param,
            "start": str(start_date),
            "end": str(end_date),
        },
    )

    if score_data is None:
        score_data = {"score": 0, "tier": "Bronze", "components": {}}

    def metric_card(label, value, suffix=""):
        # Metric cards should stay readable even when a filtered view has missing values.
        if pd.isna(value):
            value = 0.0
        st.metric(label, f"{value:,.2f}{suffix}")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("kWh per Wafer", filtered["energy_kwh_per_wafer"].mean(), "")
    with col2:
        metric_card("Water per Wafer", filtered["water_per_wafer_l"].mean(), " L")
    with col3:
        metric_card("Waste Compliance", filtered["waste_compliance_pct"].mean(), " %")
    with col4:
        metric_card("Scope 2 Emissions", filtered["scope2_tco2e"].mean(), " tCO2e")
    with col5:
        metric_card("Particle Count", filtered["particle_count"].mean(), "")

    score_fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_data["score"],
            title={"text": f"Sustainability Score ({score_data['tier']})"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 60], "color": "#f2c1c1"},
                    {"range": [60, 75], "color": "#f7e1a1"},
                    {"range": [75, 85], "color": "#c6e4b4"},
                    {"range": [85, 100], "color": "#9ad0f5"},
                ],
            },
        )
    )
    score_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=CHART_PAPER_BG,
        plot_bgcolor=CHART_PLOT_BG,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(color="#243447"),
    )

    st.plotly_chart(score_fig, use_container_width=True)

    with st.expander("How the Sustainability Rating is calculated (formula)"):
        st.markdown("**Step 1: Normalize each metric to a 0-100 score**")
        st.latex(r"\text{Inverse metric score} = 100 \times \frac{high - value}{high - low}")
        st.latex(r"\text{Direct metric score} = 100 \times \frac{value - low}{high - low}")
        st.caption("Values are clipped between low and high before scoring.")

        st.markdown("**Step 2: Compute 5 component scores (simple averages)**")
        st.markdown(
            "- **Energy**: energy/wafer, cleanroom energy, utilization, peak energy %, renewable %\n"
            "- **Water**: UPW consumption, water recycling, wastewater treatment, water/wafer\n"
            "- **Waste**: hazardous waste, chemical recycling, solvent recovery, compliance\n"
            "- **Carbon**: scope1, scope2, scope3 emissions\n"
            "- **Cleanroom**: filtration efficiency, particle count, HVAC energy, cleanroom class"
        )

        st.markdown("**Step 3: Overall Sustainability Score**")
        st.latex(
            r"\text{Overall Score} = \frac{\text{Energy} + \text{Water} + \text{Waste} + \text{Carbon} + \text{Cleanroom}}{5}"
        )
        st.caption("All 5 components are equally weighted (20% each).")

        st.markdown("**Tier Mapping**")
        st.markdown("- Platinum: >= 85\n- Gold: 75-84.99\n- Silver: 60-74.99\n- Bronze: < 60")

        component_values = score_data.get("components", {})
        if component_values:
            formula_df = pd.DataFrame(
                [
                    {"Component": k.capitalize(), "Score": round(v, 2)}
                    for k, v in component_values.items()
                ]
            )
            st.dataframe(formula_df, use_container_width=True, hide_index=True)

    alerts = fetch_json(
        "/alerts",
        params={
            "facility_id": facility_id_param,
            "start": str(start_date),
            "end": str(end_date),
            "energy_threshold": energy_threshold,
            "water_threshold": water_threshold,
            "waste_threshold": waste_threshold,
        },
    )

    alert_df = pd.DataFrame(alerts or [])
    if not alert_df.empty:
        if selected_facility == "All Facilities":
            alert_df = alert_df.merge(
                df[["facility_id", "facility_name"]].drop_duplicates(),
                on="facility_id",
                how="left",
            )
        else:
            alert_df["facility_name"] = selected_facility

    def _add_alert_markers(fig, metric_key, label):
        # Overlay alert markers directly on the trend line to connect spikes with workflow items.
        if alert_df.empty:
            return
        metric_alerts = alert_df[alert_df["metric"] == metric_key]
        if metric_alerts.empty:
            return
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(metric_alerts["timestamp"]),
                y=metric_alerts["value"],
                mode="markers",
                name=f"{label} Alerts",
                marker=dict(size=10, color="#ff6b6b", symbol="x"),
            )
        )

    st.subheader("Trends")
    trend_cols = st.columns(2)

    with trend_cols[0]:
        fig_energy = px.line(
            filtered,
            x="timestamp",
            y="energy_kwh_per_wafer",
            color="facility_name" if selected_facility == "All Facilities" else None,
            title="Energy (kWh per Wafer)",
            markers=True,
            template=PLOTLY_TEMPLATE,
        )
        style_time_series_chart(fig_energy, "Energy (kWh per Wafer)")
        _add_alert_markers(fig_energy, "energy_kwh_per_wafer", "Energy")
        st.plotly_chart(fig_energy, use_container_width=True)

    with trend_cols[1]:
        fig_water = px.line(
            filtered,
            x="timestamp",
            y="water_per_wafer_l",
            color="facility_name" if selected_facility == "All Facilities" else None,
            title="Water per Wafer (L)",
            markers=True,
            template=PLOTLY_TEMPLATE,
        )
        style_time_series_chart(fig_water, "Water per Wafer (L)")
        _add_alert_markers(fig_water, "water_per_wafer_l", "Water")
        st.plotly_chart(fig_water, use_container_width=True)

    trend_cols_2 = st.columns(2)
    with trend_cols_2[0]:
        fig_carbon = px.line(
            filtered,
            x="timestamp",
            y="scope2_tco2e",
            color="facility_name" if selected_facility == "All Facilities" else None,
            title="Scope 2 Emissions (tCO2e)",
            markers=True,
            template=PLOTLY_TEMPLATE,
        )
        style_time_series_chart(fig_carbon, "Scope 2 Emissions (tCO2e)")
        _add_alert_markers(fig_carbon, "scope2_tco2e", "Scope 2")
        st.plotly_chart(fig_carbon, use_container_width=True)

    with trend_cols_2[1]:
        fig_clean = px.line(
            filtered,
            x="timestamp",
            y="particle_count",
            color="facility_name" if selected_facility == "All Facilities" else None,
            title="Cleanroom Particle Count",
            markers=True,
            template=PLOTLY_TEMPLATE,
        )
        style_time_series_chart(fig_clean, "Cleanroom Particle Count")
        _add_alert_markers(fig_clean, "particle_count", "Particle")
        st.plotly_chart(fig_clean, use_container_width=True)

    st.subheader("Forecast")
    metric_options = [
        "energy_kwh_per_wafer",
        "water_per_wafer_l",
        "scope2_tco2e",
        "hazardous_waste_kg",
    ]
    selected_metric = st.selectbox("Metric to Forecast", metric_options)

    forecast_data = fetch_json(
        "/forecast",
        params={"facility_id": facility_id_param, "metric": selected_metric, "periods": 6},
    )

    if forecast_data:
        hist = pd.DataFrame(forecast_data["history"])
        fut = pd.DataFrame(forecast_data["forecast"])
        hist["timestamp"] = pd.to_datetime(hist["timestamp"])
        fut["timestamp"] = pd.to_datetime(fut["timestamp"])
        forecast_fig = go.Figure()
        forecast_fig.add_trace(
            go.Scatter(x=hist["timestamp"], y=hist["value"], mode="lines", name="History")
        )
        forecast_fig.add_trace(
            go.Scatter(
                x=fut["timestamp"],
                y=fut["value"],
                mode="lines+markers",
                name="Forecast",
                line={"dash": "dash"},
            )
        )
        style_time_series_chart(forecast_fig, f"Forecast: {selected_metric}")
        st.plotly_chart(forecast_fig, use_container_width=True)
    else:
        st.info("Forecast unavailable. Start the API for forecasting.")

    st.subheader("Alerts")
    if not alert_df.empty:
        st.dataframe(alert_df, use_container_width=True)
    else:
        st.success("No alerts triggered for the selected period.")

with tabs[1]:
    st.subheader("Users & Roles")
    if st.session_state.get("auth_role") != "Manager/Admin":
        st.warning("Admin access required.")
    else:
        # Admin management stays on a single page by grouping CRUD actions into forms and expanders.
        users = fetch_json("/admin/users") or []
        st.dataframe(pd.DataFrame(users), use_container_width=True)
        with st.form("create_user"):
            col_a, col_b = st.columns(2)
            user_id = col_a.text_input("User ID")
            name = col_b.text_input("Name")
            col_c, col_d = st.columns(2)
            role = col_c.selectbox("Role", ["Employer", "Support Staff", "Manager/Admin"])
            email = col_d.text_input("Email (optional)")
            password = st.text_input("Password (optional)", type="password")
            submitted = st.form_submit_button("Create User")
            if submitted:
                created = post_json(
                    "/admin/users",
                    {
                        "user_id": user_id,
                        "name": name,
                        "role": role,
                        "email": email or None,
                        "password": password or None,
                    },
                )
                if created:
                    st.success("User created.")
                    st.rerun()
                else:
                    st.error("Failed to create user.")
        with st.expander("Update user"):
            with st.form("update_user"):
                target_user_id = st.text_input("Target User ID")
                col_a, col_b = st.columns(2)
                name = col_a.text_input("New Name (optional)")
                role = col_b.selectbox(
                    "New Role (optional)",
                    ["", "Employer", "Support Staff", "Manager/Admin"],
                )
                email = st.text_input("New Email (optional)")
                password = st.text_input("New Password (optional)", type="password")
                submitted = st.form_submit_button("Update User")
                if submitted:
                    payload = {}
                    if name:
                        payload["name"] = name
                    if role:
                        payload["role"] = role
                    if email:
                        payload["email"] = email
                    if password:
                        payload["password"] = password
                    if not target_user_id or not payload:
                        st.error("Provide user ID and at least one field.")
                    else:
                        updated = patch_json(f"/admin/users/{target_user_id}", payload)
                        if updated:
                            st.success("User updated.")
                            st.rerun()
                        else:
                            st.error("Failed to update user.")
        with st.expander("Delete user"):
            with st.form("delete_user"):
                target_user_id = st.text_input("User ID to Delete")
                submitted = st.form_submit_button("Delete User")
                if submitted:
                    if not target_user_id:
                        st.error("Enter user ID.")
                    else:
                        deleted = delete_json(f"/admin/users/{target_user_id}")
                        if deleted:
                            st.success("User deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete user.")

with tabs[2]:
    st.subheader("Facilities")
    if st.session_state.get("auth_role") != "Manager/Admin":
        st.warning("Admin access required.")
    else:
        facilities = fetch_json("/admin/facilities") or []
        st.dataframe(pd.DataFrame(facilities), use_container_width=True)
        with st.form("create_facility"):
            col_a, col_b = st.columns(2)
            facility_id = col_a.text_input("Facility ID")
            facility_name = col_b.text_input("Facility Name")
            region = st.text_input("Region (optional)")
            submitted = st.form_submit_button("Add Facility")
            if submitted:
                created = post_json(
                    "/admin/facilities",
                    {
                        "facility_id": facility_id,
                        "facility_name": facility_name,
                        "region": region or None,
                    },
                )
                if created:
                    st.success("Facility added.")
                    st.rerun()
                else:
                    st.error("Failed to add facility.")
        with st.expander("Update facility"):
            with st.form("update_facility"):
                target_facility_id = st.text_input("Target Facility ID")
                col_a, col_b = st.columns(2)
                facility_name = col_a.text_input("New Facility Name (optional)")
                region = col_b.text_input("New Region (optional)")
                submitted = st.form_submit_button("Update Facility")
                if submitted:
                    payload = {}
                    if facility_name:
                        payload["facility_name"] = facility_name
                    if region:
                        payload["region"] = region
                    if not target_facility_id or not payload:
                        st.error("Provide facility ID and at least one field.")
                    else:
                        updated = patch_json(f"/admin/facilities/{target_facility_id}", payload)
                        if updated:
                            st.success("Facility updated.")
                            st.rerun()
                        else:
                            st.error("Failed to update facility.")
        with st.expander("Delete facility"):
            with st.form("delete_facility"):
                target_facility_id = st.text_input("Facility ID to Delete")
                submitted = st.form_submit_button("Delete Facility")
                if submitted:
                    if not target_facility_id:
                        st.error("Enter facility ID.")
                    else:
                        deleted = delete_json(f"/admin/facilities/{target_facility_id}")
                        if deleted:
                            st.success("Facility deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete facility.")

with tabs[3]:
    st.subheader("Assignments")
    if st.session_state.get("auth_role") != "Manager/Admin":
        st.warning("Admin access required.")
    else:
        st.caption("Auto-assigned support ownership for each facility.")
        assignments = fetch_json("/admin/assignments") or []
        assignment_df = pd.DataFrame(assignments)
        if assignment_df.empty:
            st.info("No assignments available yet.")
        else:
            summary_cols = st.columns(3)
            summary_cols[0].metric("Assignments", len(assignment_df))
            summary_cols[1].metric("Facilities Covered", assignment_df["facility_id"].nunique())
            summary_cols[2].metric("Support Owners", assignment_df["user_id"].nunique())
            st.dataframe(
                compact_table(
                    assignment_df,
                    [
                        "facility_id",
                        "user_id",
                        "metric_owner",
                        "escalation_contact",
                        "assignment_id",
                    ],
                ),
                use_container_width=True,
                hide_index=True,
            )
        st.info("Manual assignment entry is off. New alerts are routed automatically.")

with tabs[4]:
    st.subheader("Alerts Resolution")
    if st.session_state.get("auth_role") != "Manager/Admin":
        st.warning("Admin access required.")
    else:
        # This section exposes the operational workflow that is also triggered automatically by alerts.
        st.caption(
            "When an alert is created, the backend automatically assigns it to support staff, "
            "records history, and triggers admin notifications when escalation is needed."
        )
        alert_items = fetch_json("/admin/alerts") or []
        st.dataframe(pd.DataFrame(alert_items), use_container_width=True)
        with st.form("create_alert"):
            col_a, col_b = st.columns(2)
            auto_alert_id = f"alert-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            alert_id = col_a.text_input("Alert ID", value=auto_alert_id)
            facility_id = col_b.text_input("Facility ID")
            col_c, col_d = st.columns(2)
            metric = col_c.text_input("Metric")
            value = col_d.number_input("Value", value=0.0, format="%.2f")
            status = st.selectbox(
                "Status",
                ["open", "in_progress", "resolved", "needs_info", "unresolved", "escalated"],
            )
            submitted = st.form_submit_button("Create Alert")
            if submitted:
                created = post_json(
                    "/admin/alerts",
                    {
                        "alert_id": alert_id,
                        "facility_id": facility_id,
                        "metric": metric,
                        "value": value,
                        "status": status,
                        "resolution_note": None,
                        "resolved_by": None,
                    },
                )
                if created:
                    st.success("Alert created.")
                    st.rerun()
                else:
                    st.error("Failed to create alert.")

        with st.form("resolve_alert"):
            col_a, col_b = st.columns(2)
            resolve_id = col_a.text_input("Alert ID to Update")
            status = col_b.selectbox(
                "New Status",
                ["open", "in_progress", "resolved", "needs_info", "unresolved", "escalated"],
            )
            resolution_note = st.text_input("Resolution Note (optional)")
            resolved_by = st.text_input("Resolved By (optional)")
            submitted = st.form_submit_button("Update Alert")
            if submitted:
                updated = patch_json(
                    f"/admin/alerts/{resolve_id}",
                    {
                        "status": status,
                        "resolution_note": resolution_note or None,
                        "resolved_by": resolved_by or None,
                    },
                )
                if updated:
                    st.success("Alert updated.")
                    st.rerun()
                else:
                    st.error("Failed to update alert.")

        st.markdown("#### Alert History")
        history = fetch_json("/admin/alerts/history") or []
        st.dataframe(pd.DataFrame(history), use_container_width=True)

with tabs[5]:
    st.subheader("Notifications")
    if st.session_state.get("auth_role") != "Manager/Admin":
        st.warning("Admin access required.")
    else:
        st.caption("Auto-generated workflow updates for assignment and escalation.")
        notifications = fetch_json("/admin/notifications") or []
        notification_df = pd.DataFrame(notifications)
        if notification_df.empty:
            st.info("No notifications generated yet.")
        else:
            summary_cols = st.columns(3)
            summary_cols[0].metric("Notifications", len(notification_df))
            summary_cols[1].metric(
                "Queued",
                int((notification_df["status"] == "queued").sum()) if "status" in notification_df else 0,
            )
            summary_cols[2].metric(
                "Recipients",
                notification_df["recipient"].nunique() if "recipient" in notification_df else 0,
            )
            st.dataframe(
                compact_table(
                    notification_df,
                    ["channel", "recipient", "status", "message", "notification_id"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        st.info("Manual notification queueing is off. Alerts create updates automatically.")

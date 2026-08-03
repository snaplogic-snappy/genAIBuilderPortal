import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone
from collections import defaultdict

# ── Portal metadata (auto-discovered by GenAI_Demo.py) ───────────────────────
DEMO_METADATA = {
    "categories": ["Business", "Technical"],
    "tags": ["FinOps", "Platform Cost", "Chargeback", "Snowflake", "Analytics", "Business Units"],
}

# ── Configuration ─────────────────────────────────────────────────────────────
_TASK_URL = (
    "https://emea.snaplogic.com/api/1/rest/slsched/feed/"
    "ConnectFasterInc/Konstantin/Demo%20-%20SnapLogic%20CoE/"
    "SL_Runtime_Events_From_Snowflake%20Task"
)
try:
    _BEARER = st.secrets.get("SL_CHARGEBACK_BEARER", "bwUXmqyneX9RFmFPmlqIbiMAvSXdJcH7")
except Exception:
    _BEARER = "bwUXmqyneX9RFmFPmlqIbiMAvSXdJcH7"

# Cost model — $/node/month, applied uniformly for the demo
_NODE_COST_MONTHLY = 1_200
_SHARED_NODES      = 4
_PLATFORM_OVERHEAD = 8_000
_MAX_EXEC_SEC      = 3_600

# BU detection: PATH prefix → BU name (longest-match wins)
_PATH_TO_BU = {
    "ConnectFasterInc/Konstantin/": "Platform Engineering",
    "ConnectFasterInc/projects/":   "Engineering",
    "ConnectFasterInc/SalesOps/":   "Sales Operations",
    "ConnectFasterInc/Marketing/":  "Marketing",
    "ConnectFasterInc/Finance/":    "Finance",
    "ConnectFasterInc/":            "Other",
}
_BU_COLORS = {
    "Platform Engineering": "#4073FF",
    "Engineering":          "#42A5D2",
    "Sales Operations":     "#FF7D3F",
    "Marketing":            "#6366F1",
    "Finance":              "#10B981",
    "Other":                "#8A9BB5",
}


# ── Data fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_rows():
    try:
        resp = requests.get(
            _TASK_URL,
            headers={"Authorization": f"Bearer {_BEARER}"},
            timeout=180,
        )
        resp.raise_for_status()
        raw = resp.text.strip()
        # Try JSON array first, fall back to NDJSON
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data, None
            if isinstance(data, dict):
                # Unwrap common SnapLogic envelope shapes
                for key in ("response_map", "entries", "rows", "data"):
                    if key in data and isinstance(data[key], list):
                        return data[key], None
                return [data], None
        except json.JSONDecodeError:
            rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
            return rows, None
    except Exception as exc:
        return None, str(exc)


def _bu_from_path(path):
    best_key, best_bu = "", "Other"
    for prefix, bu in _PATH_TO_BU.items():
        if path.startswith(prefix) and len(prefix) > len(best_key):
            best_key, best_bu = prefix, bu
    return best_bu


def _parse_month(ts):
    """Return 'MMM YYYY' from ISO timestamp string."""
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts[:19], fmt[:len(fmt)]).strftime("%b %Y")
        except Exception:
            pass
    try:
        return datetime.fromisoformat(ts[:19]).strftime("%b %Y")
    except Exception:
        return "Unknown"


def _aggregate(rows):
    """Aggregate rows → monthly stats by BU."""
    monthly_bu = defaultdict(lambda: defaultdict(lambda: {"count": 0, "dur_sec": 0, "failures": 0}))
    for row in rows:
        path   = str(row.get("PATH") or row.get("path") or "")
        status = str(row.get("STATUS") or row.get("status") or "").lower()
        ts     = str(row.get("START_TIME") or row.get("start_time") or "")
        try:
            dur = float(row.get("DURATION_SEC") or row.get("duration_sec") or 0)
        except (ValueError, TypeError):
            dur = 0
        dur = min(dur, _MAX_EXEC_SEC)
        month  = _parse_month(ts) if ts else "Unknown"
        bu     = _bu_from_path(path)
        cell   = monthly_bu[month][bu]
        cell["count"]    += 1
        cell["dur_sec"]  += dur
        cell["failures"] += 1 if "fail" in status or "error" in status else 0
    return monthly_bu


def _cost_for_month(bu_stats):
    """Simple cost model: shared node + overhead proportional to exec minutes."""
    total_min = sum(s["dur_sec"] / 60 for s in bu_stats.values()) or 1
    node_cost = _SHARED_NODES * _NODE_COST_MONTHLY
    result = {}
    for bu, s in bu_stats.items():
        share     = (s["dur_sec"] / 60) / total_min
        exec_cost = node_cost * share
        overhead  = _PLATFORM_OVERHEAD * share
        result[bu] = round(exec_cost + overhead, 0)
    return result


# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chargeback Console | SnapLogic",
    page_icon="💰",
    layout="wide",
)

st.title("💰 SnapLogic Platform Chargeback Console")
st.markdown(
    "Allocate SnapLogic platform costs across Business Units based on actual pipeline execution data "
    "pulled live from **Snowflake** via a SnapLogic Triggered Task."
)

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Loading execution data from Snowflake… (~15 s first load, cached 30 min)"):
    rows, err = _fetch_rows()

if err or not rows:
    st.error(f"Could not load Snowflake data: {err or 'empty response'}")
    st.info("Check that the SnapLogic Triggered Task is running and the bearer token is valid.")
    st.stop()

monthly_bu = _aggregate(rows)

# Sort months chronologically
_MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
all_months = sorted(
    monthly_bu.keys(),
    key=lambda m: (
        int(m.split()[-1]) * 12 + _MONTH_ORDER.index(m.split()[0])
        if len(m.split()) == 2 and m.split()[0] in _MONTH_ORDER else 0
    ),
)

# Current/latest month
latest_month = all_months[-1] if all_months else None
latest_stats = monthly_bu.get(latest_month, {})
latest_costs = _cost_for_month(latest_stats)

total_exec     = sum(s["count"]    for s in latest_stats.values())
total_failures = sum(s["failures"] for s in latest_stats.values())
total_cost     = sum(latest_costs.values())
error_rate     = (total_failures / total_exec * 100) if total_exec else 0

# ── Data source banner ────────────────────────────────────────────────────────
fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.success(
    f"📡 **Live Snowflake data** — {len(rows):,} executions loaded · "
    f"cached 30 min · last fetched {fetched_at}"
)

if st.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.subheader(f"Platform Snapshot — {latest_month}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Estimated Platform Cost", f"${total_cost:,.0f}", help="Shared node + overhead, proportional to exec time")
k2.metric("Pipeline Executions",     f"{total_exec:,}")
k3.metric("Error Rate",              f"{error_rate:.1f}%")
k4.metric("Business Units Active",   str(len(latest_stats)))

st.markdown("---")

# ── Monthly cost trend ────────────────────────────────────────────────────────
st.subheader("Monthly Cost by Business Unit")

trend_rows = []
for m in all_months:
    costs = _cost_for_month(monthly_bu[m])
    for bu, cost in costs.items():
        trend_rows.append({"Month": m, "Business Unit": bu, "Cost ($)": cost})

if trend_rows:
    df_trend = pd.DataFrame(trend_rows)
    fig_trend = px.bar(
        df_trend, x="Month", y="Cost ($)", color="Business Unit",
        color_discrete_map=_BU_COLORS,
        barmode="stack", height=360,
    )
    fig_trend.update_layout(
        xaxis_title="", yaxis_tickformat="$,.0f",
        legend_title="Business Unit",
        margin=dict(t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# ── Current month: cost share + exec volume ───────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader(f"Cost Share by BU — {latest_month}")
    if latest_costs:
        names  = list(latest_costs.keys())
        values = list(latest_costs.values())
        colors = [_BU_COLORS.get(n, "#888") for n in names]
        fig_donut = go.Figure(go.Pie(
            labels=names, values=values,
            hole=0.45,
            marker_colors=colors,
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            textinfo="percent",
            textfont_size=11,
            textfont_color="white",
            textposition="inside",
        ))
        fig_donut.update_layout(
            height=340,
            margin=dict(t=10, b=10, l=20, r=160),
            legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left", font=dict(size=11)),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_donut, use_container_width=True)

with c2:
    st.subheader(f"Execution Volume by BU — {latest_month}")
    if latest_stats:
        exec_rows = sorted(
            [{"Business Unit": bu, "Executions": s["count"], "Failures": s["failures"]}
             for bu, s in latest_stats.items()],
            key=lambda x: -x["Executions"],
        )
        df_exec = pd.DataFrame(exec_rows)
        fig_bar = go.Figure()
        for _, row in df_exec.iterrows():
            fig_bar.add_trace(go.Bar(
                name=row["Business Unit"],
                y=[row["Business Unit"]],
                x=[row["Executions"]],
                orientation="h",
                marker_color=_BU_COLORS.get(row["Business Unit"], "#888"),
                hovertemplate=f"<b>{row['Business Unit']}</b><br>{row['Executions']:,} executions<br>{row['Failures']:,} failures<extra></extra>",
                showlegend=False,
            ))
        fig_bar.update_layout(
            height=340,
            xaxis_title="Executions",
            xaxis_tickformat=",.0f",
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10, b=40, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── Allocation table ──────────────────────────────────────────────────────────
st.subheader(f"Detailed Allocation — {latest_month}")

tbl_rows = []
for bu in sorted(latest_costs, key=lambda b: -latest_costs[b]):
    s = latest_stats.get(bu, {})
    cost = latest_costs[bu]
    tbl_rows.append({
        "Business Unit":  bu,
        "Est. Cost ($)":  cost,
        "Share (%)":      round(cost / total_cost * 100, 1) if total_cost else 0,
        "Executions":     s.get("count", 0),
        "Exec Minutes":   round(s.get("dur_sec", 0) / 60, 1),
        "Failures":       s.get("failures", 0),
        "Error Rate (%)": round(s.get("failures", 0) / s.get("count", 1) * 100, 1) if s.get("count") else 0,
    })

df_tbl = pd.DataFrame(tbl_rows)
st.dataframe(
    df_tbl.style.format({
        "Est. Cost ($)":  "${:,.0f}",
        "Share (%)":      "{:.1f}%",
        "Executions":     "{:,}",
        "Exec Minutes":   "{:,.1f}",
        "Error Rate (%)": "{:.1f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# ── About ─────────────────────────────────────────────────────────────────────
with st.expander("ℹ️ About this demo"):
    st.markdown("""
**How it works:**

1. A SnapLogic **Triggered Task** queries the `PIPELINE_EXECUTIONS` table in Snowflake and returns all runtime events as a JSON array.
2. This page fetches that data via a single POST request, aggregates by Business Unit (using pipeline PATH prefix matching) and month, then applies a simple cost model (shared Snaplex node cost + platform overhead proportional to execution time).
3. Results are **cached for 30 minutes** in Streamlit's memory — hit "Refresh data" to force a live pull.

**Cost model (simplified for demo):**
- Shared Snaplex: 4 nodes × $1,200/node/month = $4,800/month
- Platform overhead: $8,000/month
- Allocation key: proportional to adjusted execution minutes

**Full Chargeback Console** features (separate app):
- Dedicated & shared Snaplex cost split
- User → BU mapping with CSV import
- Headcount / usage / blended allocation keys
- 7-month trend with real + mock data overlay
- Per-BU drill-down, reports, and CSV export

> **Architecture:** SnapLogic pipeline → Snowflake `PIPELINE_EXECUTIONS` → SnapLogic Triggered Task → Streamlit
    """)

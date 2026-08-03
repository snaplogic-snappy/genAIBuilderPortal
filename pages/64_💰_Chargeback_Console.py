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

# Color palette — assigned round-robin to discovered project spaces
_COLOR_PALETTE = [
    "#4073FF", "#42A5D2", "#FF7D3F", "#6366F1",
    "#10B981", "#F59E0B", "#EC4899", "#8B5CF6",
    "#14B8A6", "#F97316", "#3B82F6", "#84CC16",
]


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
    """Extract project space (second path segment) as the BU name."""
    parts = path.lstrip("/").split("/")
    return parts[1] if len(parts) >= 2 else "Other"


def _bu_color_map(bus):
    return {bu: _COLOR_PALETTE[i % len(_COLOR_PALETTE)] for i, bu in enumerate(sorted(bus))}


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

# ── Link to full app ───────────────────────────────────────────────────────────
_fc1, _fc2 = st.columns([3, 1])
with _fc1:
    st.info(
        "**Want the full experience?** The complete Chargeback Console includes 5 pages: "
        "Dashboard, BU Management, Asset Mapping, Cost Configuration, and Reports — "
        "with per-BU drill-downs, user→BU mappings, CSV export, and dedicated Snaplex cost split."
    )
with _fc2:
    st.link_button(
        "🚀 Open Full Console",
        "https://sl-chargeback.streamlit.app/",
        use_container_width=True,
        type="primary",
    )

st.markdown("---")

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

# Build dynamic BU color map from all discovered BUs
all_bus = sorted({bu for month_data in monthly_bu.values() for bu in month_data})
BU_COLORS = _bu_color_map(all_bus)

# ── Sidebar controls ──────────────────────────────────────────────────────────
st.sidebar.title("💰 Chargeback Console")
st.sidebar.markdown("---")

selected_month = st.sidebar.selectbox(
    "📅 Select Month",
    options=all_months,
    index=len(all_months) - 1,
)

# BU filter
bu_filter = st.sidebar.multiselect(
    "🏢 Filter Business Units",
    options=all_bus,
    default=all_bus,
    help="Show only selected project spaces",
)
if not bu_filter:
    bu_filter = all_bus

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.sidebar.caption(f"📡 {len(rows):,} rows · cached 30 min\n{fetched_at}")

# ── Filtered stats for selected month ────────────────────────────────────────
sel_stats  = {bu: v for bu, v in monthly_bu.get(selected_month, {}).items() if bu in bu_filter}
sel_costs  = _cost_for_month(sel_stats)

total_exec     = sum(s["count"]    for s in sel_stats.values())
total_failures = sum(s["failures"] for s in sel_stats.values())
total_cost     = sum(sel_costs.values())
error_rate     = (total_failures / total_exec * 100) if total_exec else 0

# ── Data source banner ────────────────────────────────────────────────────────
st.success(
    f"📡 **Live Snowflake data** — {len(rows):,} executions · "
    f"{len(all_bus)} project spaces · last fetched {fetched_at}"
)

st.markdown("---")

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.subheader(f"Platform Snapshot — {selected_month}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Estimated Platform Cost", f"${total_cost:,.0f}", help="Shared node + overhead, proportional to exec time")
k2.metric("Pipeline Executions",     f"{total_exec:,}")
k3.metric("Error Rate",              f"{error_rate:.1f}%")
k4.metric("Project Spaces Active",   str(len(sel_stats)))

st.markdown("---")

# ── Monthly cost trend ────────────────────────────────────────────────────────
st.subheader("Monthly Cost by Project Space")

trend_rows = []
for m in all_months:
    costs = _cost_for_month({bu: v for bu, v in monthly_bu[m].items() if bu in bu_filter})
    for bu, cost in costs.items():
        trend_rows.append({"Month": m, "Project Space": bu, "Cost ($)": cost})

if trend_rows:
    df_trend = pd.DataFrame(trend_rows)
    fig_trend = px.bar(
        df_trend, x="Month", y="Cost ($)", color="Project Space",
        color_discrete_map=BU_COLORS,
        barmode="stack", height=360,
    )
    fig_trend.update_layout(
        xaxis_title="", yaxis_tickformat="$,.0f",
        legend_title="Project Space",
        margin=dict(t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# ── Selected month: cost share + exec volume ──────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader(f"Cost Share — {selected_month}")
    if sel_costs:
        names  = list(sel_costs.keys())
        values = list(sel_costs.values())
        colors = [BU_COLORS.get(n, "#888") for n in names]
        fig_donut = go.Figure(go.Pie(
            labels=names, values=values,
            hole=0.45,
            marker_colors=colors,
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            textinfo="percent",
            textfont_size=11,
            textposition="inside",
        ))
        fig_donut.update_layout(
            height=360,
            margin=dict(t=10, b=10, l=20, r=180),
            legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left", font=dict(size=10)),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_donut, use_container_width=True)

with c2:
    st.subheader(f"Execution Volume — {selected_month}")
    if sel_stats:
        exec_rows = sorted(
            [{"Project Space": bu, "Executions": s["count"], "Failures": s["failures"]}
             for bu, s in sel_stats.items()],
            key=lambda x: -x["Executions"],
        )
        df_exec = pd.DataFrame(exec_rows)
        _n = len(df_exec)
        fig_bar = go.Figure()
        for _, row in df_exec.iterrows():
            fig_bar.add_trace(go.Bar(
                name=row["Project Space"],
                y=[row["Project Space"]],
                x=[row["Executions"]],
                orientation="h",
                marker_color=BU_COLORS.get(row["Project Space"], "#888"),
                hovertemplate=(
                    f"<b>{row['Project Space']}</b><br>"
                    f"{row['Executions']:,} executions<br>"
                    f"{row['Failures']:,} failures<extra></extra>"
                ),
                showlegend=False,
            ))
        fig_bar.update_layout(
            height=max(360, _n * 30 + 60),
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
st.subheader(f"Detailed Allocation — {selected_month}")

tbl_rows = []
for bu in sorted(sel_costs, key=lambda b: -sel_costs[b]):
    s = sel_stats.get(bu, {})
    cost = sel_costs[bu]
    tbl_rows.append({
        "Project Space":  bu,
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
2. This page fetches that data, aggregates by Business Unit (project space extracted from pipeline PATH) and month, then applies a simple cost model (shared Snaplex node cost + platform overhead, proportional to execution time).
3. Results are **cached for 30 minutes** — hit "Refresh data" to force a live pull.

**Live data snapshot (Jul 2026):**
- **446,091** total pipeline executions loaded from Snowflake
- **$59,800** estimated platform cost for July
- **89,307** executions in July · **3.20%** error rate
- **9 Business Units:** GenAI & Integration Platform, Pre-Sales Engineering, Platform Engineering, Insurance Practice, Healthcare Practice, Training & Enablement, MCP Platform (COE), Professional Services, Other / External

**Cost model (simplified for demo):**
- Shared Snaplex: 4 nodes × $1,200/node/month = $4,800/month
- Platform overhead: $8,000/month
- Allocation key: proportional to adjusted execution minutes

**Full Chargeback Console** (https://sl-chargeback.streamlit.app/) adds:
- Dedicated & shared Snaplex cost split per node
- User → BU mapping with named project space resolution
- Headcount / usage / blended allocation keys
- 7-month trend with real + mock data overlay
- Per-BU drill-down, reports, and CSV export

> **Architecture:** SnapLogic pipelines → Snowflake `PIPELINE_EXECUTIONS` → SnapLogic Triggered Task → Streamlit
    """)

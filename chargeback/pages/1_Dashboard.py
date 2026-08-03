"""
Dashboard — 7-month trend, stacked cost view, execution metrics.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from mock_data import (
    init_session_state, compute_monthly_costs, get_bu_name, get_snaplex_name,
    total_executions_for_month, load_seconds,
    rows_to_exec_data, merge_exec_data,
    load_exec_cache, start_snowflake_refresh, check_refresh_done,
    _generate_exec_data,
    MONTHS, CURRENT_MONTH, CURRENT_MONTH_PROGRESS,
    BU_COLORS, CATEGORY_COLORS,
)
from theme import inject_brand

st.set_page_config(page_title="Dashboard | Chargeback Console", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")
init_session_state(st)

# ── Background Snowflake refresh ──────────────────────────────────────────────
if not st.session_state.get("_snowflake_refresh_started"):
    st.session_state["_snowflake_refresh_started"] = True
    start_snowflake_refresh()

_refresh_rows, _refresh_at = check_refresh_done()
if _refresh_rows:
    _real_ed = rows_to_exec_data(
        _refresh_rows, st.session_state.snaplexes,
        project_mappings=st.session_state.get("project_mappings"),
    )
    st.session_state.exec_data = merge_exec_data(_generate_exec_data(), _real_ed)
    st.session_state["_exec_data_source"]     = "snowflake"
    st.session_state["_exec_data_fetched_at"] = _refresh_at
    st.session_state.pop("_refresh_poll", None)
    st.rerun()

inject_brand(st, active="Dashboard")

st.title("📊 Dashboard")
st.caption("7-month cost trend, execution volumes, and allocation breakdown.")

# ── Data source banner ────────────────────────────────────────────────────────
_exec_source   = st.session_state.get("_exec_data_source", "mock")
_exec_fetched  = st.session_state.get("_exec_data_fetched_at", "")
_b1, _b2 = st.columns([6, 1])
if _exec_source == "snowflake":
    _total_rows = sum(
        d.get("count", 0)
        for _md in st.session_state.exec_data.values()
        for _bd in _md.values()
        for d in _bd.values()
    )
    _b1.success(
        f"📡 **Snowflake data** — {_total_rows:,} executions loaded. "
        f"Last fetched: {_exec_fetched or 'unknown'}."
    )
else:
    _b1.info(
        "🧪 **Demo mode** — generated data. Snowflake refresh running in background; "
        "page will update automatically when ready (~15 s)."
    )
if _b2.button("🔄 Refresh", key="btn_refresh_snowflake", help="Fetch latest data from Snowflake"):
    st.session_state.pop("_snowflake_refresh_started", None)
    st.session_state.pop("_refresh_poll", None)
    st.rerun()

# ── Month selector ────────────────────────────────────────────────────────────
selected_month = st.selectbox("Select month", MONTHS, index=len(MONTHS) - 1)

# ── Compute all months ────────────────────────────────────────────────────────
all_costs = {
    m: compute_monthly_costs(m, st.session_state.exec_data,
                             st.session_state.snaplexes, st.session_state.bus,
                             st.session_state.overhead,
                             user_mappings=st.session_state.get("user_mappings"))
    for m in MONTHS
}

sel_costs  = all_costs[selected_month]
total_cost = sum(c["total"] for c in sel_costs.values())
is_current = selected_month == CURRENT_MONTH

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
total_exec = total_executions_for_month(selected_month, st.session_state.exec_data)
total_failures = sum(
    d.get("failures", 0)
    for bu_data in st.session_state.exec_data.get(selected_month, {}).values()
    for d in bu_data.values()
)
error_rate = total_failures / total_exec * 100 if total_exec else 0

k1.metric("Total Platform Cost", f"${total_cost:,.0f}")
k2.metric("Pipeline Executions", f"{total_exec:,}")
k3.metric("Error Rate", f"{error_rate:.2f}%")

st.markdown("---")

# ── Stacked bar: cost by category per month ───────────────────────────────────
st.subheader("Monthly Platform Cost by Category")

cat_rows = []
for m in MONTHS:
    mc = all_costs[m]
    cat_rows.append({
        "Month":             m,
        "Dedicated Snaplex": sum(c["dedicated_snaplex"] for c in mc.values()),
        "Shared Snaplex":    sum(c["shared_snaplex"]    for c in mc.values()),
        "Platform Overhead": sum(c["overhead_share"]    for c in mc.values()),
    })
df_cat = pd.DataFrame(cat_rows)

fig_stack = go.Figure()
for cat, color in CATEGORY_COLORS.items():
    fig_stack.add_trace(go.Bar(
        name=cat, x=df_cat["Month"], y=df_cat[cat],
        marker_color=color,
    ))
fig_stack.update_layout(
    barmode="stack", height=360,
    xaxis_title="", yaxis_title="USD",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=10, b=10),
    yaxis_tickformat="$,.0f",
)
st.plotly_chart(fig_stack, use_container_width=True)

st.markdown("---")

# ── Line chart: cost per BU over time ────────────────────────────────────────
st.subheader("Cost Trend by Business Unit")

bu_trend_rows = []
for m in MONTHS:
    for bid, c in all_costs[m].items():
        bu_trend_rows.append({
            "Month": m, "BU": get_bu_name(bid, st.session_state.bus), "Cost": c["total"],
        })
df_trend = pd.DataFrame(bu_trend_rows)
bu_color_map = {get_bu_name(bid, st.session_state.bus): BU_COLORS.get(bid, "#888")
                for bid in (c["id"] for c in st.session_state.bus)}

fig_line = px.line(
    df_trend, x="Month", y="Cost", color="BU",
    color_discrete_map=bu_color_map,
    markers=True, height=380,
)
fig_line.update_layout(
    yaxis_tickformat="$,.0f",
    xaxis_title="", yaxis_title="USD",
    legend_title="Business Unit",
    margin=dict(t=10, b=10),
)
st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# ── Detailed table for selected month ────────────────────────────────────────
st.subheader(f"Detailed Allocation — {selected_month}")

rows = []
for bid, c in sorted(sel_costs.items(), key=lambda x: -x[1]["total"]):
    exec_mins = sum(
        load_seconds(d) / 60
        for d in st.session_state.exec_data.get(selected_month, {}).get(bid, {}).values()
    )
    rows.append({
        "Business Unit":       get_bu_name(bid, st.session_state.bus),
        "Dedicated ($)":       round(c["dedicated_snaplex"], 0),
        "Shared ($)":          round(c["shared_snaplex"],    0),
        "Overhead ($)":        round(c["overhead_share"],    0),
        "Total ($)":           round(c["total"],             0),
        "Share (%)":           round(c["total"] / total_cost * 100, 1) if total_cost else 0,
        "Exec Minutes":        round(exec_mins, 1),
    })

df_detail = pd.DataFrame(rows)
st.dataframe(
    df_detail.style
        .format({
            "Dedicated ($)": "${:,.0f}",
            "Shared ($)":    "${:,.0f}",
            "Overhead ($)":  "${:,.0f}",
            "Total ($)":     "${:,.0f}",
            "Share (%)":     "{:.1f}%",
            "Exec Minutes":  "{:,.1f}",
        })
        .background_gradient(subset=["Total ($)"], cmap="Purples"),
    use_container_width=True,
    hide_index=True,
)

# ── Node Runtime by Business Unit ─────────────────────────────────────────────
st.markdown("---")
st.subheader(f"Node Runtime by Business Unit — {selected_month}")
st.caption(
    "Pipeline execution minutes per Snaplex, split by Business Unit. "
    "Includes startup overhead per execution (configurable in Cost Configuration → Allocation Key). "
    "This is the basis for shared node cost allocation."
)

_startup = st.session_state.overhead.get("startup_overhead_sec", 10)
exec_data_month = st.session_state.exec_data.get(selected_month, {})
bus_list = st.session_state.bus

for slx in st.session_state.snaplexes:
    if not (slx.get("nodes") or 0):
        continue

    # Collect adjusted runtime minutes per BU (runtime + startup overhead)
    bu_mins = {}
    bu_counts = {}
    for b in bus_list:
        d = exec_data_month.get(b["id"], {}).get(slx["id"], {})
        raw_secs = load_seconds(d)
        count    = d.get("count", 0)
        adj_mins = (raw_secs + count * _startup) / 60
        if adj_mins > 0:
            bu_mins[b["id"]]   = adj_mins
            bu_counts[b["id"]] = count

    total_mins = sum(bu_mins.values())
    node_cost  = (slx.get("nodes") or 0) * (slx.get("node_cost_monthly") or 0)
    slx_type   = slx["type"].capitalize()

    with st.expander(
        f"**{slx['name']}** — {slx_type} · "
        f"{slx.get('nodes', 0)} node{'s' if (slx.get('nodes') or 0) != 1 else ''} · "
        f"${node_cost:,}/mo · {total_mins:,.0f} adj-exec min",
        expanded=True,
    ):
        if not bu_mins:
            st.info("No executions recorded on this node for the selected month.")
            continue

        is_dedicated = slx.get("type") == "dedicated"
        owner_bu_id  = slx.get("bu_id")
        owner_name   = get_bu_name(owner_bu_id, bus_list) if owner_bu_id else "—"

        if is_dedicated:
            st.info(
                f"**Dedicated Snaplex** — full cost of **${node_cost:,}/mo** charged to "
                f"**{owner_name}**. Usage below is for visibility only, not cost allocation.",
                icon="🔒",
            )

        col_chart, col_table = st.columns([3, 2])

        with col_chart:
            chart_rows = []
            for bid, mins in sorted(bu_mins.items(), key=lambda x: -x[1]):
                bu_name = get_bu_name(bid, bus_list)
                pct     = mins / total_mins * 100 if total_mins else 0
                cost_share = (
                    0 if is_dedicated
                    else (node_cost * mins / total_mins if total_mins and node_cost else 0)
                )
                chart_rows.append({
                    "BU":         bu_name,
                    "Minutes":    mins,
                    "Share":      f"{pct:.1f}%",
                    "Executions": bu_counts.get(bid, 0),
                    "Cost":       cost_share,
                    "color":      BU_COLORS.get(bid, "#888"),
                })
            _df_node = pd.DataFrame(chart_rows)
            _n_bars  = len(_df_node)
            _height  = max(160, _n_bars * 36 + 50)

            fig_node = go.Figure()
            for _, row in _df_node.iterrows():
                hover = (
                    f"<b>{row['BU']}</b><br>"
                    f"{row['Minutes']:,.1f} adj-min ({row['Share']})<br>"
                    f"{row['Executions']:,} executions<br>"
                    + (f"No cost charge — dedicated to {owner_name}" if is_dedicated
                       else f"Cost share: ${row['Cost']:,.0f}")
                    + "<extra></extra>"
                )
                fig_node.add_trace(go.Bar(
                    name=row["BU"],
                    y=[row["BU"]],
                    x=[row["Minutes"]],
                    orientation="h",
                    marker_color=row["color"],
                    hovertemplate=hover,
                    showlegend=False,
                ))
            fig_node.update_layout(
                height=_height,
                xaxis_title="Adjusted Runtime Minutes",
                xaxis_tickformat=",.0f",
                yaxis=dict(autorange="reversed"),
                margin=dict(t=10, b=40, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig_node, use_container_width=True, key=f"node_{slx['id']}")

        with col_table:
            tbl_rows = []
            for bid, mins in sorted(bu_mins.items(), key=lambda x: -x[1]):
                pct = mins / total_mins * 100 if total_mins else 0
                row = {
                    "Business Unit": get_bu_name(bid, bus_list),
                    "Executions":    bu_counts.get(bid, 0),
                    "Adj. Min":      round(mins, 1),
                    "Share (%)":     round(pct, 1),
                }
                if not is_dedicated:
                    row["Cost ($)"] = round(node_cost * mins / total_mins if total_mins and node_cost else 0, 0)
                tbl_rows.append(row)

            fmt = {"Executions": "{:,}", "Adj. Min": "{:,.1f}", "Share (%)": "{:.1f}%"}
            if not is_dedicated:
                fmt["Cost ($)"] = "${:,.0f}"
            st.dataframe(
                pd.DataFrame(tbl_rows).style.format(fmt),
                use_container_width=True,
                hide_index=True,
            )

# ── Auto-poll while waiting for background Snowflake refresh ─────────────────
if (st.session_state.get("_exec_data_source", "mock") == "mock"
        and st.session_state.get("_snowflake_refresh_started")):
    import time as _time
    _poll = st.session_state.get("_refresh_poll", 0)
    if _poll < 12:
        st.session_state["_refresh_poll"] = _poll + 1
        _time.sleep(3)
        st.rerun()

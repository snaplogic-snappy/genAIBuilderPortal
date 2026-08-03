"""
SnapLogic Platform Chargeback Console
Run: streamlit run app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Load .env from the app directory before anything reads os.getenv()
def _load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

_load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import calendar
import streamlit as st
import plotly.express as px
import pandas as pd

from mock_data import (
    init_session_state, compute_monthly_costs, get_bu_name,
    total_executions_for_month, active_environments,
    CURRENT_MONTH, CURRENT_MONTH_PROGRESS, BU_COLORS, CATEGORY_COLORS,
)
from api_client import SnapLogicClient
from theme import inject_brand

st.set_page_config(
    page_title="SnapLogic Chargeback Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session_state(st)
inject_brand(st, active="Home")

# ── Auto-connect to demo org on first load ────────────────────────────────────
_DEMO_SERVER = "https://emea.snaplogic.com"
_DEMO_ORG    = "ConnectFasterInc"
_DEMO_USER   = os.getenv("SNAPLOGIC_USER", "")
_DEMO_PASS   = os.getenv("SNAPLOGIC_PASSWORD", "")
_DEMO_TOKEN  = os.getenv("SNAPLOGIC_DEMO_TOKEN", os.getenv("SNAPLOGIC_TOKEN", ""))

# Connection pre-loaded in init_session_state (mock_data.py) — runs on every page

# Auto-load real data — June and July from Snowflake/CSV, earlier months remain mock
if not st.session_state.get("_real_data_loaded"):
    from snowflake_client import snowflake_pipeline_available, load_executions_via_pipeline

    # Months to load as real data: (year, month_num, label)
    _real_months = [(2026, 6, "Jun 2026"), (2026, 7, "Jul 2026")]
    _dfs_by_month: dict = {}
    _source = None
    _load_errors: list = []

    # ── Primary: Snowflake via SnapLogic pipeline endpoint ────────────────────
    if snowflake_pipeline_available():
        with st.spinner("Loading execution data from Snowflake …"):
            try:
                _df_all_sf = load_executions_via_pipeline()
                if not _df_all_sf.empty and "start_time" in _df_all_sf.columns:
                    for _fy, _fm, _flabel in _real_months:
                        _df_m = _df_all_sf[_df_all_sf["start_time"].dt.month == _fm].copy()
                        if not _df_m.empty:
                            _dfs_by_month[_flabel] = _df_m
                    if _dfs_by_month:
                        _source = "Snowflake (via SnapLogic)"
            except Exception as _e:
                _load_errors.append(f"Snowflake load failed: {_e}")

    # ── Fallback 1: local CSV export ──────────────────────────────────────────
    if not _dfs_by_month:
        from snowflake_client import load_executions_from_csv
        _csv_candidates = [
            os.path.join(os.path.dirname(__file__), "demo_data.csv"),
            os.path.expanduser("~/Downloads/Untitled 3_2026-08-02-1111.csv"),
        ]
        for _csv_path in _csv_candidates:
            if os.path.exists(_csv_path):
                try:
                    _df_all = load_executions_from_csv(_csv_path)
                    if not _df_all.empty and "start_time" in _df_all.columns:
                        for _fy, _fm, _flabel in _real_months:
                            _df_m = _df_all[_df_all["start_time"].dt.month == _fm].copy()
                            if not _df_m.empty:
                                _dfs_by_month[_flabel] = _df_m
                        _source = f"CSV export ({os.path.basename(_csv_path)})"
                        break
                except Exception:
                    pass

    # ── Fallback 2: direct SnapLogic runtime API (July only) ─────────────────
    if not _dfs_by_month and st.session_state.environments:
        _env = st.session_state.environments[0]
        with st.spinner(f"Fetching July execution data directly from {_env['org']} API …"):
            try:
                _fc     = SnapLogicClient.from_env(_env)
                _df_m   = _fc.get_executions_df(2026, 7, max_records=50000)
                if not _df_m.empty:
                    _dfs_by_month["Jul 2026"] = _df_m
                    _source = "SnapLogic API (direct)"
            except Exception as _e:
                st.warning(f"API fetch failed: {_e} — showing demo data.")

    # ── Aggregate each month and update exec_data ────────────────────────────
    _env_ref = (st.session_state.environments[0] if st.session_state.environments
                else {"org": "ConnectFasterInc"})
    _rt_map = {s["snode_id"]: s["id"] for s in st.session_state.snaplexes if s.get("snode_id")}
    _all_real_dfs = []

    for _flabel, _df_m in _dfs_by_month.items():
        _fm_num      = list(calendar.month_abbr).index(_flabel[:3])
        _period_secs = calendar.monthrange(2026, _fm_num)[1] * 86400
        if st.session_state.environments:
            _agg = SnapLogicClient.from_env(_env_ref).aggregate_by_snaplex_and_bu(
                _df_m, st.session_state.project_mappings, _rt_map,
                user_mappings=st.session_state.user_mappings,
            )
            if _agg:
                st.session_state.exec_data[_flabel] = _agg
        _all_real_dfs.append(_df_m)

    # ── Snaplex metrics from most recent month (July) ────────────────────────
    if _all_real_dfs:
        _latest_df   = _dfs_by_month.get("Jul 2026", _all_real_dfs[-1])
        _period_secs = calendar.monthrange(2026, 7)[1] * 86400
        _slx_m = SnapLogicClient.compute_snaplex_metrics(_latest_df, _period_secs)
        for _i, _slx in enumerate(st.session_state.snaplexes):
            _m = _slx_m.get(_slx.get("snode_id", ""))
            if _m:
                st.session_state.snaplexes[_i]["avg_active_pipelines"] = \
                    round(_m["avg_active_pipelines"], 3)

        _live_df = pd.concat(_all_real_dfs, ignore_index=True)
        st.session_state["_live_exec_df"]     = _live_df
        st.session_state["_live_exec_period"] = "Jun–Jul 2026"
        st.session_state["_live_exec_env"]    = _env_ref
        st.session_state["_live_data_source"] = _source
        st.session_state["_real_data_loaded"] = True

    if _load_errors:
        st.session_state["_load_errors"] = _load_errors

# ── Data load warnings (collapsed — only shown when Snowflake pipeline errors) ──
if st.session_state.get("_load_errors"):
    with st.expander("⚠️ Data load warnings", expanded=False):
        for _msg in st.session_state["_load_errors"]:
            st.caption(_msg)

# ── Manual ingest trigger (Snowflake Refresh) ────────────────────────────────
from snowflake_client import trigger_daily_ingest as _trigger_ingest
if os.getenv("SL_INGEST_BEARER") and os.getenv("SL_INGEST_ENDPOINT"):
    with st.expander("🔄 Snowflake Refresh", expanded=False):
        st.caption("Trigger the daily ingest pipeline to pull fresh data into Snowflake.")
        _ic1, _ic2 = st.columns(2)
        if _ic1.button("▶ Run Daily Ingest Now", use_container_width=True):
            with st.spinner("Triggering SL_Chargeback_Daily_Ingest…"):
                try:
                    _r = _trigger_ingest()
                    st.success("✅ Ingest task triggered — runs async on the Snaplex.")
                    st.json(_r)
                except Exception as _e:
                    st.error(f"Failed: {_e}")
        if _ic2.button("🔁 Reload from Snowflake", use_container_width=True):
            st.session_state.pop("_real_data_loaded", None)
            st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#001934 0%,#4073FF 100%);
            padding:1.8rem 2rem;border-radius:12px;margin-bottom:1.5rem;">
  <h1 style="color:white;margin:0;font-size:2rem;border:none;padding:0;">
    SnapLogic Chargeback Console
  </h1>
  <p style="color:rgba(255,255,255,.80);margin:.4rem 0 0;font-size:1rem;">
    Platform cost allocation &amp; business unit chargeback management
  </p>
</div>
""", unsafe_allow_html=True)

# ── Platform Environments ─────────────────────────────────────────────────────
has_envs = len(st.session_state.environments) > 0
with st.expander("🔌 Platform Environments", expanded=not has_envs and not st.session_state.get("_auto_connect_tried")):
    st.markdown(
        "Add one or more SnapLogic organisations (e.g. **Dev**, **UAT**, **Prod**). "
        "Live execution data is pulled per environment and merged in the chargeback model."
    )

    # ── Existing environments ─────────────────────────────────────────────────
    if st.session_state.environments:
        st.markdown("**Connected environments**")
        for i, env in enumerate(st.session_state.environments):
            ec1, ec2, ec3, ec4, ec5 = st.columns([2, 2, 2, 1, 1])
            ec1.markdown(f"**{env['name']}**")
            ec2.caption(env["org"])
            ec3.caption(env["server"])
            badge = "🟢 Connected" if env.get("connected") else "🔴 Error"
            ec4.markdown(badge)
            if ec5.button("🗑️", key=f"rm_env_{i}"):
                st.session_state.environments.pop(i)
                st.rerun()
        st.markdown("---")

    # ── Add new environment ───────────────────────────────────────────────────
    st.markdown("**Add environment**")

    # Quick-fill presets
    pf1, pf2, _ = st.columns([1, 1, 4])
    if pf1.button("⚡ Pre-fill ConnectFasterInc (EMEA)"):
        st.session_state["_new_env_name"]   = "ConnectFasterInc"
        st.session_state["_new_env_server"] = "https://emea.snaplogic.com"
        st.session_state["_new_env_org"]    = "ConnectFasterInc"
        st.rerun()

    auth_method = st.radio("Authentication method", ["Basic Auth (username + password)", "Bearer Token"],
                            horizontal=True, key="add_env_auth_method")

    with st.form("add_env_form"):
        fc1, fc2 = st.columns(2)
        env_name   = fc1.text_input("Environment label",
                                    value=st.session_state.get("_new_env_name", ""),
                                    placeholder="e.g. Production")
        env_server = fc2.text_input("Server URL",
                                    value=st.session_state.get("_new_env_server", ""),
                                    placeholder="https://emea.snaplogic.com")
        fc3, fc4 = st.columns(2)
        env_org = fc3.text_input("Organisation",
                                  value=st.session_state.get("_new_env_org", ""),
                                  placeholder="AcmeCorp")

        env_user = env_pass = env_token = ""
        if auth_method.startswith("Basic"):
            env_user = fc4.text_input("Username", placeholder="user@company.com")
            env_pass = st.text_input("Password", type="password")
        else:
            env_token = fc4.text_input("Bearer Token", type="password")

        if st.form_submit_button("🔗 Test & Add", type="primary"):
            use_basic  = auth_method.startswith("Basic")
            creds_ok   = (use_basic and env_user and env_pass) or (not use_basic and env_token)
            if env_name and env_server and env_org and creds_ok:
                with st.spinner(f"Testing connection to {env_org}…"):
                    if use_basic:
                        client = SnapLogicClient.from_basic_auth(env_server, env_org, env_user, env_pass)
                    else:
                        client = SnapLogicClient.from_bearer(env_server, env_org, env_token)
                    ok, msg = client.test_connection()
                if ok:
                    existing = next(
                        (j for j, e in enumerate(st.session_state.environments)
                         if e["org"] == env_org and e["server"] == env_server), None
                    )
                    entry = {
                        "name":      env_name,
                        "server":    env_server,
                        "org":       env_org,
                        "auth_type": "basic" if use_basic else "bearer",
                        "username":  env_user,
                        "password":  env_pass,
                        "token":     env_token,
                        "connected": True,
                    }
                    if existing is not None:
                        st.session_state.environments[existing] = entry
                    else:
                        st.session_state.environments.append(entry)
                    st.session_state.api_config = entry
                    for k in ("_new_env_name", "_new_env_server", "_new_env_org"):
                        st.session_state.pop(k, None)
                    st.success(f"✅ Connected to **{env_org}** — environment '{env_name}' added.")
                    st.rerun()
                else:
                    st.error(f"Connection failed: {msg}")
            else:
                st.warning("All fields are required.")

    if not st.session_state.environments:
        st.info("🟡 No environments configured — running in **demo mode** with mock data.")

st.markdown("---")

# ── KPI Row ───────────────────────────────────────────────────────────────────
costs = compute_monthly_costs(
    CURRENT_MONTH,
    st.session_state.exec_data,
    st.session_state.snaplexes,
    st.session_state.bus,
    st.session_state.overhead,
    user_mappings=st.session_state.get("user_mappings"),
)

total_cost      = sum(c["total"]          for c in costs.values())
total_overhead  = sum(c["overhead_share"] for c in costs.values())
total_exec      = total_executions_for_month(CURRENT_MONTH, st.session_state.exec_data)
projected       = total_cost / CURRENT_MONTH_PROGRESS if CURRENT_MONTH_PROGRESS > 0 else total_cost
avg_cost_bu     = total_cost / len(st.session_state.bus) if st.session_state.bus else 0
overhead_pct    = total_overhead / total_cost * 100 if total_cost else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Platform Cost (MTD)", f"${total_cost:,.0f}")
k2.metric("🏢 Active Business Units", len(st.session_state.bus))
k3.metric("⚙️ Executions (MTD)", f"{total_exec:,}")
k4.metric("☁️ Platform Overhead", f"${total_overhead:,.0f}",
          delta=f"{overhead_pct:.1f}% of total", delta_color="off")
k5.metric("📊 Avg Cost / BU", f"${avg_cost_bu:,.0f}")

st.markdown("---")

# ── Charts + Table ───────────────────────────────────────────────────────────
left, right = st.columns([5, 4])

with left:
    st.subheader("Cost Share by Business Unit")
    _sorted_costs = sorted(costs.items(), key=lambda x: -x[1]["total"])
    names     = [get_bu_name(bid, st.session_state.bus) for bid, _ in _sorted_costs]
    totals    = [c["total"] for _, c in _sorted_costs]
    color_map = {get_bu_name(bid, st.session_state.bus): BU_COLORS.get(bid, "#888")
                 for bid in costs}
    fig = px.pie(values=totals, names=names, color=names,
                 color_discrete_map=color_map, hole=0.45)
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont_size=11,
        textfont_color="white",
        pull=[0.03] * len(names),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        height=400,
        margin=dict(t=20, b=20, l=20, r=180),
        legend=dict(
            orientation="v",
            x=1.02, y=0.5,
            xanchor="left",
            font=dict(size=11, color="#E8EDF4"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Cost Breakdown by BU")
    rows = []
    for bid, c in sorted(costs.items(), key=lambda x: -x[1]["total"]):
        rows.append({
            "Business Unit": get_bu_name(bid, st.session_state.bus),
            "Dedicated ($)": f"${c['dedicated_snaplex']:,.0f}",
            "Shared ($)":    f"${c['shared_snaplex']:,.0f}",
            "Overhead ($)":  f"${c['overhead_share']:,.0f}",
            "Total ($)":     f"${c['total']:,.0f}",
            "Share":         f"{c['total']/total_cost*100:.1f}%" if total_cost else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Cost Category Breakdown ───────────────────────────────────────────────────
st.subheader("Platform Cost by Category (MTD)")
cat_totals = {
    "Dedicated Snaplex": sum(c["dedicated_snaplex"] for c in costs.values()),
    "Shared Snaplex":    sum(c["shared_snaplex"]    for c in costs.values()),
    "Platform Overhead": sum(c["overhead_share"]    for c in costs.values()),
}
_cc1, _cc2 = st.columns([3, 2])
with _cc1:
    fig2 = px.pie(
        values=list(cat_totals.values()),
        names=list(cat_totals.keys()),
        color=list(cat_totals.keys()),
        color_discrete_map=CATEGORY_COLORS,
        hole=0.52,
    )
    fig2.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=12,
        textfont_color="white",
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    )
    fig2.update_layout(
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

with _cc2:
    for cat, val in cat_totals.items():
        pct = val / sum(cat_totals.values()) * 100 if sum(cat_totals.values()) else 0
        color = CATEGORY_COLORS.get(cat, "#888")
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
  <div style="width:14px;height:14px;border-radius:3px;background:{color};flex-shrink:0;"></div>
  <div>
    <div style="font-size:.8rem;color:#8A9BB5;font-weight:500;">{cat}</div>
    <div style="font-size:1.1rem;font-weight:700;color:#E8EDF4;">${val:,.0f}
      <span style="font-size:.8rem;font-weight:400;color:#8A9BB5;"> {pct:.1f}%</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("---")
st.info("Use the navigation bar at the top to explore: Dashboard · BU Management · Asset Mapping · Cost Configuration · Reports")

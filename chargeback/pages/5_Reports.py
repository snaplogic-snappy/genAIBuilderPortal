"""
Reports — per-BU invoice view, 3-month projections, CSV export, live data refresh.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from mock_data import (
    init_session_state, compute_monthly_costs, get_bu_name,
    total_executions_for_month, active_environments,
    MONTHS, CURRENT_MONTH, CURRENT_MONTH_PROGRESS, BU_COLORS, CATEGORY_COLORS,
)
from api_client import SnapLogicClient
from theme import inject_brand

st.set_page_config(page_title="Reports | Chargeback Console", page_icon="📋", layout="wide",
                   initial_sidebar_state="collapsed")
init_session_state(st)
inject_brand(st, active="Reports")

st.title("📋 Reports & Chargeback Invoices")
st.caption("Generate per-BU invoices, project future costs, export data, or pull live execution data from the platform.")

tab_invoice, tab_projection, tab_export, tab_live = st.tabs(
    ["🧾 BU Invoice", "📈 Projections", "⬇️ Export", "🔄 Live Data Refresh"]
)

# ── Helpers ───────────────────────────────────────────────────────────────────
all_costs = {
    m: compute_monthly_costs(m, st.session_state.exec_data,
                             st.session_state.snaplexes, st.session_state.bus,
                             st.session_state.overhead,
                             user_mappings=st.session_state.get("user_mappings"))
    for m in MONTHS
}

# ── Invoice tab ───────────────────────────────────────────────────────────────
with tab_invoice:
    st.subheader("Per-Business Unit Chargeback Invoice")

    col_sel1, col_sel2 = st.columns(2)
    inv_month = col_sel1.selectbox("Month", MONTHS, index=len(MONTHS) - 1, key="inv_month")
    inv_bu    = col_sel2.selectbox("Business Unit", [b["name"] for b in st.session_state.bus],
                                    key="inv_bu")
    bu_obj  = next(b for b in st.session_state.bus if b["name"] == inv_bu)
    bu_id   = bu_obj["id"]
    c       = all_costs[inv_month].get(bu_id, {})
    total   = c.get("total", 0)

    # Invoice card
    st.markdown(f"""
    <div style="border:1px solid #e5e7eb;border-radius:10px;padding:1.5rem;max-width:680px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <h3 style="margin:0;color:#7C3AED;">SnapLogic Platform Chargeback</h3>
          <p style="margin:0;opacity:.65;font-size:.9rem;">Invoice period: {inv_month}</p>
        </div>
        <div style="text-align:right;">
          <p style="margin:0;font-size:1.8rem;font-weight:700;">${total:,.2f}</p>
          <p style="margin:0;opacity:.65;font-size:.85rem;">Total amount due</p>
        </div>
      </div>
      <hr style="margin:1rem 0;border-color:#e5e7eb;"/>
      <table style="width:100%;font-size:.9rem;border-collapse:collapse;">
        <tr style="background:rgba(124,58,237,0.08);">
          <th style="text-align:left;padding:.4rem .6rem;">Cost Component</th>
          <th style="text-align:right;padding:.4rem .6rem;">Amount (USD)</th>
        </tr>
        <tr><td style="padding:.4rem .6rem;">Dedicated Snaplex</td>
            <td style="text-align:right;padding:.4rem .6rem;">${c.get('dedicated_snaplex',0):,.2f}</td></tr>
        <tr><td style="padding:.4rem .6rem;">Shared Snaplex (usage share)</td>
            <td style="text-align:right;padding:.4rem .6rem;">${c.get('shared_snaplex',0):,.2f}</td></tr>
        <tr style="background:rgba(128,128,128,0.06);">
            <td style="padding:.4rem .6rem;">Platform Overhead allocation</td>
            <td style="text-align:right;padding:.4rem .6rem;">${c.get('overhead_share',0):,.2f}</td></tr>
        <tr style="border-top:2px solid #7C3AED;font-weight:700;">
          <td style="padding:.6rem .6rem;">Total</td>
          <td style="text-align:right;padding:.6rem .6rem;">${total:,.2f}</td>
        </tr>
      </table>
      <hr style="margin:1rem 0;border-color:#e5e7eb;"/>
      <p style="margin:0;font-size:.85rem;opacity:.7;">
        <b>Bill to:</b> {bu_obj['name']} · {bu_obj['cost_center']} · {bu_obj['owner']}<br/>
        <b>Allocation key:</b> {st.session_state.overhead.get('allocation_key','usage_weighted').replace('_',' ').title()} |
        <b>Headcount:</b> {bu_obj['headcount']}
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    # BU execution detail
    exec_detail = st.session_state.exec_data.get(inv_month, {}).get(bu_id, {})
    if exec_detail:
        detail_rows = []
        for slx_id, d in exec_detail.items():
            slx_name = next((s["name"] for s in st.session_state.snaplexes if s["id"] == slx_id), slx_id)
            detail_rows.append({
                "Snaplex":          slx_name,
                "Executions":       d.get("count", 0),
                "Avg Duration (s)": round(d.get("avg_duration_sec", 0), 1),
                "Failures":         d.get("failures", 0),
                "Exec Minutes":     round(d.get("count", 0) * d.get("avg_duration_sec", 0) / 60, 1),
            })
        st.markdown("**Execution detail**")
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

# ── Projection tab ────────────────────────────────────────────────────────────
with tab_projection:
    st.subheader("3-Month Cost Projection")
    st.markdown("Projections use a linear trend fitted to the last 4 months of actuals.")

    proj_bu = st.selectbox("Business Unit (or All)", ["All BUs"] + [b["name"] for b in st.session_state.bus],
                            key="proj_bu")

    def get_series(bu_name):
        if bu_name == "All BUs":
            return [sum(c["total"] for c in all_costs[m].values()) for m in MONTHS]
        bid = next(b["id"] for b in st.session_state.bus if b["name"] == bu_name)
        return [all_costs[m].get(bid, {}).get("total", 0) for m in MONTHS]

    actuals = get_series(proj_bu)

    # Simple linear regression on last 4 months
    x = list(range(len(actuals)))
    x_fit = x[-4:]
    y_fit = actuals[-4:]
    n = len(x_fit)
    mx = sum(x_fit) / n
    my = sum(y_fit) / n
    slope = sum((xi - mx) * (yi - my) for xi, yi in zip(x_fit, y_fit)) / \
            sum((xi - mx) ** 2 for xi in x_fit)
    intercept = my - slope * mx

    proj_months = ["Aug 2026", "Sep 2026", "Oct 2026"]
    proj_x = [len(MONTHS), len(MONTHS) + 1, len(MONTHS) + 2]
    projections = [max(0, slope * xi + intercept) for xi in proj_x]

    all_months_ext = MONTHS + proj_months
    all_values     = actuals + projections
    is_proj        = [False] * len(MONTHS) + [True] * 3

    df_proj = pd.DataFrame({
        "Month":      all_months_ext,
        "Cost":       all_values,
        "Projected":  is_proj,
    })

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=df_proj[~df_proj["Projected"]]["Month"],
        y=df_proj[~df_proj["Projected"]]["Cost"],
        mode="lines+markers", name="Actual",
        line=dict(color="#7C3AED", width=2.5),
        marker=dict(size=7),
    ))
    fig_proj.add_trace(go.Scatter(
        x=df_proj[df_proj["Projected"]]["Month"],
        y=df_proj[df_proj["Projected"]]["Cost"],
        mode="lines+markers", name="Projected",
        line=dict(color="#7C3AED", width=2, dash="dash"),
        marker=dict(size=7, symbol="diamond"),
    ))
    # Confidence band (±15%)
    proj_months_list = df_proj[df_proj["Projected"]]["Month"].tolist()
    fig_proj.add_trace(go.Scatter(
        x=proj_months_list + list(reversed(proj_months_list)),
        y=[v * 1.15 for v in projections] + [v * 0.85 for v in reversed(projections)],
        fill="toself", fillcolor="rgba(124,58,237,0.1)", line=dict(color="rgba(0,0,0,0)"),
        name="±15% confidence",
    ))
    fig_proj.update_layout(
        height=380, xaxis_title="", yaxis_title="USD", yaxis_tickformat="$,.0f",
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("**Projected values**")
    proj_rows = [{"Month": m, "Projected Cost": f"${v:,.0f}",
                  "Low (−15%)": f"${v*.85:,.0f}", "High (+15%)": f"${v*1.15:,.0f}"}
                 for m, v in zip(proj_months, projections)]
    st.table(pd.DataFrame(proj_rows))
    st.caption("⚠️ Projections are indicative only. Adjust cost config to model scenario changes.")

# ── Export tab ────────────────────────────────────────────────────────────────
with tab_export:
    st.subheader("Export Chargeback Data")

    exp_month = st.selectbox("Month to export", MONTHS + ["All months"], key="exp_month")

    def build_export_df(month_filter):
        rows = []
        months_to_export = MONTHS if month_filter == "All months" else [month_filter]
        for m in months_to_export:
            mc = all_costs[m]
            for bid, c in mc.items():
                bu = next((b for b in st.session_state.bus if b["id"] == bid), {})
                execs = sum(d.get("count", 0)
                            for d in st.session_state.exec_data.get(m, {}).get(bid, {}).values())
                rows.append({
                    "Month":             m,
                    "BU ID":             bid,
                    "Business Unit":     get_bu_name(bid, st.session_state.bus),
                    "Cost Centre":       bu.get("cost_center", ""),
                    "Owner":             bu.get("owner", ""),
                    "Dedicated ($)":     round(c["dedicated_snaplex"], 2),
                    "Shared ($)":        round(c["shared_snaplex"],   2),
                    "Overhead ($)":      round(c["overhead_share"],   2),
                    "Total ($)":         round(c["total"],           2),
                    "Executions":        execs,
                    "Allocation Key":    st.session_state.overhead.get("allocation_key", ""),
                })
        return pd.DataFrame(rows)

    df_export = build_export_df(exp_month)
    st.dataframe(df_export, use_container_width=True, hide_index=True)

    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name=f"snaplogic_chargeback_{exp_month.replace(' ', '_')}.csv",
        mime="text/csv",
        type="primary",
    )

    # SAP/Oracle format hint
    st.markdown("---")
    st.info("""
💡 **Finance system integration tip**: The exported CSV includes Cost Centre codes that can be
used to post journal entries directly in SAP (FB50), Oracle (GLJOURNAL), or Workday (Journal Entry API).
Map the *Total ($)* column to your GL account for 'IT Platform Services'.
    """)

# ── Live Data Refresh tab ─────────────────────────────────────────────────────
with tab_live:
    import calendar as _cal
    from snowflake_client import trigger_adhoc_ingest as _trigger_adhoc

    st.subheader("Trigger Execution Data Ingest")
    st.markdown(
        "Fires the **SL_Chargeback_Adhoc_Ingest** pipeline task with the first and last "
        "day of the selected month. The pipeline fetches execution data from the SnapLogic "
        "runtime API and loads it into Snowflake. Pagination (1 000 records/page) is handled "
        "by the pipeline."
    )

    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    _configured = bool(os.getenv("SL_ADHOC_BEARER") and os.getenv("SL_ADHOC_ENDPOINT"))
    if not _configured:
        st.warning(
            "Pipeline trigger not configured. Set **`SL_ADHOC_BEARER`** and "
            "**`SL_ADHOC_ENDPOINT`** environment variables (or in `.env`) to enable this tab."
        )

    lc1, lc2 = st.columns(2)
    _live_year  = lc1.number_input("Year",  value=2026, min_value=2020, max_value=2035, step=1,
                                    key="live_year")
    _live_month = lc2.selectbox("Month", list(range(1, 13)),
                                 format_func=lambda m: MONTH_NAMES[m - 1],
                                 index=6, key="live_month")

    _year_int  = int(_live_year)
    _month_int = int(_live_month)
    _last_day  = _cal.monthrange(_year_int, _month_int)[1]
    _start_dt  = f"{_year_int}-{_month_int:02d}-01"
    _end_dt    = f"{_year_int}-{_month_int:02d}-{_last_day:02d}"
    _period_lbl = f"{MONTH_NAMES[_month_int - 1]} {_year_int}"

    st.info(f"**Date range:** {_start_dt} → {_end_dt}  ·  will be passed as `start_date` / `end_date` to the pipeline task.")

    if st.button("▶ Trigger Ingest Pipeline", type="primary", disabled=not _configured):
        with st.spinner(f"Triggering SL_Chargeback_Adhoc_Ingest for {_period_lbl}…"):
            try:
                _result = _trigger_adhoc(_start_dt, _end_dt)
                st.success(f"✅ Ingest triggered for **{_period_lbl}** ({_start_dt} → {_end_dt}).")
                st.caption("The pipeline runs asynchronously on the Snaplex. Reload the page in a few minutes to see updated data.")
                with st.expander("Pipeline response", expanded=False):
                    st.json(_result)
            except Exception as _ex:
                st.error(f"Trigger failed: {_ex}")
                st.info("Check that `SL_ADHOC_BEARER` is valid and `SL_ADHOC_ENDPOINT` points to the correct task URL.")

        # ── Apply fetched data to model ───────────────────────────────────────
        if "_live_exec_df" in st.session_state:
            df_cached    = st.session_state["_live_exec_df"]
            period_label = st.session_state.get("_live_exec_period", "")
            cached_env   = st.session_state.get("_live_exec_env", {})

            st.markdown("---")
            st.subheader(f"Apply Live Data — {period_label} ({cached_env.get('org','')})")
            st.markdown(
                "Attribute fetched executions to BUs via project-path rules, then apply "
                "to the chargeback model for this period."
            )

            # runtime_path_id → internal snaplex id mapping (editable)
            st.markdown("**Runtime path → Snaplex mapping** (edit if needed before applying)")
            rt_ids = df_cached["runtime_path_id"].dropna().unique().tolist() if "runtime_path_id" in df_cached.columns else []
            rt_map = {}
            if rt_ids:
                mc = st.columns(2)
                for j, rt_id in enumerate(rt_ids):
                    slx_names = ["(unmapped)"] + [s["name"] for s in st.session_state.snaplexes]
                    # Try auto-match on runtime_path_id field in our model
                    default_slx = next(
                        (s["name"] for s in st.session_state.snaplexes
                         if s.get("snode_id") == rt_id or rt_id.endswith(s["id"].replace("slx_", ""))),
                        "(unmapped)"
                    )
                    default_idx = slx_names.index(default_slx) if default_slx in slx_names else 0
                    sel = mc[j % 2].selectbox(
                        rt_id, slx_names, index=default_idx, key=f"rt_map_{j}"
                    )
                    if sel != "(unmapped)":
                        slx_id = next(s["id"] for s in st.session_state.snaplexes if s["name"] == sel)
                        rt_map[rt_id] = slx_id

            if st.button("🔀 Apply to Chargeback Model", type="primary"):
                with st.spinner("Attributing executions to BUs and computing Snaplex metrics…"):
                    try:
                        import calendar
                        from datetime import datetime as _dt

                        client = SnapLogicClient.from_env(cached_env)

                        # ── BU attribution ──────────────────────────────────
                        agg = client.aggregate_by_snaplex_and_bu(
                            df_cached,
                            st.session_state.project_mappings,
                            rt_map,
                            user_mappings=st.session_state.get("user_mappings", []),
                        )
                        if agg:
                            st.session_state.exec_data[period_label] = agg

                        # ── Snaplex metrics via Little's Law ─────────────────
                        # period = days in the selected month × 86 400 s
                        try:
                            yr, mo = int(period_label.split()[-1]), \
                                     list(calendar.month_abbr).index(period_label.split()[0])
                            days_in_month = calendar.monthrange(yr, mo)[1]
                            period_secs   = days_in_month * 24 * 3600
                        except Exception:
                            period_secs = 30 * 24 * 3600  # fallback

                        slx_metrics = SnapLogicClient.compute_snaplex_metrics(
                            df_cached, period_secs
                        )

                        # Write avg_active_pipelines back onto each Snaplex
                        # matched by runtime_path_id (snode_id field)
                        updated_slx = 0
                        for i, slx in enumerate(st.session_state.snaplexes):
                            rt_id = slx.get("snode_id", "")
                            m = slx_metrics.get(rt_id)
                            if m:
                                st.session_state.snaplexes[i]["avg_active_pipelines"] = \
                                    round(m["avg_active_pipelines"], 3)
                                updated_slx += 1

                        if agg:
                            n_bus   = len(agg)
                            n_execs = sum(v.get("count", 0) for bv in agg.values() for v in bv.values())
                            st.success(
                                f"✅ Applied **{n_execs:,} executions** across **{n_bus} BUs** "
                                f"for {period_label}. "
                                f"Updated avg_active_pipelines on **{updated_slx} Snaplexes**. "
                                f"Head to the Dashboard to see updated utilisation."
                            )
                        else:
                            st.warning(
                                "No executions could be attributed to any BU. "
                                "Check your **project-path rules** in Asset Mapping — "
                                "the path prefixes must match the `path` column shown above."
                            )
                    except Exception as e:
                        st.error(f"Attribution error: {e}")

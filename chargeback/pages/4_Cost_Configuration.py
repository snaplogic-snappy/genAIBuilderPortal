"""
Cost Configuration — platform overhead, node pricing, allocation key, impact preview.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import pandas as pd

from mock_data import (
    init_session_state, compute_monthly_costs, get_bu_name,
    CURRENT_MONTH, BU_COLORS, NODE_TYPE_COSTS,
)
from theme import inject_brand

st.set_page_config(page_title="Cost Configuration | Chargeback Console", page_icon="⚙️", layout="wide",
                   initial_sidebar_state="collapsed")
init_session_state(st)
inject_brand(st, active="Cost Config")

st.title("⚙️ Cost Configuration")
st.caption("Configure platform overhead costs, Snaplex node pricing, and the overhead allocation key.")

tab_overhead, tab_snaplexes, tab_alloc, tab_preview = st.tabs(
    ["💸 Platform Overhead", "🖥️ Snaplex Pricing", "🔑 Allocation Key", "👁️ Impact Preview"]
)

# ── Platform Overhead ─────────────────────────────────────────────────────────
with tab_overhead:
    st.subheader("Platform Overhead Costs (Monthly)")
    st.markdown("""
    These costs are **not tied to a specific Snaplex**. They are distributed across all BUs
    using the allocation key configured on the **Allocation Key** tab.
    """)

    oh = st.session_state.overhead

    with st.form("overhead_form"):
        oc1, oc2, oc3 = st.columns(3)
        new_license  = oc1.number_input("SnapLogic License ($)",
                                        value=oh["license"], step=100, min_value=0,
                                        help="Monthly platform licence fee")
        new_coe_opex = oc2.number_input("COE Operating Cost ($)",
                                        value=oh["coe_opex"], step=500, min_value=0,
                                        help="Integration CoE team: salaries, tooling, training")
        new_infra    = oc3.number_input("Cloud Infrastructure ($)",
                                        value=oh["cloud_infra"], step=100, min_value=0,
                                        help="Non-Snaplex infra: VPN, storage, monitoring, etc.")

        total_oh = new_license + new_coe_opex + new_infra
        st.info(f"**Total monthly platform overhead: ${total_oh:,.0f}**")

        st.markdown("##### Optional overhead line items")
        st.caption("These are informational labels — add them to COE Operating Cost above.")
        extra_rows = [
            ("Security & Compliance tooling", 800),
            ("Training & Enablement", 1200),
            ("Support contract",      1500),
        ]
        for label, example in extra_rows:
            st.caption(f"• {label} — example: ${example:,}/month")

        if st.form_submit_button("💾 Save Overhead Configuration"):
            st.session_state.overhead["license"]    = int(new_license)
            st.session_state.overhead["coe_opex"]   = int(new_coe_opex)
            st.session_state.overhead["cloud_infra"] = int(new_infra)
            st.success(f"✅ Overhead saved — total: ${total_oh:,.0f}/month")

# ── Snaplex Pricing ───────────────────────────────────────────────────────────
with tab_snaplexes:
    st.subheader("Snaplex Node Pricing")
    st.markdown("Edit monthly cost per node for each Snaplex. Cloudplex capacity is billed per node and allocated by usage.")

    for i, slx in enumerate(st.session_state.snaplexes):
        with st.expander(f"**{slx['name']}** — {slx['type'].capitalize()} · {slx.get('env', '')}"):
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Type", slx["type"].capitalize())
            sc2.metric("Environment", slx.get("env", "—"))
            sc3.metric("Nodes", slx.get("nodes", "N/A"))
            current_monthly = (slx.get("nodes") or 0) * (slx.get("node_cost_monthly") or 0)
            sc4.metric("Current Monthly Cost",
                       f"${current_monthly:,.0f}" if current_monthly else "per-exec")

            with st.form(f"slx_price_form_{i}"):
                fp1, fp2, fp3 = st.columns(3)
                new_nodes = fp1.number_input("Nodes", min_value=0, step=1,
                                              value=slx.get("nodes") or 1, key=f"snodes_{i}")
                _ntype_opts = list(NODE_TYPE_COSTS.keys())
                _saved_ntype = slx.get("node_type", _ntype_opts[0])
                _ntype_idx = _ntype_opts.index(_saved_ntype) if _saved_ntype in _ntype_opts else 0
                new_node_type = fp2.selectbox("Node Type", _ntype_opts, index=_ntype_idx,
                                               key=f"sntype_{i}",
                                               help="M Standard=$2,200 · L Large=$4,000 · Cloudplex=$1,800 · Memory-Opt=Custom")
                _preset = NODE_TYPE_COSTS.get(new_node_type) or slx.get("node_cost_monthly") or 1200
                new_ncost = fp3.number_input("Cost per node/month ($)", min_value=0, step=50,
                                              value=int(_preset), key=f"sncost_{i}",
                                              help="Auto-filled from Node Type — override if your contract differs.")
                new_total = int(new_nodes) * int(new_ncost)
                st.caption(f"Total monthly: **${new_total:,.0f}**")

                if st.form_submit_button(f"💾 Save {slx['name']}"):
                    st.session_state.snaplexes[i]["nodes"]             = int(new_nodes)
                    st.session_state.snaplexes[i]["node_type"]         = new_node_type
                    st.session_state.snaplexes[i]["node_cost_monthly"] = int(new_ncost)
                    st.success("✅ Saved.")
                    st.rerun()

    # Platform cost summary
    total_groundplex = sum(
        (s.get("nodes") or 0) * (s.get("node_cost_monthly") or 0)
        for s in st.session_state.snaplexes
        if s.get("env") == "Production"
    )
    st.markdown("---")
    st.metric("Total Production Snaplex capacity cost", f"${total_groundplex:,.0f}/month")

# ── Allocation Key ────────────────────────────────────────────────────────────
with tab_alloc:
    st.subheader("Platform Overhead Allocation Key")
    st.markdown("""
    The allocation key determines how **platform overhead** (license + COE + infrastructure) is
    split across business units. Choose the method that best reflects your internal chargeback policy.
    """)

    st.markdown("""
    **Execution duration cap** — always-on listener pipelines (Slack agents, background
    processors) can run for hours or days, skewing cost allocation. Cap each execution's
    counted duration to prevent them from dominating. 60 min is the recommended default.
    """)
    cap_options = {900: "15 min", 1800: "30 min", 3600: "60 min (recommended)", 7200: "2 h", 86400: "24 h (uncapped)"}
    cap_sec = st.select_slider(
        "Per-execution duration cap",
        options=list(cap_options.keys()),
        format_func=lambda v: cap_options[v],
        value=st.session_state.overhead.get("duration_cap_sec", 3600),
    )

    st.markdown("---")
    st.markdown("""
    **Execution startup overhead** — each pipeline execution carries a baseline overhead
    (slot reservation, JVM warmup, connection setup). This adds N seconds to each execution's
    effective duration when computing BU cost shares.
    At 0 s = pure runtime weighting; higher values give more weight to execution count.
    """)
    startup_sec = st.number_input(
        "Execution startup overhead (seconds)",
        min_value=0,
        max_value=120,
        step=5,
        value=st.session_state.overhead.get("startup_overhead_sec", 10),
    )

    st.markdown("---")
    current_key = st.session_state.overhead.get("allocation_key", "blended")
    key_options = {
        "headcount":      "👤 Headcount-Weighted (proportional to mapped users) — Recommended",
        "blended":        "⚖️ Blended (configurable Headcount + Usage split)",
        "usage_weighted": "📈 Usage-Weighted (by pipeline execution minutes)",
        "equal":          "➗ Equal Split (each BU pays an equal share)",
    }
    _key_list = list(key_options.keys())
    selected_key = st.radio(
        "Allocation method",
        _key_list,
        format_func=lambda k: key_options[k],
        index=_key_list.index(current_key) if current_key in _key_list else 0,
    )

    # Blended ratio slider — only shown when Blended is selected
    blended_hc_pct = st.session_state.overhead.get("blended_headcount_pct", 50)
    if selected_key == "blended":
        st.markdown("##### Blended ratio")
        blended_hc_pct = st.slider(
            "Headcount weight (%)",
            min_value=0, max_value=100, step=5,
            value=int(blended_hc_pct),
            help="Remaining % goes to Usage-Weighted. 100% = pure headcount, 0% = pure usage.",
            format="%d%%",
        )
        _vol_pct = 100 - blended_hc_pct
        st.caption(
            f"**{blended_hc_pct}% Headcount** (mapped user count) "
            f"+ **{_vol_pct}% Usage** (execution minutes)"
        )

    st.markdown("---")
    descriptions = {
        "blended": f"""
**Blended** splits platform overhead using your configured ratio:
- **{blended_hc_pct}%** allocated proportional to each BU's mapped user count
- **{100 - blended_hc_pct}%** allocated proportional to pipeline execution minutes

✅ **Tunable**: slide toward headcount for stable, predictable charges; toward usage when you want heavy consumers to pay more
⚠️ **Caveat**: BUs with very high execution volume (many short runs) can dominate the usage component
        """,
        "usage_weighted": """
**Usage-Weighted** distributes overhead in proportion to each BU's share of total pipeline
execution minutes across all Snaplexes. BUs that run more workloads pay more overhead.

✅ **Fair**: heavy users pay more
⚠️ **Caveat**: penalises BUs running many short jobs vs. fewer long jobs
        """,
        "equal": """
**Equal Split** divides overhead evenly across all business units regardless of usage.

✅ **Simple** and easy to explain
⚠️ **Caveat**: small BUs subsidise large ones if usage is very unequal
        """,
        "headcount": """
**Headcount-Weighted** allocates overhead proportional to each BU's user count,
derived automatically from the **User Mappings** on the Asset Mapping tab.
Platform costs like license fees and COE salaries correlate to team size, not throughput.

✅ **Balanced**: prevents high-volume BUs (many short pipeline runs) from dominating
✅ **Self-maintaining**: user count updates automatically when you remap users
✅ **Explainable**: each BU's share is simply their proportion of total mapped users
        """,
    }
    st.markdown(descriptions[selected_key])

    if st.button("💾 Save Allocation Key"):
        st.session_state.overhead["allocation_key"]        = selected_key
        st.session_state.overhead["blended_headcount_pct"] = blended_hc_pct
        st.session_state.overhead["startup_overhead_sec"]  = startup_sec
        st.session_state.overhead["duration_cap_sec"]      = cap_sec
        _blend_info = (f", blend: **{blended_hc_pct}% HC / {100-blended_hc_pct}% usage**"
                       if selected_key == "blended" else "")
        st.success(
            f"✅ Saved — key: **{key_options[selected_key]}**"
            f"{_blend_info}, cap: **{cap_options[cap_sec]}**"
        )

# ── Impact Preview ────────────────────────────────────────────────────────────
with tab_preview:
    st.subheader("Allocation Key Impact Preview")
    st.markdown("Compare how overhead allocation methods affect each BU's monthly charge.")

    costs_by_key = {}
    for key in ["blended", "usage_weighted", "equal", "headcount"]:
        oh_copy = {**st.session_state.overhead, "allocation_key": key}
        c = compute_monthly_costs(CURRENT_MONTH, st.session_state.exec_data,
                                  st.session_state.snaplexes, st.session_state.bus, oh_copy,
                                  user_mappings=st.session_state.get("user_mappings"))
        costs_by_key[key] = c

    _hc_pct  = st.session_state.overhead.get("blended_headcount_pct", 50)
    _vol_pct = 100 - _hc_pct
    labels = {
        "blended":        f"Blended ({_hc_pct}% HC / {_vol_pct}% Usage)",
        "usage_weighted": "Usage-Weighted",
        "equal":          "Equal Split",
        "headcount":      "Headcount",
    }

    rows = []
    for bid in [b["id"] for b in st.session_state.bus]:
        row = {"Business Unit": get_bu_name(bid, st.session_state.bus)}
        for key, label in labels.items():
            row[label] = round(costs_by_key[key][bid]["overhead_share"], 2)
        _cur_key = st.session_state.overhead.get("allocation_key", "blended")
        row["Current (Total)"] = round(costs_by_key[_cur_key][bid]["total"], 2)
        rows.append(row)

    df_preview = pd.DataFrame(rows)
    st.dataframe(
        df_preview.style
            .format({k: "${:,.2f}" for k in list(labels.values()) + ["Current (Total)"]}),
        use_container_width=True,
        hide_index=True,
    )

    fig_compare = px.bar(
        df_preview.melt(id_vars="Business Unit", value_vars=list(labels.values()),
                        var_name="Allocation Key", value_name="Overhead ($)"),
        x="Business Unit", y="Overhead ($)", color="Allocation Key",
        barmode="group", height=360,
        color_discrete_map={
            labels["blended"]:        "#F59E0B",
            labels["usage_weighted"]: "#7C3AED",
            labels["equal"]:          "#3B82F6",
            labels["headcount"]:      "#10B981",
        },
    )
    fig_compare.update_layout(xaxis_title="", yaxis_tickformat="$,.0f",
                               margin=dict(t=10, b=10))
    st.plotly_chart(fig_compare, use_container_width=True)

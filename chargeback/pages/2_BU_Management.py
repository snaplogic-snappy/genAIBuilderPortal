"""
Business Unit Management — define BUs, cost centres, owners.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from mock_data import (
    init_session_state, compute_monthly_costs, get_bu_name,
    CURRENT_MONTH, BU_COLORS,
)
from theme import inject_brand

st.set_page_config(page_title="BU Management | Chargeback Console", page_icon="🏢", layout="wide",
                   initial_sidebar_state="collapsed")
init_session_state(st)
inject_brand(st, active="BU Management")

st.title("🏢 Business Unit Management")
st.caption("Define business units, cost centres, and owners. User counts are derived from mapped users.")

# ── Build user → BU lookup ────────────────────────────────────────────────────
_bu_users: dict = {}
_platform_users = {u["email"].lower(): u.get("name", u["email"])
                   for u in st.session_state.get("_platform_users", [])}
for _m in st.session_state.get("user_mappings", []):
    _em = _m["username"].lower()
    _bu_users.setdefault(_m["bu_id"], []).append({
        "email": _em,
        "name":  _platform_users.get(_em, _m["username"]),
    })

# ── Costs ─────────────────────────────────────────────────────────────────────
costs = compute_monthly_costs(
    CURRENT_MONTH, st.session_state.exec_data,
    st.session_state.snaplexes, st.session_state.bus, st.session_state.overhead,
    user_mappings=st.session_state.get("user_mappings"),
)

# ── Summary cards ─────────────────────────────────────────────────────────────
cols = st.columns(min(len(st.session_state.bus), 4))
for i, bu in enumerate(st.session_state.bus[:4]):
    c = costs.get(bu["id"], {})
    with cols[i]:
        color = BU_COLORS.get(bu["id"], "#7C3AED")
        st.markdown(f"""
        <div style="border-left:4px solid {color};padding:.6rem 1rem;
                    border-radius:6px;background:rgba(128,128,128,0.08);margin-bottom:.5rem;">
          <b>{bu['name']}</b><br/>
          <small>{bu['cost_center']} · {bu['owner']}</small><br/>
          <span style="font-size:1.2rem;font-weight:700;">${c.get('total',0):,.0f}</span>
          <small> / month</small>
        </div>
        """, unsafe_allow_html=True)

if len(st.session_state.bus) > 4:
    cols2 = st.columns(len(st.session_state.bus) - 4)
    for i, bu in enumerate(st.session_state.bus[4:]):
        c = costs.get(bu["id"], {})
        with cols2[i]:
            color = BU_COLORS.get(bu["id"], "#7C3AED")
            st.markdown(f"""
            <div style="border-left:4px solid {color};padding:.6rem 1rem;
                        border-radius:6px;background:rgba(128,128,128,0.08);margin-bottom:.5rem;">
              <b>{bu['name']}</b><br/>
              <small>{bu['cost_center']} · {bu['owner']}</small><br/>
              <span style="font-size:1.2rem;font-weight:700;">${c.get('total',0):,.0f}</span>
              <small> / month</small>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ── BU Table ──────────────────────────────────────────────────────────────────
st.subheader("All Business Units")

rows = []
for bu in st.session_state.bus:
    c = costs.get(bu["id"], {})
    rows.append({
        "Name":         bu["name"],
        "Cost Centre":  bu["cost_center"],
        "Owner":        bu["owner"],
        "Users":        len(_bu_users.get(bu["id"], [])),
        "MTD Cost ($)": round(c.get("total", 0), 0),
    })
st.dataframe(
    pd.DataFrame(rows).style.format({"MTD Cost ($)": "${:,.0f}"}),
    use_container_width=True,
    hide_index=True,
)

# ── Per-BU user roster ────────────────────────────────────────────────────────
st.subheader("User Roster by BU")
for bu in st.session_state.bus:
    _users = sorted(_bu_users.get(bu["id"], []), key=lambda u: u["name"].lower())
    _label = f"**{bu['name']}** — {len(_users)} user{'s' if len(_users) != 1 else ''}"
    with st.expander(_label, expanded=False):
        if not _users:
            st.caption("No users assigned. Map users on the **Asset Mapping → User Mappings** tab.")
        else:
            for _u in _users:
                if _u["name"] != _u["email"]:
                    st.markdown(
                        f"👤 {_u['name']} &nbsp;"
                        f"<span style='color:#888;font-size:.85rem'>{_u['email']}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f"👤 {_u['email']}")

# ── Action row ────────────────────────────────────────────────────────────────
st.markdown("---")
ac1, ac2, ac3, ac4 = st.columns([3, 1, 1, 2])

bu_names = [b["name"] for b in st.session_state.bus]
sel_name = ac1.selectbox("Select BU", bu_names, key="bu_action_sel", label_visibility="collapsed")
sel_bu   = next(b for b in st.session_state.bus if b["name"] == sel_name)
sel_idx  = st.session_state.bus.index(sel_bu)

if ac2.button("✏️ Edit", use_container_width=True, key="btn_edit_bu"):
    st.session_state["_bu_mode"] = "edit"

if ac3.button("🗑️ Delete", use_container_width=True, key="btn_del_bu", type="primary"):
    st.session_state["_bu_mode"] = "delete"

if ac4.button("➕ Add New BU", use_container_width=True, key="btn_add_bu"):
    st.session_state["_bu_mode"] = "add"

# ── Edit form ─────────────────────────────────────────────────────────────────
if st.session_state.get("_bu_mode") == "edit":
    st.markdown(f"#### Edit — {sel_bu['name']}")
    with st.form("edit_bu_form"):
        ec1, ec2 = st.columns(2)
        new_name  = ec1.text_input("Name",        value=sel_bu["name"])
        new_cc    = ec2.text_input("Cost Centre", value=sel_bu["cost_center"])
        new_owner = st.text_input("Owner",        value=sel_bu["owner"])
        sb1, sb2  = st.columns(2)
        if sb1.form_submit_button("💾 Save Changes", use_container_width=True):
            st.session_state.bus[sel_idx] = {
                **sel_bu,
                "name":        new_name,
                "cost_center": new_cc,
                "owner":       new_owner,
            }
            st.session_state["_bu_mode"] = None
            st.success(f"✅ '{new_name}' updated.")
            st.rerun()
        if sb2.form_submit_button("✖ Cancel", use_container_width=True):
            st.session_state["_bu_mode"] = None
            st.rerun()

# ── Delete confirmation ───────────────────────────────────────────────────────
elif st.session_state.get("_bu_mode") == "delete":
    st.warning(
        f"Delete **{sel_bu['name']}** ({sel_bu['cost_center']})? "
        "This removes it from all cost calculations."
    )
    dc1, dc2 = st.columns(2)
    if dc1.button("🗑️ Confirm Delete", type="primary", use_container_width=True, key="confirm_del"):
        st.session_state.bus = [b for b in st.session_state.bus if b["id"] != sel_bu["id"]]
        st.session_state["_bu_mode"] = None
        st.success(f"✅ Removed '{sel_bu['name']}'.")
        st.rerun()
    if dc2.button("✖ Cancel", use_container_width=True, key="cancel_del"):
        st.session_state["_bu_mode"] = None
        st.rerun()

# ── Add form ──────────────────────────────────────────────────────────────────
elif st.session_state.get("_bu_mode") == "add":
    st.markdown("#### Add New Business Unit")
    with st.form("add_bu_form"):
        a1, a2 = st.columns(2)
        name  = a1.text_input("BU Name *",     placeholder="e.g. Legal & Compliance")
        cc    = a2.text_input("Cost Centre *", placeholder="e.g. CC-7001")
        owner = st.text_input("Owner",         placeholder="Full name")
        sb1, sb2 = st.columns(2)
        if sb1.form_submit_button("➕ Add Business Unit", use_container_width=True):
            if not name or not cc:
                st.error("Name and Cost Centre are required.")
            else:
                new_id = "bu_" + name.lower().replace(" ", "_").replace("&", "").replace("/", "_")[:12]
                if any(b["id"] == new_id for b in st.session_state.bus):
                    new_id += "_2"
                st.session_state.bus.append({
                    "id":          new_id,
                    "name":        name,
                    "cost_center": cc,
                    "owner":       owner,
                    "headcount":   0,
                })
                st.session_state["_bu_mode"] = None
                st.success(f"✅ '{name}' added.")
                st.rerun()
        if sb2.form_submit_button("✖ Cancel", use_container_width=True):
            st.session_state["_bu_mode"] = None
            st.rerun()

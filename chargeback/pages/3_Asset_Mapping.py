"""
Asset Mapping — Snaplexes → BUs, pipeline ownership, project-path rules.
Also handles importing live Snaplex data when API is connected.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from mock_data import (
    init_session_state, get_bu_name,
    active_environments, NODE_TYPE_COSTS,
    save_user_state,
)
from api_client import SnapLogicClient
from theme import inject_brand

st.set_page_config(page_title="Asset Mapping | Chargeback Console", page_icon="🔌", layout="wide",
                   initial_sidebar_state="collapsed")
init_session_state(st)
inject_brand(st, active="Asset Mapping")

st.title("🔌 Asset Mapping")
st.caption("Map Snaplexes to business units, and configure project-path and user allocation rules.")

tab_slx, tab_projects, tab_users, tab_import = st.tabs(
    ["⚡ Snaplexes", "🗂️ Project Rules", "👤 User Mappings", "☁️ Import from Platform"]
)

# ── Snaplexes tab ─────────────────────────────────────────────────────────────
with tab_slx:
    st.subheader("Snaplex Inventory")
    st.markdown("Define each Snaplex, its type, and which BU owns it (for dedicated) or how costs are shared.")

    bu_options = {b["name"]: b["id"] for b in st.session_state.bus}
    bu_id_to_name = {b["id"]: b["name"] for b in st.session_state.bus}

    slx_rows = []
    for s in st.session_state.snaplexes:
        monthly_cost = (s.get("nodes") or 0) * (s.get("node_cost_monthly") or 0)
        slx_rows.append({
            "ID":           s["id"],
            "Name":         s["name"],
            "Type":         s["type"].capitalize(),
            "Nodes":        s.get("nodes", "—"),
            "Node Cost":    f"${s.get('node_cost_monthly', 0):,}/mo" if s.get("node_cost_monthly") else "—",
            "Monthly Cost": f"${monthly_cost:,.0f}" if monthly_cost else "—",
            "Owner BU":     bu_id_to_name.get(s.get("bu_id", ""), "Shared"),
            "Environment":  s.get("env", ""),
            "Region":       s.get("region", ""),
        })
    st.dataframe(pd.DataFrame(slx_rows), use_container_width=True, hide_index=True)

    st.markdown("**Edit Snaplex Assignment**")
    slx_names = [s["name"] for s in st.session_state.snaplexes]
    sel_slx_name = st.selectbox("Select Snaplex", slx_names, key="slx_sel")
    sel_slx = next(s for s in st.session_state.snaplexes if s["name"] == sel_slx_name)
    idx_slx = st.session_state.snaplexes.index(sel_slx)

    with st.form("edit_slx_form"):
        fc1, fc2, fc3 = st.columns(3)
        new_type = fc1.selectbox(
            "Type", ["dedicated", "shared", "cloudplex"],
            index=["dedicated", "shared", "cloudplex"].index(sel_slx["type"])
            if sel_slx["type"] in ["dedicated", "shared", "cloudplex"] else 1,
        )
        new_nodes = fc2.number_input("Nodes", min_value=0, step=1,
                                     value=sel_slx.get("nodes") or 0)
        new_node_cost = fc3.number_input("Node cost/month ($)", min_value=0, step=100,
                                          value=sel_slx.get("node_cost_monthly") or 0)

        fc4, fc5 = st.columns(2)
        bu_choices  = ["(Shared)"] + list(bu_options.keys())
        current_bu  = bu_id_to_name.get(sel_slx.get("bu_id", ""), "(Shared)")
        default_idx = bu_choices.index(current_bu) if current_bu in bu_choices else 0
        new_bu_name = fc4.selectbox("Owner BU", bu_choices, index=default_idx)
        new_env     = fc5.selectbox("Environment", ["Production", "Non-Production"],
                                    index=0 if sel_slx.get("env") == "Production" else 1)
        if st.form_submit_button("💾 Save"):
            new_bu_id = bu_options.get(new_bu_name) if new_bu_name != "(Shared)" else None
            st.session_state.snaplexes[idx_slx] = {
                **sel_slx,
                "type":             new_type,
                "nodes":            int(new_nodes) if new_nodes else None,
                "node_cost_monthly": int(new_node_cost) if new_node_cost else None,
                "bu_id":            new_bu_id,
                "env":              new_env,
            }
            st.success("✅ Snaplex updated.")
            st.rerun()

    st.markdown("**Add New Snaplex**")
    with st.form("add_slx_form"):
        na1, na2 = st.columns(2)
        new_name  = na1.text_input("Snaplex Name")
        new_snode = na2.text_input("Snode ID (from platform)", placeholder="e.g. 64ee0f97...")
        na3, na4, na5 = st.columns(3)
        add_type  = na3.selectbox("Type", ["dedicated", "shared", "cloudplex"])
        add_nodes = na4.number_input("Nodes", min_value=0, step=1, value=2)
        add_ncost = na5.number_input("Node cost/month ($)", min_value=0, step=100, value=1200)
        na6, na7  = st.columns(2)
        add_bu    = na6.selectbox("Owner BU", ["(Shared)"] + list(bu_options.keys()))
        add_env   = na7.selectbox("Environment", ["Production", "Non-Production"])
        if st.form_submit_button("➕ Add Snaplex"):
            if new_name:
                new_id = "slx_" + new_name.lower().replace(" ", "_")[:12]
                st.session_state.snaplexes.append({
                    "id":               new_id,
                    "name":             new_name,
                    "type":             add_type,
                    "bu_id":            bu_options.get(add_bu) if add_bu != "(Shared)" else None,
                    "nodes":            int(add_nodes) if add_nodes else None,
                    "node_cost_monthly": int(add_ncost) if add_ncost else None,
                    "region":           "eu-central-1",
                    "env":              add_env,
                    "snode_id":         new_snode,
                })
                st.success(f"✅ Snaplex '{new_name}' added.")
                st.rerun()

# ── Project Allocation tree tab ───────────────────────────────────────────────
with tab_projects:
    st.subheader("Project Allocation")
    st.caption(
        "Assign project spaces (and individual projects within them) to Business Units. "
        "A space-level assignment covers all projects inside it. "
        "Project-level assignments override the parent space rule."
    )

    # ── Build project tree ────────────────────────────────────────────────────
    _ORG = "ConnectFasterInc"
    _tree: dict[str, set] = {}   # {space: {project_name, ...}}

    # Seed from live exec data
    if "_live_exec_df" in st.session_state:
        for _p in st.session_state["_live_exec_df"]["path"].dropna().unique():
            _parts = str(_p).strip("/").split("/")
            if len(_parts) >= 2:
                _sp = _parts[1]
                _tree.setdefault(_sp, set())
                if len(_parts) >= 3:
                    _tree[_sp].add(_parts[2])

    # Ensure every already-mapped space/project is represented in the tree
    for _m in st.session_state.project_mappings:
        _pp = _m["project_path"].strip("/").split("/")
        if len(_pp) >= 2:
            _sp = _pp[1]
            _tree.setdefault(_sp, set())
            if len(_pp) >= 3:
                _tree[_sp].add(_pp[2])

    # ── Optional: enrich tree from platform API ───────────────────────────────
    _envs = active_environments(st)
    _api_col, _api_info = st.columns([2, 4])
    if _envs:
        if _api_col.button("☁️ Fetch all projects from Platform API", key="fetch_projects_api"):
            try:
                _client = SnapLogicClient.from_env(_envs[0])
                _api_projs = _client.list_projects()
                for _ap in _api_projs:
                    _sp, _pr = _ap["space"], _ap["project"]
                    _tree.setdefault(_sp, set()).add(_pr)
                st.session_state["_api_projects_loaded"] = True
                st.rerun()
            except Exception as _api_e:
                st.error(f"Platform API error: {_api_e}")
        if st.session_state.get("_api_projects_loaded"):
            _api_info.caption("✅ Project list enriched from platform API — includes projects with no execution history.")

    _spaces = sorted(_tree.keys())

    # ── Lookup helpers ────────────────────────────────────────────────────────
    from mock_data import BU_COLORS as _BUC
    _pm_dict = {_m["project_path"].rstrip("/"): _m["bu_id"]
                for _m in st.session_state.project_mappings}
    _bu_name  = {b["id"]: b["name"]  for b in st.session_state.bus}
    _bu_color = {b["id"]: _BUC.get(b["id"], "#666") for b in st.session_state.bus}
    _bu_by_name = {b["name"]: b["id"] for b in st.session_state.bus}
    _bu_list  = [b["name"] for b in st.session_state.bus]

    def _badge(bu_id):
        if not bu_id:
            return "<span style='color:#888;font-size:.8rem'>— unassigned —</span>"
        c = _bu_color.get(bu_id, "#888")
        n = _bu_name.get(bu_id, bu_id)
        return (f"<span style='background:{c};color:#fff;padding:2px 8px;"
                f"border-radius:10px;font-size:.78rem;font-weight:600'>{n}</span>")

    def _assign(path, bu_id):
        filtered = [m for m in st.session_state.project_mappings
                    if m["project_path"].rstrip("/") != path.rstrip("/")]
        if bu_id:
            filtered.append({"project_path": path, "bu_id": bu_id})
        st.session_state.project_mappings = filtered
        st.rerun()

    # ── BU selector (fixed sidebar-like column) ───────────────────────────────
    _tcol, _bcol = st.columns([3, 1])

    with _bcol:
        st.markdown("**Assign selection to:**")
        _sel_bu_name = st.radio("BU", _bu_list, label_visibility="collapsed",
                                key="pm_tree_bu_sel")
        _sel_bu_id   = _bu_by_name[_sel_bu_name]
        _sel_color   = _bu_color.get(_sel_bu_id, "#888")
        st.markdown(
            f"<div style='background:{_sel_color};color:#fff;padding:6px 10px;"
            f"border-radius:8px;text-align:center;font-weight:600;margin-top:4px'>"
            f"{_sel_bu_name}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.caption(
            "Click **Assign space** to map the whole project space, "
            "or expand to assign individual projects."
        )

    # ── Tree ──────────────────────────────────────────────────────────────────
    with _tcol:
        for _sp in _spaces:
            _sp_path    = f"/{_ORG}/{_sp}"
            _sp_bu      = _pm_dict.get(_sp_path)
            _projs      = sorted(_tree.get(_sp, []))
            # Count how many individual projects have overrides
            _proj_overrides = sum(
                1 for _pr in _projs
                if _pm_dict.get(f"/{_ORG}/{_sp}/{_pr}") and
                   _pm_dict.get(f"/{_ORG}/{_sp}/{_pr}") != _sp_bu
            )
            _detail = f"  ·  {len(_projs)} projects"
            if _proj_overrides:
                _detail += f"  ·  {_proj_overrides} overrides"

            with st.expander(
                f"📁 **{_sp}**{_detail}",
                expanded=(_sp_bu == _sel_bu_id),
            ):
                # Space-level badge + assign/clear buttons
                _hc1, _hc2, _hc3 = st.columns([3, 1, 1])
                _hc1.markdown(_badge(_sp_bu), unsafe_allow_html=True)
                if _hc2.button("Assign space", key=f"sp_assign_{_sp}", use_container_width=True):
                    _assign(_sp_path, _sel_bu_id)
                if _sp_bu and _hc3.button("Clear", key=f"sp_clear_{_sp}", use_container_width=True):
                    _assign(_sp_path, None)

                # Individual projects
                if _projs:
                    st.markdown(
                        "<div style='height:1px;background:rgba(255,255,255,.08);"
                        "margin:8px 0'></div>",
                        unsafe_allow_html=True,
                    )
                    for _pri, _pr in enumerate(_projs):
                        _pr_path = f"/{_ORG}/{_sp}/{_pr}"
                        _pr_bu   = _pm_dict.get(_pr_path)
                        # Effective BU: project override > space rule
                        _eff_bu  = _pr_bu if _pr_bu else _sp_bu
                        _pk = f"{_sp}_{_pri}"  # index-based — guaranteed unique per space

                        _pc1, _pc2, _pc3 = st.columns([3, 1, 1])
                        _pr_label = f"&nbsp;&nbsp;&nbsp;📄 {_pr}"
                        if _pr_bu and _pr_bu != _sp_bu:
                            _pr_label += "&nbsp;&nbsp;" + _badge(_pr_bu)
                        elif _eff_bu:
                            _pr_label += f"&nbsp;&nbsp;<span style='color:#888;font-size:.75rem'>({_bu_name.get(_eff_bu,'?')} via space)</span>"
                        _pc1.markdown(_pr_label, unsafe_allow_html=True)
                        if _pc2.button("Assign", key=f"pr_a_{_pk}", use_container_width=True):
                            _assign(_pr_path, _sel_bu_id)
                        if _pr_bu and _pc3.button("Clear", key=f"pr_c_{_pk}", use_container_width=True):
                            _assign(_pr_path, None)
                else:
                    st.caption("No individual projects found in execution data.")

# ── User Mappings tab ────────────────────────────────────────────────────────
with tab_users:
    st.subheader("User → BU Mappings")
    st.caption(
        "Map platform users to business units. "
        "**User mappings take priority over project-path rules** — "
        "useful when a user runs pipelines in a shared namespace but costs should flow to their own BU."
    )

    from mock_data import BU_COLORS as _BUC  # already imported above via _BUC alias in project tab

    _u_bu_name    = {b["id"]: b["name"]  for b in st.session_state.bus}
    _u_bu_color   = {b["id"]: _BUC.get(b["id"], "#666") for b in st.session_state.bus}
    _u_bu_by_name = {b["name"]: b["id"]  for b in st.session_state.bus}
    _u_bu_list    = [b["name"] for b in st.session_state.bus]
    _u_um_dict    = {m["username"].lower(): m["bu_id"] for m in st.session_state.user_mappings}
    _u_excl_set   = {e.lower() for e in st.session_state.get("excluded_users", [])}

    _TRAINING_SENTINEL = "__training__"

    def _u_badge(bu_id):
        if bu_id == _TRAINING_SENTINEL:
            return ("<span style='background:#6B7280;color:#fff;padding:2px 8px;"
                    "border-radius:10px;font-size:.78rem;font-weight:600'>🎓 Training</span>")
        if not bu_id:
            return "<span style='color:#888;font-size:.8rem'>— unassigned —</span>"
        c = _u_bu_color.get(bu_id, "#888")
        n = _u_bu_name.get(bu_id, bu_id)
        return (f"<span style='background:{c};color:#fff;padding:2px 8px;"
                f"border-radius:10px;font-size:.78rem;font-weight:600'>{n}</span>")

    def _u_assign(username, target):
        username = username.lower()
        st.session_state.user_mappings = [
            m for m in st.session_state.user_mappings if m["username"].lower() != username
        ]
        excl = [e for e in st.session_state.get("excluded_users", []) if e.lower() != username]
        if target == _TRAINING_SENTINEL:
            excl.append(username)
        elif target:
            st.session_state.user_mappings.append({"username": username, "bu_id": target})
        st.session_state.excluded_users = excl
        save_user_state(
            st.session_state.user_mappings,
            st.session_state.excluded_users,
            st.session_state.get("_platform_users", []),
            st.session_state.get("project_mappings", []),
        )
        st.rerun()

    _TRAINING_GROUPS_KW = {"bootcamp", "training", "workshop", "learn"}

    def _is_training_groups(groups_str: str) -> bool:
        """True when every non-'members' group matches a training keyword."""
        groups = [g for g in groups_str.split() if g.lower() != "members"]
        if not groups:
            return False
        return all(any(k in g.lower() for k in _TRAINING_GROUPS_KW) for g in groups)

    import csv as _csv_mod, io as _io

    _CSV_DEFAULT_PATH = os.path.expanduser("~/Downloads/users_ConnectFasterInc.csv")

    def _parse_users_csv(content: str) -> tuple:
        """Parse CSV content → (parsed_list, auto_excl_list).
        @snaplogic.com users are never training — they run the bootcamps.
        """
        _rows   = list(_csv_mod.DictReader(_io.StringIO(content)))
        _parsed = []
        _excl   = []
        _seen   = set()
        for _row in _rows:
            _email  = (_row.get("Email") or "").strip().lower()
            _name   = (_row.get("Name") or "").strip()
            _groups = (_row.get("Groups") or "").strip()
            if not _email or "@" not in _email or _email in _seen:
                continue
            _seen.add(_email)
            _parsed.append({"email": _email, "name": _name or _email,
                             "roles": [_row.get("Role", "")], "groups": _groups.split()})
            if _is_training_groups(_groups) and not _email.endswith("@snaplogic.com"):
                _excl.append(_email)
        return _parsed, _excl

    def _apply_csv_import(parsed, auto_excl):
        st.session_state["_platform_users"]        = parsed
        st.session_state["_platform_users_loaded"] = True
        _excl_merged = list(set(st.session_state.get("excluded_users", [])) | set(auto_excl))
        st.session_state.user_mappings = [
            m for m in st.session_state.user_mappings
            if m["username"] not in set(auto_excl)
        ]
        st.session_state.excluded_users = _excl_merged
        import hashlib as _hashlib
        _dm       = {r["domain"]: r["bu_id"] for r in st.session_state.get("domain_rules", [])}
        _excl_set = set(auto_excl)
        _already  = {m["username"] for m in st.session_state.user_mappings}
        _bu_ids   = [b["id"] for b in st.session_state.bus if b["id"] != "bu_other"]
        for _pu in parsed:
            _em  = _pu["email"]
            if _em in _excl_set or _em in _already:
                continue
            _dom = _em.split("@")[1] if "@" in _em else ""
            if _dom in _dm:
                # Named partner domain → mapped BU (e.g. bu_other)
                st.session_state.user_mappings.append({"username": _em, "bu_id": _dm[_dom]})
                _already.add(_em)
            elif _em.endswith("@snaplogic.com"):
                # Internal SnapLogic staff → distribute across BUs by stable hash
                _bu_id = _bu_ids[int(_hashlib.md5(_em.encode()).hexdigest(), 16) % len(_bu_ids)]
                st.session_state.user_mappings.append({"username": _em, "bu_id": _bu_id})
                _already.add(_em)
            # Everything else → left unassigned
        save_user_state(
            st.session_state.user_mappings,
            st.session_state.excluded_users,
            st.session_state.get("_platform_users", []),
            st.session_state.get("project_mappings", []),
        )

    # ── Auto-load CSV on first render (or forced reload) ─────────────────────
    if not st.session_state.get("_platform_users_loaded"):
        if os.path.exists(_CSV_DEFAULT_PATH):
            try:
                with open(_CSV_DEFAULT_PATH, encoding="utf-8-sig") as _f:
                    _auto_parsed, _auto_excl = _parse_users_csv(_f.read())
                # Reset any stale user_mappings/excluded_users before applying
                from mock_data import DEFAULT_USER_MAPPINGS
                st.session_state.user_mappings = [m.copy() for m in DEFAULT_USER_MAPPINGS]
                st.session_state.excluded_users = []
                _apply_csv_import(_auto_parsed, _auto_excl)
                st.session_state["_csv_autoloaded"] = True
                st.rerun()
            except Exception:
                pass

    # ── Status line ───────────────────────────────────────────────────────────
    if st.session_state.get("_platform_users_loaded"):
        _n_excl = len(_u_excl_set)
        _src    = "auto-loaded from Downloads" if st.session_state.get("_csv_autoloaded") else "loaded"
        st.caption(
            f"✅ {len(st.session_state.get('_platform_users', []))} users {_src}"
            + (f"  ·  {_n_excl} marked as Training" if _n_excl else "")
        )

    # ── Manual CSV import / API fetch (collapsed once loaded) ─────────────────
    with st.expander("📥 Import / Refresh user list", expanded=not st.session_state.get("_platform_users_loaded")):
        if os.path.exists(_CSV_DEFAULT_PATH) and st.session_state.get("_platform_users_loaded"):
            if st.button("🔄 Reload from CSV (re-apply all rules)", key="reload_csv"):
                st.session_state.pop("_platform_users_loaded", None)
                st.session_state.pop("_csv_autoloaded", None)
                st.rerun()

        _u_envs = active_environments(st)
        if _u_envs:
            if st.button("☁️ Fetch users from Platform API", key="fetch_users_api"):
                try:
                    _uclient   = SnapLogicClient.from_env(_u_envs[0])
                    _api_users = _uclient.list_users()
                    if _api_users:
                        st.session_state["_platform_users"]        = _api_users
                        st.session_state["_platform_users_loaded"] = True
                        st.session_state.pop("_csv_autoloaded", None)
                        st.rerun()
                    else:
                        st.warning("Members API returned no data — use CSV import below.")
                except Exception as _ue:
                    st.error(f"Platform API error: {_ue}")

        st.caption(
            "Upload the export from **SnapLogic Platform → Settings → Users → Export**. "
            "Expected columns: `Name, Email, Role, App access, Groups, Date added`"
        )
        _csv_file = st.file_uploader("Upload users CSV", type="csv", key="users_csv_upload")
        if _csv_file:
            _parsed, _auto_excl = _parse_users_csv(_csv_file.read().decode("utf-8-sig"))
            _n_training = len(_auto_excl)
            _n_regular  = len(_parsed) - _n_training
            st.info(
                f"Found **{len(_parsed)} users** — "
                f"**{_n_regular} regular** and **{_n_training} training** "
                f"(only in Bootcamp/Training/Workshop groups)."
            )
            _ic1, _ic2 = st.columns(2)
            if _ic1.button(f"✅ Import + auto-mark {_n_training} as Training", key="csv_import_auto"):
                _apply_csv_import(_parsed, _auto_excl)
                st.session_state.pop("_csv_autoloaded", None)
                st.rerun()
            if _ic2.button("📋 Import (no auto-training)", key="csv_import_plain"):
                st.session_state["_platform_users"]        = _parsed
                st.session_state["_platform_users_loaded"] = True
                st.session_state.pop("_csv_autoloaded", None)
                save_user_state(
                    st.session_state.user_mappings,
                    st.session_state.get("excluded_users", []),
                    _parsed,
                )
                st.rerun()

    # ── Domain rules ─────────────────────────────────────────────────────────
    with st.expander("🌐 Domain Rules — auto-assign by email domain"):
        _dr_bu_names  = {b["id"]: b["name"] for b in st.session_state.bus}
        _dr_bu_by_name = {b["name"]: b["id"] for b in st.session_state.bus}

        # Current rules table + delete
        if st.session_state.domain_rules:
            for _dri, _dr in enumerate(st.session_state.domain_rules):
                _drc1, _drc2, _drc3 = st.columns([3, 3, 1])
                _drc1.markdown(f"`@{_dr['domain']}`")
                _drc2.markdown(f"→ **{_dr_bu_names.get(_dr['bu_id'], _dr['bu_id'])}**")
                if _drc3.button("✕", key=f"dr_del_{_dri}", use_container_width=True):
                    st.session_state.domain_rules.pop(_dri)
                    st.rerun()
        else:
            st.caption("No domain rules defined.")

        # Add new rule
        with st.form("add_domain_rule"):
            _ndr1, _ndr2, _ndr3 = st.columns([3, 3, 1])
            _new_domain = _ndr1.text_input("Domain", placeholder="example.com")
            _new_dr_bu  = _ndr2.selectbox("→ BU", [b["name"] for b in st.session_state.bus])
            if _ndr3.form_submit_button("Add", use_container_width=True):
                if _new_domain:
                    _clean = _new_domain.strip().lower().lstrip("@")
                    if not any(r["domain"] == _clean for r in st.session_state.domain_rules):
                        st.session_state.domain_rules.append(
                            {"domain": _clean, "bu_id": _dr_bu_by_name[_new_dr_bu]}
                        )
                    st.rerun()

        st.markdown("---")
        # Apply rules to all loaded users
        if st.button("⚡ Apply domain rules to all unassigned users", key="apply_domain_rules"):
            _dm = {r["domain"]: r["bu_id"] for r in st.session_state.domain_rules}
            _excl_set_dr = {e.lower() for e in st.session_state.get("excluded_users", [])}
            _mapped_set  = {m["username"].lower() for m in st.session_state.user_mappings}
            _applied = 0
            for _pu in st.session_state.get("_platform_users", []):
                _em = _pu["email"].lower()
                if _em in _excl_set_dr or _em in _mapped_set:
                    continue
                _dom = _em.split("@")[1] if "@" in _em else ""
                if _dom in _dm:
                    st.session_state.user_mappings.append({"username": _em, "bu_id": _dm[_dom]})
                    _applied += 1
            if _applied:
                save_user_state(
                    st.session_state.user_mappings,
                    st.session_state.get("excluded_users", []),
                    st.session_state.get("_platform_users", []),
                )
                st.success(f"✅ Assigned {_applied} users by domain rule.")
                st.rerun()
            else:
                st.info("No unassigned users matched any domain rule.")

    # ── Build user list: platform API/CSV + exec data + existing mappings ───────
    _all_users: dict   = {}   # email (lowercase) → display_name
    _user_groups: dict = {}   # email (lowercase) → groups list (from CSV/API)

    for _pu in st.session_state.get("_platform_users", []):
        _key = _pu["email"].lower()
        _all_users[_key] = _pu.get("name") or _key
        if _pu.get("groups"):
            _user_groups[_key] = _pu["groups"]

    if "_live_exec_df" in st.session_state:
        for _ue in st.session_state["_live_exec_df"]["user_id"].dropna().unique():
            _ue = str(_ue).lower()
            if "@" in _ue:
                _all_users.setdefault(_ue, _ue)

    for _m in st.session_state.user_mappings:
        _key = _m["username"].lower()
        if "@" in _key:   # non-email entries are project-space fallbacks, not real user accounts
            _all_users.setdefault(_key, _key)
    for _eu in st.session_state.get("excluded_users", []):
        _key = _eu.lower()
        _all_users.setdefault(_key, _key)

    if not _all_users:
        st.info(
            "No users loaded yet. Use **Fetch users from Platform API** or **Import from CSV** above."
        )
    else:
        _utcol, _ubcol = st.columns([3, 1])

        with _ubcol:
            st.markdown("**Assign selection to:**")
            _radio_options = ["🎓 Training (no cost)"] + _u_bu_list
            _u_sel_label   = st.radio("Target", _radio_options, label_visibility="collapsed",
                                      key="um_tree_bu_sel")
            if _u_sel_label == "🎓 Training (no cost)":
                _u_sel_target = _TRAINING_SENTINEL
                st.markdown(
                    "<div style='background:#6B7280;color:#fff;padding:6px 10px;"
                    "border-radius:8px;text-align:center;font-weight:600;margin-top:4px'>"
                    "🎓 Training — no cost, excluded from headcount</div>",
                    unsafe_allow_html=True,
                )
            else:
                _u_sel_target = _u_bu_by_name[_u_sel_label]
                _u_sel_color  = _u_bu_color.get(_u_sel_target, "#888")
                st.markdown(
                    f"<div style='background:{_u_sel_color};color:#fff;padding:6px 10px;"
                    f"border-radius:8px;text-align:center;font-weight:600;margin-top:4px'>"
                    f"{_u_sel_label}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("---")
            st.caption(
                "**Training** users are excluded from all cost allocation and do not "
                "count toward BU headcount. Click **Clear** to unset any assignment."
            )

        with _utcol:
            # Filter / summary bar
            _n_total      = len(_all_users)
            _n_mapped     = sum(1 for e in _all_users if e in _u_um_dict or e in _u_excl_set)
            _n_unassigned = _n_total - _n_mapped
            _n_sl_unasgn  = sum(1 for e in _all_users
                                if e.endswith("@snaplogic.com") and e not in _u_um_dict and e not in _u_excl_set)
            _flt1, _flt2 = st.columns([3, 2])
            _flt1.caption(
                f"{_n_total} users total · {_n_mapped} assigned · "
                f"**{_n_unassigned} unassigned**"
                + (f" · ⚠️ {_n_sl_unasgn} @snaplogic.com need BU" if _n_sl_unasgn else "")
            )
            _show_unasgn_sl = _flt2.toggle("Show only unassigned @snaplogic.com", key="filter_sl_only")

            def _u_sort_key(kv):
                email = kv[0]
                if email in _u_excl_set:
                    return (1, email.lower())
                if email in _u_um_dict:
                    return (0, email.lower())
                return (2, email.lower())

            _sorted_users = sorted(_all_users.items(), key=_u_sort_key)
            if _show_unasgn_sl:
                _sorted_users = [
                    (e, n) for e, n in _sorted_users
                    if e.endswith("@snaplogic.com") and e not in _u_um_dict and e not in _u_excl_set
                ]
            for _ui, (_uemail, _uname) in enumerate(_sorted_users):
                _is_training = _uemail in _u_excl_set
                _cur_bu      = _TRAINING_SENTINEL if _is_training else _u_um_dict.get(_uemail)
                _uc1i, _uc2i, _uc3i = st.columns([4, 1, 1])
                if _uname != _uemail:
                    _display = f"👤 **{_uname}** &nbsp;<span style='color:#888;font-size:.8rem'>{_uemail}</span>"
                else:
                    _display = f"👤 {_uemail}"
                _grps = _user_groups.get(_uemail, [])
                if _grps:
                    _grp_str = ", ".join(g for g in _grps if g.lower() != "members")
                    if _grp_str:
                        _display += f"&nbsp;&nbsp;<span style='color:#6B7280;font-size:.75rem'>{_grp_str}</span>"
                _display += f"&nbsp;&nbsp;{_u_badge(_cur_bu)}"
                _uc1i.markdown(_display, unsafe_allow_html=True)
                if _uc2i.button("Assign", key=f"u_assign_{_ui}", use_container_width=True):
                    _u_assign(_uemail, _u_sel_target)
                if _cur_bu and _uc3i.button("Clear", key=f"u_clear_{_ui}", use_container_width=True):
                    _u_assign(_uemail, None)

# ── Import from Platform tab ──────────────────────────────────────────────────
with tab_import:
    st.subheader("Import Live Snaplexes from Platform")
    envs = active_environments(st)

    if not envs:
        st.info("Add at least one SnapLogic environment on the **Home** page to import live Snaplex data.")
    else:
        env_labels = [f"{e['name']} ({e['org']})" for e in envs]
        sel_env_label = st.selectbox("Environment", env_labels, key="import_env_sel")
        sel_env = envs[env_labels.index(sel_env_label)]

        if st.button("🔄 Fetch Snaplexes from API"):
            try:
                client = SnapLogicClient.from_env(sel_env)
                live_snaplexes = client.list_snaplexes()
                st.session_state["_live_snaplexes"] = live_snaplexes
                st.session_state["_live_snaplexes_env"] = sel_env
                st.success(f"Found {len(live_snaplexes)} Snaplexes in {sel_env['org']}.")
            except Exception as e:
                st.error(f"API error: {e}")

        if "_live_snaplexes" in st.session_state:
            ls = st.session_state["_live_snaplexes"]
            df_live = pd.DataFrame([{
                "Name":            s.get("name", ""),
                "Location":        s.get("location", "—"),
                "Type hint":       s.get("type_hint", "—"),
                "Nodes (live)":    s.get("jcc_count", "—"),
                "Active Pipes":    s.get("active_pipelines", 0),
                "Snode ID":        s.get("snode_id", ""),
                "Runtime Path ID": s.get("runtime_path_id", ""),
            } for s in ls])
            st.dataframe(df_live, use_container_width=True, hide_index=True)

            st.markdown("**Add Snaplex to chargeback model**")
            st.caption("Name, Snode ID, and Runtime Path ID are pulled from the API. "
                       "Type and node count are pre-filled from the API where possible — "
                       "adjust if they don't match your billing contract. "
                       "Node cost and BU assignment are always manual.")
            live_names = [s.get("name", "") for s in ls]
            sel_live = st.selectbox("Select Snaplex", live_names, key="live_slx_sel")
            sel_live_data = next(s for s in ls if s.get("name") == sel_live)

            # Pre-fill from API
            _api_type_hint  = sel_live_data.get("type_hint", "shared")
            _api_node_hint  = int(sel_live_data.get("node_hint") or 1)
            _type_options   = ["cloudplex", "shared", "dedicated"]
            _type_default   = _type_options.index(_api_type_hint) if _api_type_hint in _type_options else 1

            ic1, ic2, ic3, ic4 = st.columns(4)
            import_type  = ic1.selectbox("Type", _type_options, index=_type_default, key="imp_type",
                                          help="Pre-filled from API `location`. Change to 'dedicated' if exclusively used by one BU.")
            import_nodes = ic2.number_input("Nodes (billing)", min_value=1, step=1, value=_api_node_hint,
                                             key="imp_nodes",
                                             help="Pre-filled from live JCC count. Verify against your contract for K8s auto-scale Snaplexes.")
            _ntype_options = list(NODE_TYPE_COSTS.keys())
            # Derive default from the CURRENT type selection, not just the API hint
            _is_cloudplex  = (import_type == "cloudplex")
            _ntype_default = _ntype_options.index("Cloudplex") if _is_cloudplex and "Cloudplex" in _ntype_options else 0
            # Key includes import_type so the widget re-creates (and picks new default) when type changes
            import_node_type = ic3.selectbox("Node Type", _ntype_options, index=_ntype_default,
                                              key=f"imp_ntype_{import_type}",
                                              help="Node tier from your SnapLogic contract. Not available from API — select to auto-fill cost.")
            _preset_cost = NODE_TYPE_COSTS.get(import_node_type) or 2200
            # Key includes node type so widget re-creates (and picks new preset) when node type changes
            import_ncost = ic4.number_input("Node cost/month ($)", min_value=0, step=100,
                                             value=int(_preset_cost), key=f"imp_ncost_{import_node_type}",
                                             help="Auto-filled from Node Type. Override if your contract differs.")
            _ic_bu, _ic_env = st.columns(2)
            import_bu   = _ic_bu.selectbox("Owner BU (for dedicated) / leave Shared for shared Snaplexes",
                                            ["(Shared)"] + [b["name"] for b in st.session_state.bus],
                                            key="imp_bu")
            import_env  = _ic_env.selectbox("Environment", ["Production", "Non-Production"], key="imp_env")

            if st.button("➕ Add to Chargeback Model"):
                existing_ids = [s.get("snode_id") for s in st.session_state.snaplexes]
                if sel_live_data.get("snode_id") in existing_ids:
                    st.warning("Snaplex already in the model.")
                else:
                    new_id = "slx_" + sel_live.lower().replace(" ", "_")[:12]
                    bu_options_map = {b["name"]: b["id"] for b in st.session_state.bus}
                    st.session_state.snaplexes.append({
                        "id":               new_id,
                        "name":             sel_live,
                        "type":             import_type,
                        "node_type":        import_node_type,
                        "bu_id":            bu_options_map.get(import_bu) if import_bu != "(Shared)" else None,
                        "nodes":            int(import_nodes) if import_nodes else None,
                        "node_cost_monthly": int(import_ncost) if import_ncost else None,
                        "region":           sel_live_data.get("path", "").split("/")[2] if sel_live_data.get("path") else "",
                        "env":              import_env,
                        "snode_id":         sel_live_data.get("snode_id", ""),
                        "runtime_path_id":  sel_live_data.get("runtime_path_id", ""),
                    })
                    st.success(f"✅ '{sel_live}' added to the chargeback model.")
                    st.rerun()

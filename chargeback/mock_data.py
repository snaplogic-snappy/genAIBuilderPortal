"""
Mock data + cost engine for SnapLogic Chargeback Console.
Used in demo mode when no live API connection is configured.
"""
import json, os, random, threading
import urllib.request
import pandas as pd

_STATE_PATH       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_state.json")
_EXEC_CACHE_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec_data_cache.json")
_EXEC_COMPUTED_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec_data_computed.json")
_REFRESH_FLAG        = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".exec_refresh_done")

# Module-level shared state for background refresh (single-process demo use)
_refresh_result = {"rows": None, "fetched_at": None, "done": False}
_refresh_lock   = threading.Lock()

_SNOWFLAKE_TASK_URL = (
    "https://emea.snaplogic.com/api/1/rest/slsched/feed/"
    "ConnectFasterInc/Konstantin/Demo%20-%20SnapLogic%20CoE/"
    "SL_Runtime_Events_From_Snowflake%20Task"
)
_SNOWFLAKE_BEARER = "bwUXmqyneX9RFmFPmlqIbiMAvSXdJcH7"

# ── Exec data cache (Snowflake) ───────────────────────────────────────────────

def save_exec_cache(rows):
    """Persist raw Snowflake rows to disk."""
    import time as _t
    try:
        with open(_EXEC_CACHE_PATH, "w", encoding="utf-8") as _f:
            json.dump({"rows": rows, "fetched_at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())}, _f)
    except Exception:
        pass

def save_exec_computed(exec_data, fetched_at):
    """Persist pre-computed exec_data dict to disk (tiny, fast to load)."""
    try:
        with open(_EXEC_COMPUTED_PATH, "w", encoding="utf-8") as _f:
            json.dump({"exec_data": exec_data, "fetched_at": fetched_at}, _f)
    except Exception:
        pass

def load_exec_computed():
    """Return (exec_data_dict, fetched_at) or (None, None). Fast — no row parsing."""
    try:
        if os.path.exists(_EXEC_COMPUTED_PATH):
            with open(_EXEC_COMPUTED_PATH, encoding="utf-8") as _f:
                _d = json.load(_f)
            return _d.get("exec_data"), _d.get("fetched_at", "")
    except Exception:
        pass
    return None, None

def load_exec_cache():
    """Return (rows, fetched_at_str) or (None, None)."""
    try:
        if os.path.exists(_EXEC_CACHE_PATH):
            with open(_EXEC_CACHE_PATH, encoding="utf-8") as _f:
                _d = json.load(_f)
            return _d.get("rows", []), _d.get("fetched_at", "")
    except Exception:
        pass
    return None, None

def _parse_month(start_time):
    """Convert START_TIME string to a MONTHS-compatible label like 'Jul 2026'."""
    _MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    if not start_time:
        return None
    try:
        s = str(start_time).replace("T", " ").replace("Z", "")[:19]
        year, month = int(s[:4]), int(s[5:7])
        return f"{_MONTH_ABBR[month-1]} {year}"
    except Exception:
        return None

_MAX_EXEC_SEC = 3600  # cap per-execution duration at 1 hour (mirrors mock data logic)

def _snaplex_from_path(runtime_path_id, snaplexes):
    """Map RUNTIME_PATH_ID (e.g. 'ConnectFasterInc/rt/cloud/dev') to a snaplex id."""
    if not runtime_path_id:
        return "slx_cloud"
    rp = str(runtime_path_id).lower()
    for slx in (snaplexes or []):
        sn = (slx.get("snode_id") or "").lower()
        if sn and (sn == rp or sn in rp):
            return slx["id"]
    if "cloud" in rp:
        return "slx_cloud"
    return "slx_eks"

def _bu_from_path(pipeline_path, project_mappings):
    """Map a pipeline PATH like '/ConnectFasterInc/Jean-Claude/PROD_MCP' to a BU id."""
    if not pipeline_path or not project_mappings:
        return "bu_other"
    path_lc = str(pipeline_path).lower().rstrip("/")
    for pm in sorted(project_mappings, key=lambda x: len(x.get("project_path", "")), reverse=True):
        prefix = pm.get("project_path", "").lower().rstrip("/")
        if prefix and (path_lc == prefix or path_lc.startswith(prefix + "/")):
            return pm["bu_id"]
    return "bu_other"

def merge_exec_data(mock, real):
    """Overlay real Snowflake months over mock data; mock fills historical gaps."""
    merged = {m: mock.get(m, {}) for m in MONTHS}
    for month, mdata in real.items():
        if month in merged:
            merged[month] = mdata
    return merged

def rows_to_exec_data(rows, snaplexes, user_mappings=None, project_mappings=None):
    """Convert flat Snowflake rows to exec_data shape.

    exec_data: {month → {bu_id → {slx_id → {count, avg_duration_sec, total_duration_sec, failures}}}}

    BU: by PATH prefix matching against project_mappings.
    Snaplex: by RUNTIME_PATH_ID matching snode_id.
    Duration capped at _MAX_EXEC_SEC.
    """
    if not rows:
        return {}
    _pm = project_mappings or DEFAULT_PROJECT_MAPPINGS
    accum = {}
    for row in rows:
        month = _parse_month(row.get("START_TIME") or row.get("start_time"))
        if not month:
            continue
        path   = row.get("PATH") or row.get("path") or ""
        bu_id  = _bu_from_path(path, _pm)
        slx_id = _snaplex_from_path(
            row.get("RUNTIME_PATH_ID") or row.get("runtime_path_id"), snaplexes
        )
        status = (row.get("STATUS") or row.get("status") or "").lower()
        dur    = min(float(row.get("DURATION_SEC") or row.get("duration_sec") or 0), _MAX_EXEC_SEC)
        failed = 1 if status in ("failed", "error", "stopped") else 0

        bucket = accum.setdefault(month, {}).setdefault(bu_id, {}).setdefault(slx_id, {
            "count": 0, "total_duration_sec": 0.0, "failures": 0,
        })
        bucket["count"]              += 1
        bucket["total_duration_sec"] += dur
        bucket["failures"]           += failed

    for month_data in accum.values():
        for bu_data in month_data.values():
            for slx_data in bu_data.values():
                cnt = slx_data["count"] or 1
                slx_data["avg_duration_sec"] = slx_data["total_duration_sec"] / cnt
    return accum

def fetch_exec_from_snowflake():
    """POST to the Snowflake task endpoint; return list of row dicts or None."""
    try:
        req = urllib.request.Request(_SNOWFLAKE_TASK_URL, data=b"{}", method="POST")
        req.add_header("Authorization", f"Bearer {_SNOWFLAKE_BEARER}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8").strip()
        if not body:
            return None
        # Handle JSON array, NDJSON, or SnapLogic envelope
        if body.startswith("["):
            return json.loads(body)
        if body.startswith("{"):
            # Try NDJSON first
            lines = [l.strip() for l in body.splitlines() if l.strip().startswith("{")]
            if len(lines) > 1:
                return [json.loads(l) for l in lines]
            # Single envelope
            d = json.loads(body)
            for key in ("entities", "rows", "data", "result"):
                if key in d:
                    return d[key]
            return [d]
        return None
    except Exception:
        return None

def start_snowflake_refresh():
    """Kick off a background thread to fetch Snowflake data."""
    def _run():
        import time as _t
        rows = fetch_exec_from_snowflake()
        if rows is not None:
            fetched_at = _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())
            save_exec_cache(rows)
            # Pre-compute and save the aggregated dict so future startups are instant
            _real_ed  = rows_to_exec_data(rows, DEFAULT_SNAPLEXES)
            _merged   = merge_exec_data(_generate_exec_data(), _real_ed)
            save_exec_computed(_merged, fetched_at)
            with _refresh_lock:
                _refresh_result["rows"]       = rows
                _refresh_result["fetched_at"] = fetched_at
                _refresh_result["done"]       = True
    threading.Thread(target=_run, daemon=True).start()

def check_refresh_done():
    """Returns (rows, fetched_at) if a refresh completed since last check; else (None, None).
    Consumes the result so repeated calls don't re-trigger updates.
    """
    with _refresh_lock:
        if _refresh_result.get("done"):
            rows = _refresh_result["rows"]
            at   = _refresh_result["fetched_at"]
            _refresh_result["done"] = False
            _refresh_result["rows"] = None
            return rows, at
    return None, None

def save_user_state(user_mappings, excluded_users=None, platform_users=None, project_mappings=None):
    """Persist user mappings, excluded users, platform users, and project mappings to disk."""
    try:
        with open(_STATE_PATH, "w", encoding="utf-8") as _f:
            json.dump({
                "user_mappings":    user_mappings,
                "excluded_users":   excluded_users or [],
                "platform_users":   platform_users or [],
                "project_mappings": project_mappings or [],
            }, _f, ensure_ascii=False)
    except Exception:
        pass

def load_user_state():
    """Return (user_mappings, excluded_users, platform_users, project_mappings) from disk, or None."""
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, encoding="utf-8") as _f:
                _d = json.load(_f)
            return (
                _d.get("user_mappings", []),
                _d.get("excluded_users", []),
                _d.get("platform_users", []),
                _d.get("project_mappings", []),
            )
    except Exception:
        pass
    return None

MONTHS = ["Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "May 2026", "Jun 2026", "Jul 2026"]
CURRENT_MONTH = "Jul 2026"
CURRENT_MONTH_IDX = 6
CURRENT_MONTH_PROGRESS = 0.93  # July 29

BU_COLORS = {
    "bu_genai":    "#7C3AED",
    "bu_training": "#3B82F6",
    "bu_platform": "#10B981",
    "bu_presales": "#F59E0B",
    "bu_insurance":"#EF4444",
    "bu_healthcare":"#6366F1",
    "bu_mcp":      "#EC4899",
    "bu_proserv":  "#F97316",
    "bu_other":    "#14B8A6",
}

CATEGORY_COLORS = {
    "Dedicated Snaplex":     "#7C3AED",
    "Shared Snaplex":        "#A78BFA",
    "Platform Overhead":     "#F59E0B",
}

# SnapLogic node pricing tiers ($/node/month). None = user must enter.
NODE_TYPE_COSTS = {
    "M (Standard)":        2200,
    "L (Large / K8s)":     4000,
    "Cloudplex":           1800,
    "Memory-Optimized M":  None,   # contract-specific — user must enter
    "Custom":              None,
}

DEFAULT_BUS = [
    {"id": "bu_genai",     "name": "GenAI & Integration Platform", "cost_center": "CC-1001",
     "owner": "Jocelyn Arcega",   "headcount": 20},
    {"id": "bu_training",  "name": "Training & Enablement",        "cost_center": "CC-2001",
     "owner": "Multi-team",       "headcount": 6},
    {"id": "bu_platform",  "name": "Platform Engineering",         "cost_center": "CC-3001",
     "owner": "Nilesh Parmar",    "headcount": 6},
    {"id": "bu_presales",  "name": "Pre-Sales Engineering",        "cost_center": "CC-4001",
     "owner": "Konstantin Riegel","headcount": 5},
    {"id": "bu_insurance", "name": "Insurance Practice",           "cost_center": "CC-5001",
     "owner": "Toni Branco",      "headcount": 4},
    {"id": "bu_healthcare","name": "Healthcare Practice",          "cost_center": "CC-5002",
     "owner": "James Holliss",    "headcount": 3},
    {"id": "bu_mcp",       "name": "MCP Platform (COE)",           "cost_center": "CC-9001",
     "owner": "Platform COE",     "headcount": 4},
    {"id": "bu_proserv",   "name": "Professional Services",        "cost_center": "CC-6001",
     "owner": "Steve C",          "headcount": 5},
    {"id": "bu_other",     "name": "Other / External",             "cost_center": "CC-9999",
     "owner": "Various",          "headcount": 4},
]

DEFAULT_SNAPLEXES = [
    # Real ConnectFasterInc snaplexes — snode_id / runtime_path_id verified from
    # GET /api/1/rest/public/snaplex/ConnectFasterInc (Jul 2026)
    {"id": "slx_cloud",  "name": "SnapLogic Cloud (Cloudplex)", "type": "cloudplex",  "bu_id": None,
     "nodes": 4, "node_cost_monthly": 1800,
     "region": "aws-eu-west-1", "env": "Production",
     "snode_id": "ConnectFasterInc/rt/cloud/dev",
     "max_slots": 2000, "jcc_count": 2,
     "avg_active_pipelines": 32.0, "avg_cpu_pct": 7.0},
    {"id": "slx_eks",    "name": "EKS K8s EMEA Groundplex",     "type": "shared",     "bu_id": None,
     "nodes": 3, "node_cost_monthly": 4000, "region": "eu-central-1", "env": "Production",
     "snode_id": "ConnectFasterInc/rt/sidekick/demo",
     "max_slots": 4000, "jcc_count": 2,
     "avg_active_pipelines": 7.84, "avg_cpu_pct": 2.0},
    {"id": "slx_linux",  "name": "EMEA Linux Groundplex (EC2)",  "type": "dedicated",  "bu_id": "bu_training",
     "nodes": 2, "node_cost_monthly": 2200, "region": "eu-central-1", "env": "Production",
     "snode_id": "ConnectFasterInc/rt/sidekick/emea-linux-ec2",
     "max_slots": 4000, "jcc_count": 1,
     "avg_active_pipelines": 3.0, "avg_cpu_pct": 4.0},
    {"id": "slx_mcp",    "name": "MCP Server Groundplex",        "type": "dedicated",  "bu_id": "bu_mcp",
     "nodes": 1, "node_cost_monthly": 2200, "region": "eu-central-1", "env": "Production",
     "snode_id": "ConnectFasterInc/rt/sidekick/mcp",
     "max_slots": 4000, "jcc_count": 1,
     "avg_active_pipelines": 1.5, "avg_cpu_pct": 1.5},
    {"id": "slx_win",    "name": "EMEA Windows Groundplex (EC2)", "type": "shared",    "bu_id": None,
     "nodes": 1, "node_cost_monthly": 2200, "region": "eu-central-1", "env": "Production",
     "snode_id": "ConnectFasterInc/rt/sidekick/demo-win",
     "max_slots": 2000, "jcc_count": 1,
     "avg_active_pipelines": None, "avg_cpu_pct": None},
]

DEFAULT_OVERHEAD = {  # allocation_key default: blended 70% headcount / 30% usage
    "license":    8500,
    "coe_opex":   25000,
    "cloud_infra": 500,
    "allocation_key": "blended",
    "blended_headcount_pct": 70,
    "startup_overhead_sec": 10,
    "duration_cap_sec": 3600,
}


DEFAULT_USER_MAPPINGS = [
    # Real ConnectFasterInc users — user_id overrides project-path attribution
    # (e.g. kriegel runs in snapLogic4snapLogic namespace but costs go to Pre-Sales)
    {"username": "jarcega@snaplogic.com",        "bu_id": "bu_genai"},
    {"username": "lwang+admin@snaplogic.com",     "bu_id": "bu_genai"},
    {"username": "kriegel@snaplogic.com",         "bu_id": "bu_presales"},
    {"username": "nparmar@snaplogic.com",         "bu_id": "bu_platform"},
    {"username": "tbranco@snaplogic.com",         "bu_id": "bu_insurance"},
    {"username": "jholliss@snaplogic.com",        "bu_id": "bu_healthcare"},
    {"username": "mpentzek@snaplogic.com",        "bu_id": "bu_platform"},
    {"username": "dbapat@snaplogic.com",          "bu_id": "bu_other"},
    {"username": "sameerasalamshaikh@gmail.com",  "bu_id": "bu_other"},
    {"username": "cward@snaplogic.com",           "bu_id": "bu_other"},
    # Project-space fallback — matched when USER_ID = full path (no requester on triggered runs)
    # GenAI
    {"username": "Jean-Claude",          "bu_id": "bu_genai"},
    {"username": "LunaWang",             "bu_id": "bu_genai"},
    {"username": "Agent Creator",        "bu_id": "bu_genai"},
    # Training
    {"username": "snapLogic4snapLogic",  "bu_id": "bu_genai"},
    {"username": "Jean Claude",          "bu_id": "bu_genai"},
    {"username": "toolsasapi",           "bu_id": "bu_genai"},
    {"username": "toolsasmcp",           "bu_id": "bu_genai"},
    # Platform
    {"username": "Nilesh",               "bu_id": "bu_platform"},
    {"username": "Angelica",             "bu_id": "bu_platform"},
    {"username": "projects",             "bu_id": "bu_platform"},
    {"username": "autosync",             "bu_id": "bu_platform"},
    # Pre-Sales
    {"username": "Konstantin",           "bu_id": "bu_presales"},
    {"username": "Ravik",                "bu_id": "bu_presales"},
    {"username": "SteveC Project Space", "bu_id": "bu_proserv"},
    {"username": "RG",                   "bu_id": "bu_platform"},
    {"username": "Markus",               "bu_id": "bu_presales"},
    # Insurance
    {"username": "Toni",                 "bu_id": "bu_insurance"},
    # Healthcare
    {"username": "James",                "bu_id": "bu_healthcare"},
    # MCP COE
    {"username": "apim",                 "bu_id": "bu_mcp"},
    # Other
    {"username": "Joe",                  "bu_id": "bu_insurance"},
    {"username": "Jordan Millhausen",    "bu_id": "bu_insurance"},
    {"username": "Jee",                  "bu_id": "bu_insurance"},
    {"username": "Jocelyn",              "bu_id": "bu_healthcare"},
    {"username": "00_GauravSubhedar",    "bu_id": "bu_healthcare"},
    {"username": "bromano",              "bu_id": "bu_healthcare"},
    {"username": "IWConnect",            "bu_id": "bu_other"},
]

DEFAULT_PROJECT_MAPPINGS = [
    # Real ConnectFasterInc namespace → BU mappings (verified from July 2026 runtime data)
    # GenAI & Integration Platform
    {"project_path": "/ConnectFasterInc/Jean-Claude",           "bu_id": "bu_genai"},
    {"project_path": "/ConnectFasterInc/Jean Claude",           "bu_id": "bu_genai"},
    {"project_path": "/ConnectFasterInc/LunaWang",              "bu_id": "bu_genai"},
    {"project_path": "/ConnectFasterInc/Agent Creator",         "bu_id": "bu_genai"},
    {"project_path": "/ConnectFasterInc/snapLogic4snapLogic",   "bu_id": "bu_genai"},
    {"project_path": "/ConnectFasterInc/toolsasapi",            "bu_id": "bu_genai"},
    {"project_path": "/ConnectFasterInc/toolsasmcp",            "bu_id": "bu_genai"},
    # Platform Engineering
    {"project_path": "/ConnectFasterInc/Nilesh",                "bu_id": "bu_platform"},
    {"project_path": "/ConnectFasterInc/Angelica",              "bu_id": "bu_platform"},
    {"project_path": "/ConnectFasterInc/projects",              "bu_id": "bu_platform"},
    {"project_path": "/ConnectFasterInc/autosync",              "bu_id": "bu_platform"},
    # Pre-Sales Engineering
    {"project_path": "/ConnectFasterInc/Konstantin",            "bu_id": "bu_presales"},
    {"project_path": "/ConnectFasterInc/Ravik",                 "bu_id": "bu_presales"},
    {"project_path": "/ConnectFasterInc/SteveC Project Space",  "bu_id": "bu_proserv"},
    {"project_path": "/ConnectFasterInc/RG",                    "bu_id": "bu_platform"},
    {"project_path": "/ConnectFasterInc/Markus",                "bu_id": "bu_presales"},
    # Insurance Practice
    {"project_path": "/ConnectFasterInc/Toni",                  "bu_id": "bu_insurance"},
    # Healthcare Practice
    {"project_path": "/ConnectFasterInc/James",                 "bu_id": "bu_healthcare"},
    # MCP Platform COE
    {"project_path": "/ConnectFasterInc/apim",                  "bu_id": "bu_mcp"},
    # Other / External
    # Insurance Practice
    {"project_path": "/ConnectFasterInc/Joe",                   "bu_id": "bu_insurance"},
    {"project_path": "/ConnectFasterInc/Jordan Millhausen",     "bu_id": "bu_insurance"},
    {"project_path": "/ConnectFasterInc/Jee",                   "bu_id": "bu_insurance"},
    # Healthcare Practice
    {"project_path": "/ConnectFasterInc/Jocelyn",               "bu_id": "bu_healthcare"},
    {"project_path": "/ConnectFasterInc/00_GauravSubhedar",     "bu_id": "bu_healthcare"},
    {"project_path": "/ConnectFasterInc/bromano",               "bu_id": "bu_healthcare"},
    # Other / External
    {"project_path": "/ConnectFasterInc/IWConnect",             "bu_id": "bu_other"},
]


def _generate_exec_data():
    rng = random.Random(42)
    # Base volumes calibrated to real July 2026 ConnectFasterInc data (duration_sec
    # uses state_timestamp - create_time, capped at 60 min per execution):
    #
    # bu_genai:    Jean-Claude MCP tools (slx_cloud: 77k × 1.7s) + snapLogic4snapLogic
    #              Slack agents (slx_eks: 7.3k × 128s avg, capped) → ~17.8k min
    # bu_presales: Konstantin POC pipelines (slx_eks: 2.1k × 13s) + Ravik/Markus
    #              agents (slx_cloud: 80 × 260s) → ~814 min
    # (count, avg_dur_sec) → total_duration_sec = count * avg_dur
    base = {
        "bu_genai":     {"slx_cloud": (77000, 1.7), "slx_eks":  (7300, 128)},
        "bu_training":  {"slx_linux": (150,   25),  "slx_cloud": (100,  10)},
        "bu_platform":  {"slx_eks":   (700,   22),  "slx_mcp":   (800,   8)},
        "bu_presales":  {"slx_eks":   (2100,  13),  "slx_cloud":  (80, 260)},
        "bu_insurance": {"slx_eks":   (750,   32),  "slx_cloud":  (50,  20)},
        "bu_healthcare":{"slx_cloud": (50,    20),  "slx_mcp":    (20,   8)},
        "bu_mcp":       {"slx_mcp":   (15,   120),  "slx_cloud":  (30,  10)},
        "bu_other":     {"slx_cloud": (50,   100)},
        "bu_proserv":   {"slx_cloud": (40,    25),  "slx_eks":    (20,  15)},
    }
    # Per-BU monthly multipliers (Jan→Jul).
    # Jun/Jul are overridden by real data — included so all 7 months render consistently.
    # GenAI grows fastest (+82% Jan→Jul); others show gentle growth (+12–25%).
    bu_multipliers = {
        "bu_genai":     [0.55, 0.62, 0.70, 0.78, 0.85, 0.92, 1.00],
        "bu_training":  [0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00],
        "bu_platform":  [0.75, 0.79, 0.83, 0.88, 0.92, 0.96, 1.00],
        "bu_presales":  [0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00],
        "bu_insurance": [0.82, 0.85, 0.88, 0.91, 0.94, 0.97, 1.00],
        "bu_healthcare":   [0.85, 0.87, 0.90, 0.93, 0.95, 0.97, 1.00],
        "bu_mcp":       [0.78, 0.82, 0.87, 0.91, 0.95, 0.97, 1.00],
        "bu_other":     [0.80, 0.84, 0.87, 0.91, 0.94, 0.97, 1.00],
        "bu_proserv":   [0.85, 0.87, 0.90, 0.93, 0.96, 0.98, 1.00],
    }
    default_mult = [0.82, 0.85, 0.88, 0.91, 0.94, 0.97, 1.00]

    result = {}
    for i, month in enumerate(MONTHS):
        result[month] = {}
        for bu_id, slx_map in base.items():
            result[month][bu_id] = {}
            mults = bu_multipliers.get(bu_id, default_mult)
            for slx_id, (base_count, avg_dur) in slx_map.items():
                jitter = rng.uniform(0.93, 1.07)
                count = int(base_count * mults[i] * jitter)
                actual_avg = avg_dur * rng.uniform(0.95, 1.05)
                result[month][bu_id][slx_id] = {
                    "count":              count,
                    "avg_duration_sec":   actual_avg,
                    "total_duration_sec": count * actual_avg,
                    "failures":           max(0, int(count * rng.uniform(0.005, 0.02))),
                }
    return result


def compute_monthly_costs(month, exec_data, snaplexes, bus, overhead,
                          include_dev=False, user_mappings=None):
    """
    Returns {bu_id: {snaplex, overhead_share, total}}.
    Each Snaplex's cost is split among BUs by their usage share on that specific
    Snaplex (adjusted exec minutes). Dedicated Snaplexes are fully charged to their
    owning BU. Platform overhead is allocated separately by allocation_key.

    user_mappings: if provided, headcount is computed from mapped email users rather
                   than the manually stored bu["headcount"] value.
    """
    bu_ids = [b["id"] for b in bus]
    costs = {bid: {"dedicated_snaplex": 0.0, "shared_snaplex": 0.0,
                   "snaplex": 0.0, "overhead_share": 0.0} for bid in bu_ids}

    # Headcount: count of distinct email-format user_mappings per BU
    if user_mappings is not None:
        _hc = {}
        for m in user_mappings:
            if "@" in m.get("username", ""):
                _hc[m["bu_id"]] = _hc.get(m["bu_id"], 0) + 1
    else:
        _hc = {b["id"]: b.get("headcount", 0) for b in bus}

    _startup = overhead.get("startup_overhead_sec", 10)
    prod_slx = [s for s in snaplexes
                if (include_dev or s.get("env") == "Production")
                and s.get("nodes") and s.get("node_cost_monthly")]

    for slx in prod_slx:
        slx_cost = slx["nodes"] * slx["node_cost_monthly"]
        if slx["type"] == "dedicated" and slx.get("bu_id") in costs:
            # Dedicated: full cost to owning BU
            costs[slx["bu_id"]]["dedicated_snaplex"] += slx_cost
        else:
            # Shared / Cloudplex: split by each BU's adjusted exec minutes on this Snaplex
            exec_mins = {}
            for bid in bu_ids:
                d = exec_data.get(month, {}).get(bid, {}).get(slx["id"], {})
                exec_mins[bid] = (load_seconds(d) + d.get("count", 0) * _startup) / 60
            total_mins = sum(exec_mins.values()) or 1
            for bid in bu_ids:
                costs[bid]["shared_snaplex"] += slx_cost * exec_mins[bid] / total_mins

    # 3. Platform overhead
    total_overhead = overhead["license"] + overhead["coe_opex"] + overhead["cloud_infra"]
    key = overhead.get("allocation_key", "equal")

    if key == "equal":
        per_bu = total_overhead / len(bus) if bus else 0
        for bid in bu_ids:
            costs[bid]["overhead_share"] = per_bu

    elif key == "usage_weighted":
        mins_map = {}
        for bid in bu_ids:
            m = sum(
                load_seconds(d) / 60
                for d in exec_data.get(month, {}).get(bid, {}).values()
            )
            mins_map[bid] = m
        grand = sum(mins_map.values()) or 1
        for bid in bu_ids:
            costs[bid]["overhead_share"] = total_overhead * mins_map[bid] / grand

    elif key == "headcount":
        total_hc = sum(_hc.get(bid, 0) for bid in bu_ids) or 1
        for bid in bu_ids:
            costs[bid]["overhead_share"] = total_overhead * _hc.get(bid, 0) / total_hc

    elif key == "blended":
        hc_pct  = overhead.get("blended_headcount_pct", 50) / 100.0
        vol_pct = 1.0 - hc_pct
        total_hc = sum(_hc.get(bid, 0) for bid in bu_ids) or 1
        mins_map = {}
        for bid in bu_ids:
            mins_map[bid] = sum(
                load_seconds(d) / 60
                for d in exec_data.get(month, {}).get(bid, {}).values()
            )
        grand = sum(mins_map.values()) or 1
        for bid in bu_ids:
            hc_share  = total_overhead * hc_pct  * _hc.get(bid, 0) / total_hc
            vol_share = total_overhead * vol_pct * mins_map[bid] / grand
            costs[bid]["overhead_share"] = hc_share + vol_share

    for bid in bu_ids:
        c = costs[bid]
        c["snaplex"] = c["dedicated_snaplex"] + c["shared_snaplex"]
        c["total"]   = c["snaplex"] + c["overhead_share"]

    return costs


def load_seconds(entry: dict) -> float:
    """Total node-seconds consumed by an execution entry.
    Uses total_duration_sec when available (live API data), falls back to
    count × avg for legacy mock entries that predate this field.
    """
    if "total_duration_sec" in entry:
        return entry["total_duration_sec"]
    return entry.get("count", 0) * entry.get("avg_duration_sec", 0)


def get_bu_name(bu_id, bus):
    for b in bus:
        if b["id"] == bu_id:
            return b["name"]
    return bu_id


def get_snaplex_name(slx_id, snaplexes):
    for s in snaplexes:
        if s["id"] == slx_id:
            return s["name"]
    return slx_id


def total_executions_for_month(month, exec_data):
    return sum(
        d.get("count", 0)
        for bu_data in exec_data.get(month, {}).values()
        for d in bu_data.values()
    )


def init_session_state(st):
    if "bus" not in st.session_state:
        st.session_state.bus = [b.copy() for b in DEFAULT_BUS]
    if "snaplexes" not in st.session_state:
        st.session_state.snaplexes = [s.copy() for s in DEFAULT_SNAPLEXES]
    if "overhead" not in st.session_state:
        st.session_state.overhead = DEFAULT_OVERHEAD.copy()
    # Load user + project mappings from disk early — needed by exec_data path below
    if "user_mappings" not in st.session_state:
        _saved = load_user_state()
        if _saved:
            _um, _excl, _pu, _pm_saved = _saved
            st.session_state.user_mappings = _um
            if "excluded_users" not in st.session_state:
                st.session_state.excluded_users = _excl
            if _pu and "_platform_users" not in st.session_state:
                st.session_state["_platform_users"]        = _pu
                st.session_state["_platform_users_loaded"] = True
            if _pm_saved and "project_mappings" not in st.session_state:
                st.session_state.project_mappings = _pm_saved
        else:
            st.session_state.user_mappings = [m.copy() for m in DEFAULT_USER_MAPPINGS]
    if "project_mappings" not in st.session_state:
        st.session_state.project_mappings = [m.copy() for m in DEFAULT_PROJECT_MAPPINGS]
    if "exec_data" not in st.session_state:
        # Fast path: pre-computed dict (tiny, loads in ms)
        _computed, _fetched_at = load_exec_computed()
        if _computed is not None:
            st.session_state.exec_data                = _computed
            st.session_state["_exec_data_source"]     = "snowflake"
            st.session_state["_exec_data_fetched_at"] = _fetched_at
            # Tell app.py not to fire its legacy 10s Snowflake loader
            if "_real_data_loaded" not in st.session_state:
                st.session_state["_real_data_loaded"] = True
        else:
            # Slow path: raw rows cache (54 MB) — only on first-ever run
            _mock_ed   = _generate_exec_data()
            _rows, _fetched_at = load_exec_cache()
            if _rows is not None:
                _real_ed = rows_to_exec_data(
                    _rows,
                    st.session_state.get("snaplexes", DEFAULT_SNAPLEXES),
                    project_mappings=st.session_state.get("project_mappings"),
                )
                _merged = merge_exec_data(_mock_ed, _real_ed)
                st.session_state.exec_data                = _merged
                st.session_state["_exec_data_source"]     = "snowflake"
                st.session_state["_exec_data_fetched_at"] = _fetched_at
                save_exec_computed(_merged, _fetched_at)
                if "_real_data_loaded" not in st.session_state:
                    st.session_state["_real_data_loaded"] = True
            else:
                st.session_state.exec_data                = _mock_ed
                st.session_state["_exec_data_source"]     = "mock"
                st.session_state["_exec_data_fetched_at"] = ""
    if "excluded_users" not in st.session_state:
        st.session_state.excluded_users = []
    if "domain_rules" not in st.session_state:
        st.session_state.domain_rules = [
            {"domain": "iwconnect.com",       "bu_id": "bu_other"},
            {"domain": "cognizant.com",       "bu_id": "bu_other"},
            {"domain": "accenture.com",       "bu_id": "bu_other"},
            {"domain": "reply.com",           "bu_id": "bu_other"},
            {"domain": "reply.de",            "bu_id": "bu_other"},
            {"domain": "srivensolutions.com",  "bu_id": "bu_other"},
            {"domain": "infosys.com",          "bu_id": "bu_other"},
            {"domain": "atos.net",             "bu_id": "bu_other"},
            {"domain": "rojoconsultancy.com",  "bu_id": "bu_other"},
        ]
    if "environments" not in st.session_state:
        st.session_state.environments = []
    if "api_exec_cache" not in st.session_state:
        st.session_state.api_exec_cache = {}
    if "api_config" not in st.session_state:
        st.session_state.api_config = None
    # Auto-register ConnectFasterInc connection from env vars on any page load
    if not st.session_state.environments and not st.session_state.get("_auto_connect_tried"):
        st.session_state["_auto_connect_tried"] = True
        import os as _os
        _server = "https://emea.snaplogic.com"
        _org    = "ConnectFasterInc"
        _user   = _os.getenv("SNAPLOGIC_USER", "")
        _pass   = _os.getenv("SNAPLOGIC_PASSWORD", "")
        _token  = _os.getenv("SNAPLOGIC_DEMO_TOKEN", _os.getenv("SNAPLOGIC_TOKEN", ""))
        if _user and _pass:
            _auth, _creds = "basic", {"username": _user, "password": _pass, "token": ""}
        elif _token:
            _auth, _creds = "bearer", {"username": "", "password": "", "token": _token}
        else:
            _auth, _creds = None, {}
        if _auth:
            try:
                from api_client import SnapLogicClient as _SLC
                _c = (_SLC.from_basic_auth(_server, _org, _creds["username"], _creds["password"])
                      if _auth == "basic" else _SLC.from_bearer(_server, _org, _creds["token"]))
                _ok, _ = _c.test_connection()
            except Exception:
                _ok = False
            _entry = {
                "name": "ConnectFasterInc", "server": _server, "org": _org,
                "auth_type": _auth, "connected": _ok,
                **_creds,
            }
            st.session_state.environments = [_entry]
            st.session_state.api_config   = _entry


def active_environments(st):
    """Returns list of connected environment dicts."""
    return [e for e in st.session_state.get("environments", []) if e.get("connected")]


def sidebar_connection_badge(st):
    envs = active_environments(st)
    if envs:
        for e in envs:
            st.sidebar.success(f"🟢 {e['name']} — {e['org']}")
    else:
        st.sidebar.warning("🟡 Demo Mode — mock data")

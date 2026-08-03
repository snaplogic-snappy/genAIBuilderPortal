"""
SnapLogic Platform API client for execution & Snaplex data.
Uses the SnapLogic Public REST API:
  Runtime log:   GET /api/1/rest/public/runtime/{org}
  Snaplex info:  GET /api/1/rest/public/snaplex/{org}
  Asset browse:  GET /api/1/rest/public/assetapi/{path}
"""
import requests
import pandas as pd
from datetime import datetime
import calendar
from typing import Optional


class SnapLogicClient:
    def __init__(self, server_url: str, org: str,
                 bearer_token: str = None,
                 username: str = None, password: str = None):
        """
        Accepts either bearer_token OR username+password (Basic Auth).
        Basic Auth: Authorization: Basic base64(username:password)
        """
        import base64
        self.base = server_url.rstrip("/")
        self.org = org
        if bearer_token:
            auth_value = f"Bearer {bearer_token}"
        elif username and password:
            encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
            auth_value = f"Basic {encoded}"
        else:
            raise ValueError("Provide either bearer_token or username+password")
        self.headers = {
            "Authorization": auth_value,
            "Content-Type": "application/json",
        }

    @classmethod
    def from_basic_auth(cls, server_url: str, org: str, username: str, password: str):
        return cls(server_url, org, username=username, password=password)

    @classmethod
    def from_bearer(cls, server_url: str, org: str, token: str):
        return cls(server_url, org, bearer_token=token)

    @classmethod
    def from_env(cls, env: dict) -> "SnapLogicClient":
        """Build a client from an environment dict stored in session_state.environments."""
        if env.get("auth_type") == "basic" or (env.get("username") and env.get("password")):
            return cls.from_basic_auth(env["server"], env["org"],
                                       env["username"], env["password"])
        return cls.from_bearer(env["server"], env["org"], env["token"])

    # ── Connectivity ─────────────────────────────────────────────────────────

    def test_connection(self) -> tuple:
        """Quick connectivity check against the Snaplex endpoint."""
        try:
            resp = requests.get(
                f"{self.base}/api/1/rest/public/snaplex/{self.org}",
                headers=self.headers,
                timeout=10,
            )
            if resp.status_code == 200:
                return True, "OK"
            return False, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            return False, str(e)

    # ── Snaplexes ─────────────────────────────────────────────────────────────

    def list_snaplexes(self) -> list:
        """
        List all Snaplexes with slot config and live node stats.
        Returns list of dicts: name, path, runtime_path_id, snode_id,
          max_slots, jcc_count, nodes_running, active_pipelines
        """
        resp = requests.get(
            f"{self.base}/api/1/rest/public/snaplex/{self.org}",
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        rm = data.get("response_map", {})

        # API returns a dict keyed by plex path
        if isinstance(rm, dict):
            results = []
            for path, entry in rm.items():
                pi = entry.get("plex_info", {})
                cc_running = entry.get("cc_info", {}).get("running", [])
                active_pipelines = sum(
                    n.get("stats", {}).get("active_pipelines", 0)
                    for n in cc_running
                )
                location = pi.get("location", "")
                # "cloud" = Cloudplex, "sidekick" = Groundplex
                type_hint = "cloudplex" if location == "cloud" else "shared"
                # jcc_count=0 on K8s auto-scale-to-zero; use nodes_running as fallback
                node_hint = pi.get("jcc_count") or len(cc_running) or 1
                results.append({
                    "name":             pi.get("label", path.rsplit("/", 1)[-1]),
                    "path":             path,
                    "runtime_path_id":  pi.get("runtime_path_id", ""),
                    "snode_id":         pi.get("snode_id", ""),
                    "max_slots":        pi.get("max_slots"),
                    "jcc_count":        pi.get("jcc_count"),
                    "nodes_running":    len(cc_running),
                    "active_pipelines": active_pipelines,
                    "location":         location,
                    "type_hint":        type_hint,
                    "node_hint":        node_hint,
                })
            return results

        # Fallback: list format
        if isinstance(rm, list):
            return rm
        return rm.get("entries", [])

    def get_snaplex_detail(self, plex_path: str) -> dict:
        """
        Get detailed Snaplex info including node count and status.
        plex_path: e.g. /ConnectFasterInc/shared/eks-k8s-emea-groundplex
        Returns plex_info (jcc_count, max_slots) + cc_info (running/down nodes).
        """
        resp = requests.get(
            f"{self.base}/api/1/rest/public/snaplex/{self.org}",
            headers=self.headers,
            params={"plex_path": plex_path},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        rm = data.get("response_map", {})
        return {
            "plex_info": rm.get("plex_info", {}),
            "cc_info":   rm.get("cc_info", {}),
        }

    # ── Asset / Project browsing ─────────────────────────────────────────────

    def list_projects(self, project_space: Optional[str] = None) -> list:
        """
        Return all project paths under the org (or a specific project space).
        Uses GET /api/1/rest/public/assetapi/{org}[/{project_space}]

        Each result dict: {"space": str, "project": str, "path": str}
        """
        browse_path = f"{self.org}/{project_space}" if project_space else self.org
        resp = requests.get(
            f"{self.base}/api/1/rest/public/assetapi/{browse_path}",
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        entries = data.get("response_map", {}).get("entries", [])
        results = []
        for entry in entries:
            epath = entry.get("path", "")
            parts = epath.strip("/").split("/")
            if len(parts) >= 3 and entry.get("asset_type") == "Project":
                results.append({
                    "space":   parts[1],
                    "project": parts[2],
                    "path":    epath,
                })
            elif len(parts) >= 2 and entry.get("asset_type") == "ProjectSpace":
                # Top-level browse: recurse into each space
                pass
        return results

    def list_users(self) -> list:
        """
        Return all org members.  Tries several known SnapLogic API shapes in order:
          1. GET /api/1/rest/public/org/{org}/members   (SnapLogic SaaS standard)
          2. GET /api/1/rest/public/user/list/{org}     (older control-plane variant)
        Returns [] on 403/404 (caller should fall back to CSV import).
        Each result dict: {"email": str, "name": str, "roles": list, "groups": list}
        """
        candidates = [
            f"{self.base}/api/1/rest/public/org/{self.org}/members",
            f"{self.base}/api/1/rest/public/user/list/{self.org}",
        ]
        for url in candidates:
            try:
                resp = requests.get(url, headers=self.headers, timeout=30)
            except Exception:
                continue
            if resp.status_code in (403, 404):
                continue
            if not resp.ok:
                continue
            data = resp.json()
            rm   = data.get("response_map", {})
            # Try known member-list keys
            members = (
                rm.get("members") or
                rm.get("users") or
                rm.get("user_list") or
                []
            )
            if not members:
                continue
            results = []
            for m in members:
                email = m.get("email") or m.get("user_id") or m.get("login") or m.get("name", "")
                results.append({
                    "email":  email,
                    "name":   m.get("display_name") or m.get("full_name") or m.get("name") or email,
                    "roles":  m.get("roles", []),
                    "groups": m.get("groups", []),
                })
            return results
        return []

    # ── Runtime log ──────────────────────────────────────────────────────────

    def get_executions_df(self, year: int, month: int, max_records: int = 20000) -> pd.DataFrame:
        """
        Fetch all pipeline executions for a given month via:
          GET /api/1/rest/public/runtime/{org}

        Returned DataFrame columns (normalised):
          label, path, runtime_path_id, status, duration_sec,
          start_time, document_count, error_documents, invoker, user_id
        """
        start_dt = datetime(year, month, 1)
        last_day  = calendar.monthrange(year, month)[1]
        end_dt    = datetime(year, month, last_day, 23, 59, 59)

        start_ms = int(start_dt.timestamp() * 1000)
        end_ms   = int(end_dt.timestamp()   * 1000)

        all_entries = []
        batch  = 1000
        offset = 0
        total  = None

        while offset < max_records:
            params = {
                "start":  start_ms,
                "end":    end_ms,
                "limit":  min(batch, max_records - offset),
                "offset": offset,
            }
            resp = requests.get(
                f"{self.base}/api/1/rest/public/runtime/{self.org}",
                headers=self.headers,
                params=params,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            rm      = data.get("response_map", {})
            entries = rm.get("entries", [])
            if total is None:
                total = rm.get("total", 0)

            all_entries.extend(entries)
            # Stop when we have all records or got a short page
            if len(entries) < batch or len(all_entries) >= total:
                break
            offset += batch

        if not all_entries:
            return pd.DataFrame(columns=[
                "label", "path", "runtime_path_id", "status",
                "duration_sec", "start_time", "document_count",
                "error_documents", "invoker", "user_id",
            ])

        df = pd.json_normalize(all_entries)

        # Normalise field names to our internal schema
        rename_map = {
            "state":       "status",        # Completed / Failed / Stopped
            "path_id":     "path",           # /Org/projects/…
            "create_time": "start_time",    # ISO timestamp
            "documents":   "document_count",
            # user identity — SnapLogic runtime API uses 'requester'; fall back to 'owner'
            "requester":   "user_id",
            "owner":       "user_id",
        }
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

        # Parse timestamps
        if "start_time" in df.columns:
            df["start_time"] = pd.to_datetime(df["start_time"], utc=True, errors="coerce")
        if "state_timestamp" in df.columns:
            df["end_time"] = pd.to_datetime(df["state_timestamp"], utc=True, errors="coerce")

        # Compute real duration from state_timestamp - create_time.
        # The API's $.duration field records dispatch overhead (~100ms), not actual
        # execution time. state_timestamp is when the pipeline last changed state,
        # giving true wall-clock duration for completed executions.
        if "end_time" in df.columns and "start_time" in df.columns:
            real_dur = (df["end_time"] - df["start_time"]).dt.total_seconds()
            df["duration_sec"] = real_dur.clip(lower=0, upper=3600).fillna(0.0)
        elif "duration" in df.columns:
            df["duration_sec"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0.0) / 1000.0
        else:
            df["duration_sec"] = 0.0

        # Guarantee all expected columns exist

        for col in ["label", "path", "runtime_path_id", "status",
                    "document_count", "error_documents", "invoker", "user_id"]:
            if col not in df.columns:
                df[col] = "" if col not in ("document_count", "error_documents") else 0

        return df

    # ── Derived Snaplex metrics ───────────────────────────────────────────────

    @staticmethod
    def compute_snaplex_metrics(df: pd.DataFrame, period_secs: float) -> dict:
        """
        Derive avg_active_pipelines per Snaplex from execution DataFrame.

        Uses Little's Law:
            avg_active = total_duration_sec / period_seconds

        This reconstructs the same "Active Pipelines (count) avg" number shown in
        the SnapLogic Monitor → Metrics dashboard, which is not available via the
        Public REST API directly.

        Returns:
          {runtime_path_id: {avg_active_pipelines, total_duration_sec, exec_count}}
        """
        if df.empty or period_secs <= 0:
            return {}

        result = {}
        for rt_id, grp in df.groupby("runtime_path_id"):
            total_dur = float(grp["duration_sec"].sum())
            result[str(rt_id)] = {
                "avg_active_pipelines": total_dur / period_secs,
                "total_duration_sec":   total_dur,
                "exec_count":           len(grp),
                "avg_duration_sec":     float(grp["duration_sec"].mean()),
            }
        return result

    # ── Aggregate for cost engine ─────────────────────────────────────────────

    def aggregate_by_snaplex_and_bu(
        self,
        df: pd.DataFrame,
        project_mappings: list,
        runtime_path_to_slx_id: dict,
        user_mappings: list = None,
        excluded_users: list = None,
    ) -> dict:
        """
        Convert raw executions DataFrame into:
          {bu_id: {snaplex_internal_id: {count, avg_duration_sec, failures}}}

        project_mappings:        [{project_path, bu_id}]  — prefix-match on path column
        runtime_path_to_slx_id:  {runtime_path_id → internal snaplex id}
                                  e.g. {"ConnectFasterInc/rt/sidekick/demo": "slx_shared"}
        user_mappings:           [{username, bu_id}]  — exact user_id match, takes priority
                                  over project-path mapping
        excluded_users:          [username/email, ...]  — training/inactive users whose
                                  executions are dropped from all cost allocation
        """
        if df.empty:
            return {}

        # Drop training / excluded users before any allocation
        _excl = set(excluded_users or [])
        if _excl:
            df = df[~df["user_id"].isin(_excl)].copy()
        if df.empty:
            return {}

        pm = {m["project_path"].rstrip("/"): m["bu_id"] for m in project_mappings}
        um = {m["username"]: m["bu_id"] for m in (user_mappings or [])}

        def resolve_bu(row) -> Optional[str]:
            # User mapping wins over project path
            if um and row.get("user_id") in um:
                return um[row["user_id"]]
            path = row.get("path", "")
            if not path:
                return None
            project = path.rstrip("/").rsplit("/", 1)[0]
            for prefix, bu_id in pm.items():
                if project.startswith(prefix):
                    return bu_id
            return None

        df = df.copy()
        df["bu_id"]   = df.apply(resolve_bu, axis=1)
        df["slx_key"] = df["runtime_path_id"].map(runtime_path_to_slx_id).fillna(
                            df["runtime_path_id"]
                        )
        df["failed"]  = ~df["status"].str.lower().isin(
                            ["completed", "complete", "succeeded"]
                        )

        result = {}
        for (bu_id, slx_key), grp in df.dropna(subset=["bu_id"]).groupby(["bu_id", "slx_key"]):
            if bu_id not in result:
                result[bu_id] = {}
            result[bu_id][slx_key] = {
                "count":              len(grp),
                "avg_duration_sec":   float(grp["duration_sec"].mean()),
                "total_duration_sec": float(grp["duration_sec"].sum()),
                "failures":           int(grp["failed"].sum()),
            }
        return result

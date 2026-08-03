"""
Snowflake data layer — accessed via SnapLogic triggered task endpoint.

Architecture:
  SL_Chargeback_Daily_Ingest  (scheduled, daily)
      SnapLogic runtime API  →  Snowflake PIPELINE_EXECUTIONS

  SL_Chargeback_Read Task     (triggered REST endpoint, bearer auth)
      Snowflake PIPELINE_EXECUTIONS  →  JSON response  →  this client
"""
import os
import requests
import pandas as pd


def snowflake_pipeline_available() -> bool:
    """True only when the task endpoint and bearer token are configured."""
    if os.environ.get("SNAPLOGIC_USE_SNOWFLAKE", "false").lower() != "true":
        return False
    return bool(
        os.environ.get("SL_READ_BEARER") and os.environ.get("SL_READ_ENDPOINT")
    )


def trigger_daily_ingest(timeout: int = 30) -> dict:
    """
    Fire the SL_Chargeback_Daily_Ingest Task to fetch yesterday's data into Snowflake.
    Returns the raw task response dict (non-blocking — pipeline runs async on the Snaplex).
    """
    bearer   = os.environ.get("SL_INGEST_BEARER", "")
    endpoint = os.environ.get("SL_INGEST_ENDPOINT", "")
    if not (bearer and endpoint):
        return {"error": "SL_INGEST_BEARER / SL_INGEST_ENDPOINT not configured"}
    resp = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {bearer}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def trigger_adhoc_ingest(start_date: str, end_date: str, timeout: int = 30) -> dict:
    """
    Fire the SL_Chargeback_Adhoc_Ingest Task to re-ingest a specific date range.
    Dates must be ISO format YYYY-MM-DD strings.
    Dates are passed as URL query params (pipeline parameters _start_date / _end_date).
    """
    bearer   = os.environ.get("SL_ADHOC_BEARER", "")
    endpoint = os.environ.get("SL_ADHOC_ENDPOINT", "")
    if not (bearer and endpoint):
        return {"error": "SL_ADHOC_BEARER / SL_ADHOC_ENDPOINT not configured"}
    resp = requests.post(
        endpoint,
        params={"start_date": start_date, "end_date": end_date},
        json={"start_date": start_date, "end_date": end_date},
        headers={"Authorization": f"Bearer {bearer}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def load_executions_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Load pipeline execution data directly from a CSV export (e.g. from the
    SL_Runtime_Events_To_Snowflake pipeline).  Normalises column names,
    derives project_space from PATH, and casts types to match the Snowflake
    schema so the rest of the app sees an identical DataFrame.
    """
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]

    if "start_time" in df.columns:
        df["start_time"] = pd.to_datetime(df["start_time"], utc=True, errors="coerce")
    if "end_time" in df.columns:
        df["end_time"] = pd.to_datetime(df["end_time"], utc=True, errors="coerce")
    if "duration_sec" not in df.columns and "duration" in df.columns:
        df["duration_sec"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0) / 1000.0

    # Cap per-execution duration at 60 min — always-on listener pipelines can span
    # days and would otherwise dominate cost allocation.
    df["duration_sec"] = pd.to_numeric(df["duration_sec"], errors="coerce").fillna(0).clip(upper=3600)

    # Derive project_space from the path column if not already present
    if "project_space" not in df.columns and "path" in df.columns:
        def _extract_ps(p):
            parts = str(p).strip("/").split("/")
            return parts[1] if len(parts) > 1 else (parts[0] if parts else "")
        df["project_space"] = df["path"].apply(_extract_ps)

    for col in ["label", "path", "runtime_path_id", "status",
                "document_count", "error_documents", "invoker", "user_id", "project_space", "end_time"]:
        if col not in df.columns:
            df[col] = "" if col not in ("document_count", "error_documents", "end_time") else (0 if col != "end_time" else pd.NaT)

    return df


def load_executions_via_pipeline(year: int = None, month: int = None,
                                  timeout: int = 120) -> pd.DataFrame:
    """
    Trigger SL_Runtime_Events_From_Snowflake Task and return all execution records.
    New pipeline takes no parameters — returns the full dataset in one call.
    """
    bearer   = os.environ["SL_READ_BEARER"]
    endpoint = os.environ["SL_READ_ENDPOINT"]

    resp = requests.get(
        endpoint,
        headers={"Authorization": f"Bearer {bearer}"},
        timeout=timeout,
    )
    resp.raise_for_status()

    data = resp.json()

    # SnapLogic triggered task wraps SnowflakeExecute output as:
    # [{"ResultQuery": [{row}, ...]}]
    if isinstance(data, list):
        if data and "ResultQuery" in data[0]:
            rows = data[0]["ResultQuery"]
        else:
            rows = data
    elif isinstance(data, dict):
        rows = (
            data.get("response_map", {}).get("entries")
            or data.get("entries")
            or data.get("rows")
            or []
        )
    else:
        rows = []

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]

    if "start_time" in df.columns:
        df["start_time"] = pd.to_datetime(df["start_time"], utc=True, errors="coerce")
    if "duration_sec" not in df.columns and "duration" in df.columns:
        df["duration_sec"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0) / 1000.0
    for col in ["label", "path", "runtime_path_id", "status",
                "document_count", "error_documents", "invoker", "user_id", "project_space"]:
        if col not in df.columns:
            df[col] = "" if col not in ("document_count", "error_documents") else 0

    return df

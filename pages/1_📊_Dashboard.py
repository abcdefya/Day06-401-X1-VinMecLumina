"""Observability Dashboard - partial live updates with hallucination monitoring."""

from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lumina Dashboard", page_icon="📊", layout="wide")
st.title("📊 Observability Dashboard")

# SLO definitions
SLO_P95_LATENCY_MS = 5000
SLO_ERROR_RATE_PCT = 5.0
SLO_COST_USD_MONTHLY = 10.0
SLO_HALLUCINATION_RATE_PCT = 0.5

RUNBOOKS = {
    "High P95 Latency": "https://github.com/abcdefya/NhomX1-401-Day06/blob/main/docs/runbooks/high-latency.md",
    "High Error Rate": "https://github.com/abcdefya/NhomX1-401-Day06/blob/main/docs/runbooks/high-error-rate.md",
    "Cost Budget Alert": "https://github.com/abcdefya/NhomX1-401-Day06/blob/main/docs/runbooks/cost-budget.md",
    "High Hallucination Proxy Rate": "https://github.com/abcdefya/NhomX1-401-Day06/blob/main/docs/runbooks/hallucination-proxy.md",
}

METRICS_PATH = Path("metrics/metrics.jsonl")
CACHE_KEY = "dashboard_metrics_cache"


def _load_records_if_changed() -> tuple[list[dict], bool, pd.Timestamp | None]:
    try:
        from src.core.metrics_store import load_all
    except Exception:
        return [], False, None

    mtime = METRICS_PATH.stat().st_mtime if METRICS_PATH.exists() else 0.0
    cache = st.session_state.get(CACHE_KEY)
    has_changed = cache is None or cache.get("mtime") != mtime

    if has_changed:
        try:
            records = load_all()
        except Exception:
            records = []
        cache = {
            "mtime": mtime,
            "records": records,
            "loaded_at": pd.Timestamp.now(),
        }
        st.session_state[CACHE_KEY] = cache

    cache = st.session_state.get(CACHE_KEY, {"records": [], "loaded_at": None})
    return cache.get("records", []), has_changed, cache.get("loaded_at")


def _prepare_frames(records: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.DataFrame(records)
    if "event" not in df.columns:
        df["event"] = "workflow"

    df["ts"] = pd.to_datetime(df["ts"], unit="s", errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")

    ops_df = df[df["event"].isin(["workflow", "chat_turn"])].copy()
    feedback_df = df[df["event"] == "feedback"].copy()

    for col in ["latency_ms", "prompt_tokens", "completion_tokens", "total_tokens", "cost_usd"]:
        if col in ops_df.columns:
            ops_df[col] = pd.to_numeric(ops_df[col], errors="coerce")
        else:
            ops_df[col] = 0

    if "error" not in ops_df.columns:
        ops_df["error"] = None
    ops_df["is_error"] = ops_df["error"].notna() & (ops_df["error"] != "None") & (ops_df["error"] != "")

    if "is_helpful" not in feedback_df.columns:
        feedback_df["is_helpful"] = False
    if "is_hallucination_proxy" not in feedback_df.columns:
        feedback_df["is_hallucination_proxy"] = ~feedback_df["is_helpful"].astype(bool)

    feedback_df["is_helpful"] = feedback_df["is_helpful"].fillna(False).astype(bool)
    feedback_df["is_hallucination_proxy"] = feedback_df["is_hallucination_proxy"].fillna(False).astype(bool)

    return df, ops_df, feedback_df


def _render_dashboard_body(records: list[dict], has_changed: bool, loaded_at: pd.Timestamp | None, auto_refresh: bool):
    if not records:
        st.info("No metrics yet. Run a workflow analysis from the main page first.")
        return

    df, ops_df, feedback_df = _prepare_frames(records)

    p95 = float(ops_df["latency_ms"].quantile(0.95)) if len(ops_df) else 0.0
    err_rate = float(ops_df["is_error"].mean() * 100) if len(ops_df) else 0.0
    total_cost = float(ops_df["cost_usd"].sum()) if len(ops_df) else 0.0

    feedback_total = int(len(feedback_df))
    halluc_rate = float(feedback_df["is_hallucination_proxy"].mean() * 100) if feedback_total else 0.0
    helpful_rate = float(feedback_df["is_helpful"].mean() * 100) if feedback_total else 0.0

    status_msg = "Live mode: waiting for new metric events"
    if has_changed:
        status_msg = "Live mode: new metric event detected"
    if not auto_refresh:
        status_msg = "Auto-refresh disabled"

    loaded_str = loaded_at.strftime("%Y-%m-%d %H:%M:%S") if loaded_at is not None else "N/A"
    st.caption(f"{status_msg} | Last data load: {loaded_str}")

    alerts_fired = []
    if p95 > SLO_P95_LATENCY_MS:
        alerts_fired.append(
            f"🔴 **High P95 Latency**: {p95:.0f} ms > {SLO_P95_LATENCY_MS} ms - [Runbook]({RUNBOOKS['High P95 Latency']})"
        )
    if err_rate > SLO_ERROR_RATE_PCT:
        alerts_fired.append(
            f"🔴 **High Error Rate**: {err_rate:.1f}% > {SLO_ERROR_RATE_PCT}% - [Runbook]({RUNBOOKS['High Error Rate']})"
        )
    if total_cost > SLO_COST_USD_MONTHLY:
        alerts_fired.append(
            f"🔴 **Cost Budget Alert**: ${total_cost:.2f} > ${SLO_COST_USD_MONTHLY} - [Runbook]({RUNBOOKS['Cost Budget Alert']})"
        )
    if feedback_total and halluc_rate > SLO_HALLUCINATION_RATE_PCT:
        alerts_fired.append(
            f"🔴 **High Hallucination Proxy Rate**: {halluc_rate:.2f}% > {SLO_HALLUCINATION_RATE_PCT}% - [Runbook]({RUNBOOKS['High Hallucination Proxy Rate']})"
        )

    if alerts_fired:
        for alert in alerts_fired:
            st.error(alert)
    else:
        st.success("✅ All SLOs healthy")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Requests", len(ops_df))
    c2.metric("P95 Latency", f"{p95:.0f} ms", delta=f"SLO {SLO_P95_LATENCY_MS} ms", delta_color="off")
    c3.metric("Error Rate", f"{err_rate:.1f}%", delta=f"SLO {SLO_ERROR_RATE_PCT}%", delta_color="off")
    c4.metric("Total Cost", f"${total_cost:.4f}", delta=f"Budget ${SLO_COST_USD_MONTHLY}", delta_color="off")
    c5.metric("Feedback Votes", feedback_total)
    c6.metric("Hallucination Proxy", f"{halluc_rate:.2f}%", delta=f"SLO {SLO_HALLUCINATION_RATE_PCT}%", delta_color="off")

    st.divider()

    st.subheader("1. Latency - P50 / P95 / P99")
    if not ops_df.empty:
        df_lat = ops_df.set_index("ts")[["latency_ms"]].copy()
        df_lat = df_lat.resample("1min").agg(
            P50=("latency_ms", lambda x: x.quantile(0.50)),
            P95=("latency_ms", lambda x: x.quantile(0.95)),
            P99=("latency_ms", lambda x: x.quantile(0.99)),
        ).dropna(how="all")
        df_lat["SLO_P95"] = SLO_P95_LATENCY_MS
        if not df_lat.empty:
            st.line_chart(df_lat, color=["#2196F3", "#FF9800", "#f44336", "#9E9E9E"])
        else:
            st.info("Not enough data for time-bucketed latency chart.")
    else:
        st.info("No request metrics yet.")

    st.subheader("2. Traffic - Requests per Minute")
    if not ops_df.empty:
        df_traffic = ops_df.set_index("ts").resample("1min").size().rename("requests_per_min").reset_index()
        if not df_traffic.empty:
            st.bar_chart(df_traffic.set_index("ts")["requests_per_min"])
        else:
            st.info("No traffic data yet.")
    else:
        st.info("No traffic data yet.")

    st.subheader("3. Error Rate (%)")
    if not ops_df.empty:
        df_err = ops_df.set_index("ts")[["is_error"]].resample("1min").agg(
            error_rate=("is_error", lambda x: x.mean() * 100)
        ).dropna()
        df_err["SLO_line"] = SLO_ERROR_RATE_PCT
        if not df_err.empty:
            st.line_chart(df_err, color=["#f44336", "#9E9E9E"])
        else:
            st.info("No error data yet.")
    else:
        st.info("No error data yet.")

    st.subheader("4. Cumulative Cost (USD)")
    if not ops_df.empty:
        df_cost = ops_df.set_index("ts")[["cost_usd"]].resample("1min").sum()
        df_cost["cumulative_cost"] = df_cost["cost_usd"].cumsum()
        df_cost["budget"] = SLO_COST_USD_MONTHLY
        st.line_chart(df_cost[["cumulative_cost", "budget"]], color=["#4CAF50", "#9E9E9E"])
    else:
        st.info("No cost data yet.")

    st.subheader("5. Token Usage - Prompt vs Completion")
    token_cols = [col for col in ["prompt_tokens", "completion_tokens"] if col in ops_df.columns]
    if not ops_df.empty and token_cols:
        df_tok = ops_df.set_index("ts")[token_cols].resample("1min").sum().dropna(how="all")
        if not df_tok.empty:
            st.bar_chart(df_tok, color=["#03A9F4", "#FF5722"])
        else:
            st.info("Not enough data for bucketed token chart.")
    else:
        st.info("No token data yet.")

    st.subheader("6. Hallucination Proxy Rate (from Useful/Not Useful feedback)")
    if feedback_total:
        df_hall = feedback_df.set_index("ts")[["is_hallucination_proxy"]].resample("1min").agg(
            hallucination_rate=("is_hallucination_proxy", lambda x: x.mean() * 100)
        ).dropna()
        df_hall["SLO_line"] = SLO_HALLUCINATION_RATE_PCT

        if not df_hall.empty:
            st.line_chart(df_hall[["hallucination_rate", "SLO_line"]], color=["#9C27B0", "#9E9E9E"])
        else:
            st.metric("Hallucination Proxy Rate", f"{halluc_rate:.2f}%")

        st.caption(
            f"Based on {feedback_total} explicit votes. Useful: {helpful_rate:.1f}% | Not useful (hallucination proxy): {halluc_rate:.1f}%."
        )
    else:
        st.info("No explicit feedback yet. Click Hữu ích / Không hữu ích on the main page to populate this panel.")

    with st.expander("Raw metrics data"):
        st.dataframe(df.sort_values("ts", ascending=False).head(200), use_container_width=True)


with st.sidebar:
    st.markdown("### ⚙️ Dashboard settings")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_seconds = st.slider("Refresh interval (seconds)", min_value=2, max_value=60, value=2, step=1)
    if st.button("🔄 Refresh now"):
        st.rerun()

    st.caption("When auto-refresh is on, only the metrics block reruns (not full page reload).")
    st.divider()

    st.markdown("### 🚨 Alert Rules")
    st.markdown(
        f"""
| Alert | Threshold | Runbook |
|-------|-----------|---------|
| High P95 Latency | > {SLO_P95_LATENCY_MS} ms | [Link]({RUNBOOKS['High P95 Latency']}) |
| High Error Rate | > {SLO_ERROR_RATE_PCT} % | [Link]({RUNBOOKS['High Error Rate']}) |
| Cost Budget | > ${SLO_COST_USD_MONTHLY}/month | [Link]({RUNBOOKS['Cost Budget Alert']}) |
| Hallucination Proxy | > {SLO_HALLUCINATION_RATE_PCT} % | [Link]({RUNBOOKS['High Hallucination Proxy Rate']}) |
"""
    )

    st.divider()
    st.markdown("### 📋 SLO Table")
    st.markdown(
        f"""
| SLO | Target | Runbook |
|-----|--------|---------|
| P95 Latency | < {SLO_P95_LATENCY_MS} ms | [Runbook]({RUNBOOKS['High P95 Latency']}) |
| Error Rate | < {SLO_ERROR_RATE_PCT} % | [Runbook]({RUNBOOKS['High Error Rate']}) |
| Monthly Cost | < ${SLO_COST_USD_MONTHLY} | [Runbook]({RUNBOOKS['Cost Budget Alert']}) |
| Hallucination Proxy | < {SLO_HALLUCINATION_RATE_PCT} % | [Runbook]({RUNBOOKS['High Hallucination Proxy Rate']}) |
"""
    )


if auto_refresh:
    @st.fragment(run_every=refresh_seconds)
    def _live_metrics_fragment():
        records, has_changed, loaded_at = _load_records_if_changed()
        _render_dashboard_body(records, has_changed, loaded_at, auto_refresh=True)

    _live_metrics_fragment()
else:
    records, has_changed, loaded_at = _load_records_if_changed()
    _render_dashboard_body(records, has_changed, loaded_at, auto_refresh=False)

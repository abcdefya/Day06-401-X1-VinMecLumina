"""Observability Dashboard — 6-panel metrics view with SLO lines."""
import time
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Lumina Dashboard", page_icon="📊", layout="wide")
st.title("📊 Observability Dashboard")

# ── SLO definitions ──────────────────────────────────────────────────────────
SLO_P95_LATENCY_MS = 5000   # P95 latency < 5000 ms
SLO_ERROR_RATE_PCT = 5.0    # Error rate < 5 %
SLO_COST_USD_MONTHLY = 10.0 # Monthly cost < $10

RUNBOOKS = {
    "High P95 Latency":  "https://github.com/your-org/lumina/wiki/Runbook-High-Latency",
    "High Error Rate":   "https://github.com/your-org/lumina/wiki/Runbook-High-Error-Rate",
    "Cost Budget Alert": "https://github.com/your-org/lumina/wiki/Runbook-Cost-Budget",
}

# ── Auto-refresh ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Dashboard settings")
    auto_refresh = st.checkbox("Auto-refresh (30 s)", value=False)
    if st.button("🔄 Refresh now"):
        st.rerun()
    st.divider()
    st.markdown("### 🚨 Alert Rules")
    st.markdown(f"""
| Alert | Threshold | Runbook |
|-------|-----------|---------|
| High P95 Latency | > {SLO_P95_LATENCY_MS} ms | [Link]({RUNBOOKS['High P95 Latency']}) |
| High Error Rate | > {SLO_ERROR_RATE_PCT} % | [Link]({RUNBOOKS['High Error Rate']}) |
| Cost Budget | > ${SLO_COST_USD_MONTHLY}/month | [Link]({RUNBOOKS['Cost Budget Alert']}) |
""")
    st.divider()
    st.markdown("### 📋 SLO Table")
    st.markdown(f"""
| SLO | Target | Runbook |
|-----|--------|---------|
| P95 Latency | < {SLO_P95_LATENCY_MS} ms | [Runbook]({RUNBOOKS['High P95 Latency']}) |
| Error Rate | < {SLO_ERROR_RATE_PCT} % | [Runbook]({RUNBOOKS['High Error Rate']}) |
| Monthly Cost | < ${SLO_COST_USD_MONTHLY} | [Runbook]({RUNBOOKS['Cost Budget Alert']}) |
""")

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    from src.core.metrics_store import load_all
    records = load_all()
except Exception:
    records = []

if not records:
    st.info("No metrics yet. Run a workflow analysis from the main page first, then refresh.")
    st.stop()

df = pd.DataFrame(records)
df["ts"] = pd.to_datetime(df["ts"], unit="s")
df = df.sort_values("ts")

# Convenience columns
df["is_error"] = df["error"].notna() & (df["error"] != "None") & (df["error"] != "")

# ── Alert banners ─────────────────────────────────────────────────────────────
p95 = df["latency_ms"].quantile(0.95) if len(df) else 0
err_rate = df["is_error"].mean() * 100 if len(df) else 0
total_cost = df["cost_usd"].sum() if "cost_usd" in df.columns else 0

alerts_fired = []
if p95 > SLO_P95_LATENCY_MS:
    alerts_fired.append(f"🔴 **High P95 Latency**: {p95:.0f} ms > {SLO_P95_LATENCY_MS} ms — [Runbook]({RUNBOOKS['High P95 Latency']})")
if err_rate > SLO_ERROR_RATE_PCT:
    alerts_fired.append(f"🔴 **High Error Rate**: {err_rate:.1f}% > {SLO_ERROR_RATE_PCT}% — [Runbook]({RUNBOOKS['High Error Rate']})")
if total_cost > SLO_COST_USD_MONTHLY:
    alerts_fired.append(f"🔴 **Cost Budget Alert**: ${total_cost:.2f} > ${SLO_COST_USD_MONTHLY} — [Runbook]({RUNBOOKS['Cost Budget Alert']})")

if alerts_fired:
    for a in alerts_fired:
        st.error(a)
else:
    st.success("✅ All SLOs healthy")

# ── Summary KPIs ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Requests", len(df))
c2.metric("P95 Latency", f"{p95:.0f} ms", delta=f"SLO {SLO_P95_LATENCY_MS} ms", delta_color="off")
c3.metric("Error Rate", f"{err_rate:.1f}%", delta=f"SLO {SLO_ERROR_RATE_PCT}%", delta_color="off")
c4.metric("Total Cost", f"${total_cost:.4f}", delta=f"Budget ${SLO_COST_USD_MONTHLY}", delta_color="off")

st.divider()

# ── Panel 1: Latency P50 / P95 / P99 over time ───────────────────────────────
st.subheader("1. Latency — P50 / P95 / P99")
df_lat = df.set_index("ts")[["latency_ms"]].copy()
df_lat = df_lat.resample("1min").agg(
    P50=("latency_ms", lambda x: x.quantile(0.50)),
    P95=("latency_ms", lambda x: x.quantile(0.95)),
    P99=("latency_ms", lambda x: x.quantile(0.99)),
).dropna(how="all")

# Add SLO reference line as a constant series
df_lat["SLO_P95"] = SLO_P95_LATENCY_MS

if not df_lat.empty:
    st.line_chart(df_lat, color=["#2196F3", "#FF9800", "#f44336", "#9E9E9E"])
else:
    st.info("Not enough data for time-bucketed latency chart.")
    st.bar_chart(df[["latency_ms"]].rename(columns={"latency_ms": "Latency (ms)"}))

# ── Panel 2: Traffic / QPS ────────────────────────────────────────────────────
st.subheader("2. Traffic — Requests per Minute")
df_traffic = df.set_index("ts").resample("1min").size().rename("requests_per_min").reset_index()
if not df_traffic.empty:
    st.bar_chart(df_traffic.set_index("ts")["requests_per_min"])
else:
    st.info("No traffic data yet.")

# ── Panel 3: Error Rate over time ─────────────────────────────────────────────
st.subheader("3. Error Rate (%)")
df_err = df.set_index("ts")[["is_error"]].resample("1min").agg(
    error_rate=("is_error", lambda x: x.mean() * 100)
).dropna()
df_err["SLO_line"] = SLO_ERROR_RATE_PCT
if not df_err.empty:
    st.line_chart(df_err, color=["#f44336", "#9E9E9E"])
else:
    st.info("No error data yet.")

# ── Panel 4: Cost over time (cumulative) ──────────────────────────────────────
st.subheader("4. Cumulative Cost (USD)")
if "cost_usd" in df.columns:
    df_cost = df.set_index("ts")[["cost_usd"]].resample("1min").sum()
    df_cost["cumulative_cost"] = df_cost["cost_usd"].cumsum()
    df_cost["budget"] = SLO_COST_USD_MONTHLY
    st.line_chart(df_cost[["cumulative_cost", "budget"]], color=["#4CAF50", "#9E9E9E"])
else:
    st.info("No cost data yet.")

# ── Panel 5: Tokens In / Out ──────────────────────────────────────────────────
st.subheader("5. Token Usage — Prompt vs Completion")
token_cols = [c for c in ["prompt_tokens", "completion_tokens"] if c in df.columns]
if token_cols:
    df_tok = df.set_index("ts")[token_cols].resample("1min").sum().dropna(how="all")
    if not df_tok.empty:
        st.bar_chart(df_tok, color=["#03A9F4", "#FF5722"])
    else:
        st.info("Not enough data for bucketed token chart.")
        st.bar_chart(df[token_cols].sum().rename("tokens").to_frame().T)
else:
    st.info("No token data yet.")

# ── Panel 6: Quality Proxy — Critical alert rate ──────────────────────────────
st.subheader("6. Quality Proxy — Critical Alert Rate")
if "is_critical" in df.columns:
    df_qual = df.set_index("ts")[["is_critical"]].resample("1min").agg(
        critical_rate=("is_critical", lambda x: x.mean() * 100)
    ).dropna()
    if not df_qual.empty:
        st.line_chart(df_qual, color=["#9C27B0"])
    else:
        critical_pct = df["is_critical"].mean() * 100
        st.metric("Critical Alert Rate", f"{critical_pct:.1f}%")
else:
    st.info("No quality data yet.")

# ── Raw data expander ─────────────────────────────────────────────────────────
with st.expander("Raw metrics data"):
    st.dataframe(df.sort_values("ts", ascending=False).head(100), use_container_width=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(30)
    st.rerun()

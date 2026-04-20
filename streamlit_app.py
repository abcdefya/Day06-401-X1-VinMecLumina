"""Streamlit UI for Vinmec Lumina API — stress-test & response viewer."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st

# ── defaults ────────────────────────────────────────────────────────────────

DEFAULT_ANALYZE_BODY = {
    "patient_id": "P001",
    "initial_state": None,
    "llm_provider": "azure",
    "create_conversation": True,
}

DEFAULT_CHAT_BODY = {
    "message": "Xin chào, kết quả xét nghiệm của tôi như thế nào?",
    "conversation_id": None,
    "patient_id": "P001",
    "workflow_result": None,
    "llm_provider": "azure",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _post(url: str, body: dict, api_key: str, timeout: int) -> dict:
    t0 = time.perf_counter()
    try:
        resp = requests.post(
            url,
            json=body,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        return {"status_code": resp.status_code, "elapsed_ms": elapsed, "body": data}
    except requests.exceptions.RequestException as exc:
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        return {"status_code": None, "elapsed_ms": elapsed, "body": {"error": str(exc)}}


def _run_stress(url: str, body: dict, api_key: str, n: int, workers: int, timeout: int) -> list[dict]:
    results: list[dict] = [None] * n  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_post, url, body, api_key, timeout): i for i in range(n)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
    return results


def _status_badge(code: int | None) -> str:
    if code is None:
        return "🔴 Error"
    if 200 <= code < 300:
        return f"🟢 {code}"
    if 400 <= code < 500:
        return f"🟡 {code}"
    return f"🔴 {code}"


# ── layout ───────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Vinmec Lumina — API Tester", layout="wide")
st.title("Vinmec Lumina API Tester")

# Sidebar — connection settings
with st.sidebar:
    st.header("Connection")
    base_url = st.text_input("Base URL", value="http://localhost:8000")
    api_key = st.text_input("X-API-Key", value="", type="password")
    timeout = st.number_input("Timeout (s)", min_value=1, max_value=120, value=30)

    st.divider()
    st.header("Stress Test")
    n_requests = st.number_input("Number of requests", min_value=1, max_value=500, value=1)
    max_workers = st.number_input("Parallel workers", min_value=1, max_value=50, value=5)

# Tabs
tab_analyze, tab_chat = st.tabs(["📊 Analyze", "💬 Chat"])


# ── /api/v1/analyze ───────────────────────────────────────────────────────────

with tab_analyze:
    st.subheader("POST /api/v1/analyze")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("**Request body (JSON)**")
        analyze_raw = st.text_area(
            label="analyze_body",
            value=json.dumps(DEFAULT_ANALYZE_BODY, indent=2, ensure_ascii=False),
            height=260,
            label_visibility="collapsed",
        )

        run_analyze = st.button("Send", key="btn_analyze", type="primary")

    with col_right:
        st.markdown("**Responses**")
        analyze_placeholder = st.empty()

    if run_analyze:
        try:
            body = json.loads(analyze_raw)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            st.stop()

        url = f"{base_url.rstrip('/')}/api/v1/analyze"
        with st.spinner(f"Sending {n_requests} request(s)…"):
            results = _run_stress(url, body, api_key, n_requests, max_workers, timeout)

        with analyze_placeholder.container():
            ok = sum(1 for r in results if r and r["status_code"] == 200)
            elapsed_vals = [r["elapsed_ms"] for r in results if r]
            avg_ms = round(sum(elapsed_vals) / len(elapsed_vals), 1) if elapsed_vals else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Total", n_requests)
            m2.metric("Success", ok)
            m3.metric("Avg latency", f"{avg_ms} ms")

            for i, res in enumerate(results):
                with st.expander(
                    f"Request {i + 1} — {_status_badge(res['status_code'])}  ({res['elapsed_ms']} ms)",
                    expanded=(n_requests == 1),
                ):
                    st.json(res["body"])


# ── /api/v1/chat ──────────────────────────────────────────────────────────────

with tab_chat:
    st.subheader("POST /api/v1/chat")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("**Request body (JSON)**")
        chat_raw = st.text_area(
            label="chat_body",
            value=json.dumps(DEFAULT_CHAT_BODY, indent=2, ensure_ascii=False),
            height=260,
            label_visibility="collapsed",
        )

        run_chat = st.button("Send", key="btn_chat", type="primary")

    with col_right:
        st.markdown("**Responses**")
        chat_placeholder = st.empty()

    if run_chat:
        try:
            body = json.loads(chat_raw)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            st.stop()

        url = f"{base_url.rstrip('/')}/api/v1/chat"
        with st.spinner(f"Sending {n_requests} request(s)…"):
            results = _run_stress(url, body, api_key, n_requests, max_workers, timeout)

        with chat_placeholder.container():
            ok = sum(1 for r in results if r and r["status_code"] == 200)
            elapsed_vals = [r["elapsed_ms"] for r in results if r]
            avg_ms = round(sum(elapsed_vals) / len(elapsed_vals), 1) if elapsed_vals else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Total", n_requests)
            m2.metric("Success", ok)
            m3.metric("Avg latency", f"{avg_ms} ms")

            for i, res in enumerate(results):
                label = f"Request {i + 1} — {_status_badge(res['status_code'])}  ({res['elapsed_ms']} ms)"
                with st.expander(label, expanded=(n_requests == 1)):
                    body_data = res["body"]
                    # Surface the reply prominently when it's a successful chat response
                    if res["status_code"] == 200 and "reply" in body_data:
                        st.markdown(f"**Reply:** {body_data['reply']}")
                        if "history" in body_data:
                            with st.expander("Conversation history", expanded=False):
                                st.json(body_data["history"])
                        st.caption(f"conversation_id: {body_data.get('conversation_id', '—')}")
                    else:
                        st.json(body_data)

# lumina_app.py — Merged 3-Tab Streamlit App Design

**Date:** 2026-04-20
**Status:** Approved

## Summary

Merge `app.py`, `streamlit_app.py`, and `pages/1_📊_Dashboard.py` into a single
`lumina_app.py` with three tabs. All AI responses go through the FastAPI server
(HTTP); local mock-patient data and the metrics file are still read directly.
Old files are kept as-is (no deletions).

---

## Architecture

```
lumina_app.py
├── Sidebar (shared across tabs)
│   ├── Connection: Base URL, API Key (password), Timeout
│   ├── LLM Provider: Azure OpenAI / Groq
│   ├── Patient selector  (Tab 2)
│   ├── Stress test: N requests, parallel workers  (Tab 3)
│   └── Dashboard: auto-refresh toggle, interval slider  (Tab 1)
└── st.tabs(["📊 Dashboard", "💬 UI Chat", "🔧 Stress Test"])
    ├── Tab 1: Dashboard
    ├── Tab 2: UI Chat
    └── Tab 3: Stress Test
```

---

## Tab 1 — Dashboard

Lifted verbatim from `pages/1_📊_Dashboard.py`.

- Reads `metrics/metrics.jsonl` directly via `src.core.metrics_store.load_all()`.
- Live auto-refresh via `@st.fragment(run_every=N)`.
- SLO cards: P95 latency, error rate, total cost, hallucination proxy rate.
- Alert banners when SLOs are breached (with runbook links).
- Six charts: latency percentiles, traffic, error rate, cumulative cost,
  token usage, hallucination proxy rate.
- Raw data expander (last 200 rows).
- Sidebar controls (auto-refresh, interval) under a collapsible section.

---

## Tab 2 — UI Chat

Patient-facing analysis UI. All AI calls go through the FastAPI server.

### Components

1. **Patient card + lab table** — reads from `src.data.mock_patients` directly
   (no AI, no change needed).
2. **"Analyze with AI" button** — calls `POST /api/v1/analyze`:
   ```json
   { "patient_id": "...", "llm_provider": "...", "create_conversation": true }
   ```
   Stores `result` and `conversation_id` in session state.
3. **AI output panel** — renders severity badge, summary, per-test explanations,
   and suggestions from the API response.
4. **Feedback buttons (👍/👎)** — writes to `metrics/metrics.jsonl` via
   `src.core.metrics_store.record()` directly (observability only, not AI).
5. **Follow-up chat** — calls `POST /api/v1/chat`:
   ```json
   { "conversation_id": "...", "message": "...", "llm_provider": "..." }
   ```
   Uses `conversation_id` from session state; no local message history maintained.

### Session state keys

| Key | Set by | Used by |
|-----|--------|---------|
| `selected_patient_id` | Patient selector | Reset guard |
| `workflow_result` | Analyze button | AI output panel, feedback |
| `conversation_id` | Analyze response | Chat calls |
| `analysis_id` | Analyze button | Feedback dedup |
| `feedback_votes` | Feedback buttons | Disable after vote |
| `chat_display` | Chat input | Chat message display |

### Error handling

- API key missing or server down → show `st.error` with instructions.
- HTTP 4xx/5xx → surface status code and body in `st.error`.
- No successful analyze yet → chat input is hidden.

---

## Tab 3 — Stress Test

Lifted verbatim from `streamlit_app.py`.

- Two inner tabs: `📊 Analyze` (`POST /api/v1/analyze`) and `💬 Chat`
  (`POST /api/v1/chat`).
- JSON request body editors (text area, pre-filled with defaults).
- Send button → fires N parallel requests using `ThreadPoolExecutor`.
- Results: total / success count / avg latency metrics, then per-request
  expanders with status badge and response body.
- Shares Base URL, API Key, Timeout, N requests, and workers from the sidebar.

---

## Data flow summary

| Concern | Source |
|---------|--------|
| AI analysis | `POST /api/v1/analyze` (HTTP) |
| AI chat | `POST /api/v1/chat` (HTTP) |
| Patient data / lab table | `src.data.mock_patients` (local) |
| Observability metrics | `metrics/metrics.jsonl` (local file) |
| Feedback recording | `src.core.metrics_store.record()` (local) |

---

## Files affected

| File | Action |
|------|--------|
| `lumina_app.py` | **Create** (new entry point) |
| `app.py` | Keep (unchanged) |
| `streamlit_app.py` | Keep (unchanged) |
| `pages/1_📊_Dashboard.py` | Keep (unchanged) |

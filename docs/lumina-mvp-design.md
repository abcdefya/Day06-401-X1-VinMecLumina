# Vinmec Lumina — Phase 1 MVP Implementation Plan

**Team:** X1 | **Track:** Vinmec | **Date:** 2026-04-09  
**Timeline:** 1 day (8–10 hours coding) | **Team size:** 6

---

## 1. 🔧 Tech Stack Proposal (Pragmatic)

| Layer | Choice | Justification |
|---|---|---|
| **UI** | Streamlit | Zero boilerplate, Python-native, renders tables/colors/columns in minutes |
| **Workflow** | LangGraph | Already scaffolded in the repo; handles multi-step conditional flows cleanly |
| **LLM** | Claude Sonnet 4.6 (primary) / Groq Llama-3.3-70B (fallback) | Claude: higher quality medical language; Groq: free tier for cost safety |
| **LLM abstraction** | LangChain | Already in requirements; wraps both providers uniformly |
| **Data** | Python dicts / JSON files | No DB setup time; hardcoded mock is fine for 1-day demo |
| **Guardrails** | Pure Python rule layer | Deterministic red-flag check before LLM call; no extra library needed |
| **Env/Config** | python-dotenv | Already in repo |

**Why not RAG with vector DB?** For 3 panels of test data, inline KB injection in the system prompt is faster, more reliable, and eliminates infra setup time.

---

## 2. 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    STREAMLIT UI                      │
│  Sidebar: Patient selector (3 patients)              │
│  Main:    Lab results table (color-coded)            │
│           "Giải thích với AI" button                 │
│           AI Output panel (summary + severity card)  │
└────────────────────┬────────────────────────────────┘
                     │ patient_id + lab_results JSON
                     ▼
┌─────────────────────────────────────────────────────┐
│              LANGGRAPH WORKFLOW ENGINE               │
│                                                      │
│  START → [guard_node]                                │
│              ↓ (red flag? → ESCALATE path)           │
│          [severity_node]  ← rule-based Python        │
│              ↓                                       │
│          [explain_node]   ← LLM call                 │
│              ↓                                       │
│          [suggest_node]   ← LLM call                 │
│              ↓                                       │
│             END → ExplanationResult                  │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐   ┌─────────────────────────────┐
│   LLM LAYER     │   │       DATA LAYER             │
│ Claude / Groq   │   │ mock_patients.json           │
│ System prompt   │   │ mock_lab_results.json        │
│ Output parser   │   │ reference_ranges.py          │
│ Keyword filter  │   │ severity_rules.py            │
└─────────────────┘   │ lab_kb.py (inline KB text)  │
                      └─────────────────────────────┘
```

**Data flow:** `Select Patient → Load JSON → Guard check → Severity classify → LLM explain → LLM suggest → Render output`

---

## 3. 🔄 Core Workflows (3 selected)

### Workflow 1: Explain Result (highest priority — clearest AI value)

| Step | Detail |
|---|---|
| **Input** | `patient_profile` (age, sex, conditions) + `lab_results[]` (test_code, value, unit, ref_low, ref_high, flag) |
| **Processing** | LLM receives: patient context + each abnormal result + KB snippet for that test → generates plain-language explanation per result |
| **Output** | List of explanations ranked by severity; each item: test name, value, what it means, why it may be relevant to this patient |
| **UI** | Expandable accordion per test; abnormal ones open by default; green/yellow/red left-border color |

**Prompt strategy:** Single call with all abnormal items. Prompt enforces: "Explain in Vietnamese for a non-medical adult. Do NOT diagnose. Do NOT name diseases. Use hedging language."

---

### Workflow 2: Severity Classification (rule-based + LLM confirmation)

| Step | Detail |
|---|---|
| **Input** | Lab result values + reference ranges + patient age/sex |
| **Processing** | **Layer 1 (Python rule):** compare value to ref_low/ref_high and critical thresholds → assign NORMAL / WATCH / SEE_DOCTOR / CRITICAL. **Layer 2 (LLM):** only used to add 1-line human-readable rationale |
| **Output** | Overall severity badge for the report + per-result severity tag |
| **UI** | Large colored badge at top: 🟢 Bình thường / 🟡 Theo dõi / 🔴 Gặp bác sĩ / 🚨 KHẨN CẤP. Per-row tags in the table |

**Escalation rule:** If ANY result is CRITICAL → skip LLM explanation → show hard-coded red alert box with "Vui lòng gặp bác sĩ hoặc đến cơ sở y tế ngay." + disable normal flow.

---

### Workflow 3: Follow-up Suggestion (closes the loop)

| Step | Detail |
|---|---|
| **Input** | Overall severity label + list of abnormal tests + patient profile |
| **Processing** | LLM generates 1–3 concrete next steps from a constrained menu: theo dõi tại nhà / tái khám / xét nghiệm bổ sung / gặp bác sĩ chuyên khoa. No freestyle advice |
| **Output** | Numbered list of safe, actionable suggestions |
| **UI** | Card below the explanation panel with checklist-style items. Button: "Đặt lịch khám Vinmec" (mock link) |

**Constraint in prompt:** "Choose next steps ONLY from: [monitor at home, retest in X weeks, see GP, see specialist]. Do NOT recommend specific medications or treatments."

---

## 4. 🧠 AI Design

### Prompt Strategy

**System prompt (shared across all LLM nodes):**
```
Bạn là Lumina — trợ lý giải thích kết quả xét nghiệm của Vinmec.

GIỚI HẠN BẮT BUỘC:
- KHÔNG chẩn đoán bệnh, KHÔNG đặt tên bệnh
- KHÔNG tư vấn thuốc hoặc liều dùng
- Dùng ngôn ngữ dễ hiểu, tránh thuật ngữ y khoa phức tạp
- Luôn kèm gợi ý "tham khảo bác sĩ" khi không chắc chắn
- Nếu câu hỏi vượt phạm vi xét nghiệm, từ chối lịch sự

Bạn đang nói chuyện với bệnh nhân {name}, {age} tuổi, {sex}.
Tiền sử: {conditions}.
```

**Per-node prompts:** Explain node gets KB snippet + test values. Suggest node gets severity summary only.

### RAG Approach

No vector DB. `lab_kb.py` contains a Python dict: `test_code → {meaning, common_causes_high, common_causes_low, safe_next_step}` for 15 common tests (CBC, glucose, HbA1c, lipid panel, liver enzymes, creatinine). At call time, only the KB entries for the patient's abnormal tests are injected.

### Guardrails

| Layer | Implementation | Trigger |
|---|---|---|
| **Pre-LLM red flag** | Python: check value against `critical_low/critical_high` thresholds | Before any LLM call |
| **Pre-LLM scope check** | If 0 abnormal results → skip LLM → show "All results within normal range" | Before explain node |
| **Post-LLM keyword filter** | Regex scan output for banned terms: ["chẩn đoán", "bạn bị", "dùng thuốc", "kê đơn"] | After LLM response |
| **Confidence fallback** | If LLM output < 50 words or contains "tôi không chắc" → replace with template fallback message | After LLM response |

### Fallback Behavior

```python
FALLBACK_MESSAGE = """
Lumina chưa có đủ thông tin để giải thích chỉ số này một cách chính xác.
Vui lòng tham khảo trực tiếp với bác sĩ của bạn để được tư vấn phù hợp.
"""
```

---

## 5. 🎨 Demo UX Flow

```
Screen 1 — Landing / Patient Select
┌─────────────────────────────────────────────────────┐
│  🏥 Vinmec Lumina                        [Sidebar]  │
│  "Trợ lý giải thích kết quả xét nghiệm"            │
│                                          ● Nguyễn A  │
│                                          ○ Trần B    │
│                                          ○ Lê C      │
└─────────────────────────────────────────────────────┘
     ↓ Click patient

Screen 2 — Patient Profile + Lab Results Table
┌─────────────────────────────────────────────────────┐
│  👤 Nguyễn Thị A | 45 tuổi | Nữ                    │
│  Tiền sử: Đái tháo đường type 2                     │
│  Ngày xét nghiệm: 2026-04-08                        │
│                                                      │
│  Chỉ số        Kết quả   Tham chiếu    Trạng thái   │
│  ──────────────────────────────────────────────────  │
│  🔴 HbA1c      8.2%      4.0–5.6%     Cao           │
│  🟡 LDL-C      3.4       <3.0 mmol/L  Theo dõi      │
│  🟢 Creatinine 78        44–97 μmol/L Bình thường   │
│  ...                                                 │
│                                                      │
│         [ 🤖 Giải thích với AI ]                    │
└─────────────────────────────────────────────────────┘
     ↓ Click button → spinner "Lumina đang phân tích..."

Screen 3 — AI Output Panel (appears below)
┌─────────────────────────────────────────────────────┐
│  🔴 MỨC ĐỘ TỔNG QUÁT: GẶP BÁC SĨ                  │
│                                                      │
│  📋 Tóm tắt: 2 chỉ số cần chú ý, 1 cần theo dõi   │
│                                                      │
│  ▼ HbA1c — 8.2% (Cao)                              │
│    Chỉ số này phản ánh mức đường huyết trung bình   │
│    trong 3 tháng qua. Với bạn (tiền sử đái tháo     │
│    đường), kết quả này cho thấy đường huyết chưa    │
│    được kiểm soát tốt. Tham chiếu cho người khỏe    │
│    mạnh là 4–5.6%.                                  │
│                                                      │
│  ▼ LDL-C — 3.4 mmol/L (Theo dõi)                  │
│    Mỡ "xấu" hơi cao so với khuyến nghị...          │
│                                                      │
│  📌 Bước tiếp theo:                                 │
│    1. Tái khám và điều chỉnh phác đồ kiểm soát     │
│       đường huyết với bác sĩ nội tiết              │
│    2. Tái xét nghiệm HbA1c sau 3 tháng             │
│    3. Theo dõi chế độ ăn và vận động               │
│                                                      │
│    [ 📅 Đặt lịch Vinmec ]   [ 👍 ]  [ 👎 ]        │
└─────────────────────────────────────────────────────┘
```

**Critical path demo (Patient 3 — Lê Thị C):** Shows red KHẨN CẤP banner immediately without waiting for LLM — demonstrates the guard layer.

---

## 6. 🧪 Mock Data Design

### Patient Cases

**Patient 1 — Nguyễn Thị A (45F, DM Type 2) — Mildly Abnormal**
```json
{
  "patient_id": "P001",
  "name": "Nguyễn Thị A",
  "age": 45,
  "sex": "Nữ",
  "conditions": ["Đái tháo đường type 2"],
  "lab_results": [
    {"test_code": "HBA1C", "test_name": "HbA1c", "value": 8.2, "unit": "%",
     "ref_low": 4.0, "ref_high": 5.6, "flag": "HIGH"},
    {"test_code": "LDL", "test_name": "LDL Cholesterol", "value": 3.4, "unit": "mmol/L",
     "ref_low": null, "ref_high": 3.0, "flag": "HIGH"},
    {"test_code": "CREATININE", "test_name": "Creatinine", "value": 78, "unit": "μmol/L",
     "ref_low": 44, "ref_high": 97, "flag": "NORMAL"},
    {"test_code": "GLUCOSE_F", "test_name": "Glucose (đói)", "value": 9.1, "unit": "mmol/L",
     "ref_low": 3.9, "ref_high": 6.1, "flag": "HIGH"}
  ]
}
```

**Patient 2 — Trần Văn B (62M, Hypertension) — Normal**
```json
{
  "patient_id": "P002",
  "name": "Trần Văn B",
  "age": 62,
  "sex": "Nam",
  "conditions": ["Tăng huyết áp"],
  "lab_results": [
    {"test_code": "WBC", "test_name": "Bạch cầu", "value": 6.8, "unit": "×10⁹/L",
     "ref_low": 4.0, "ref_high": 10.0, "flag": "NORMAL"},
    {"test_code": "HGB", "test_name": "Hemoglobin", "value": 138, "unit": "g/L",
     "ref_low": 130, "ref_high": 170, "flag": "NORMAL"},
    {"test_code": "CREATININE", "test_name": "Creatinine", "value": 91, "unit": "μmol/L",
     "ref_low": 62, "ref_high": 106, "flag": "NORMAL"},
    {"test_code": "LDL", "test_name": "LDL Cholesterol", "value": 2.8, "unit": "mmol/L",
     "ref_low": null, "ref_high": 3.0, "flag": "NORMAL"}
  ]
}
```

**Patient 3 — Lê Thị C (38F, Pregnant 28 weeks) — CRITICAL**
```json
{
  "patient_id": "P003",
  "name": "Lê Thị C",
  "age": 38,
  "sex": "Nữ",
  "conditions": ["Đang mang thai tuần 28"],
  "lab_results": [
    {"test_code": "HGB", "test_name": "Hemoglobin", "value": 68, "unit": "g/L",
     "ref_low": 110, "ref_high": 160, "flag": "CRITICAL_LOW",
     "critical_low": 70},
    {"test_code": "WBC", "test_name": "Bạch cầu", "value": 18.5, "unit": "×10⁹/L",
     "ref_low": 4.0, "ref_high": 10.0, "flag": "HIGH"},
    {"test_code": "PLATELET", "test_name": "Tiểu cầu", "value": 89, "unit": "×10⁹/L",
     "ref_low": 150, "ref_high": 400, "flag": "LOW"},
    {"test_code": "AST", "test_name": "AST", "value": 245, "unit": "U/L",
     "ref_low": 0, "ref_high": 40, "flag": "HIGH"}
  ]
}
```

### Reference Ranges + Severity Rules (Python dict, `reference_ranges.py`)
```python
CRITICAL_THRESHOLDS = {
    "HGB": {"critical_low": 70, "critical_high": 200},
    "POTASSIUM": {"critical_low": 2.5, "critical_high": 6.0},
    "GLUCOSE_F": {"critical_low": 2.8, "critical_high": 25.0},
    "PLATELET": {"critical_low": 50, "critical_high": 1000},
}

SEVERITY_RULES = {
    "CRITICAL_LOW": "CRITICAL",
    "CRITICAL_HIGH": "CRITICAL",
    "HIGH": "SEE_DOCTOR" if deviation > 50% else "WATCH",
    "LOW": "SEE_DOCTOR" if deviation > 50% else "WATCH",
    "NORMAL": "NORMAL",
}
```

---

## 7. 👥 Task Breakdown for 6 People

| # | Person | Role | Responsibility | Expected Output | Dependencies |
|---|---|---|---|---|---|
| 1 | **Dương Khoa Điềm** | UI Lead (Streamlit) | Build all screens: patient selector sidebar, lab results table with colors, AI output panel layout, feedback buttons | `app.py` — full Streamlit UI skeleton that accepts Python dict inputs | Needs mock data format from Person 3 |
| 2 | **Hoàng Thị Thanh Tuyền** | AI Logic | Write system prompt, explain_node, suggest_node LLM calls, response parser, `lab_kb.py` | `src/nodes/explain_node.py`, `src/nodes/suggest_node.py`, `src/data/lab_kb.py` | Needs patient JSON format from Person 3 |
| 3 | **Đỗ Thế Anh** | Data + Mock API | Create 3 patient JSON files, `reference_ranges.py`, data loader functions, define shared data schema | `src/data/mock_patients.py`, `src/data/reference_ranges.py` | **FIRST to deliver** — others depend on this |
| 4 | **Nguyễn Hồ Bảo Thiên** | Guardrails + Rule Engine | Build `guard_node` (critical threshold check), `severity_node` (rule-based classification), post-LLM keyword filter | `src/nodes/guard_node.py`, `src/nodes/severity_node.py` | Needs critical thresholds from Person 3 |
| 5 | **Lê Minh Khang** | LangGraph Orchestration | Wire all nodes into LangGraph graph, define AgentState, handle routing (normal vs critical path), expose `run_workflow()` function | `src/workflow.py` — complete graph with all 4 nodes | Needs node signatures from Persons 2 and 4 |
| 6 | **Võ Thanh Chung** | Integration + Demo Polish | Connect UI to workflow, CSS styling (Vinmec colors), fix integration bugs, prepare demo script, final QA | `app.py` final, `demo_script.md`, CSS overrides | Needs working workflow from Person 5 and UI from Person 1 |

**Critical path:** Person 3 → Persons 2 & 4 (parallel) → Person 5 → Person 6 + Person 1 (parallel) → Done

---

## 8. ⏱️ Execution Timeline (1-day plan)

### Phase 1: Setup + Skeleton (8:00–10:00)
- **All:** `git pull`, install deps (`pip install streamlit`), set up `.env` with API keys
- **Person 3:** Define and share data schema/format (shared Slack message with sample JSON) — **by 8:30**
- **Person 1:** Scaffold `app.py` with Streamlit columns and placeholder sections
- **Person 6:** Verify existing LangGraph skeleton compiles, clean up dead imports in `agent.py`

### Phase 2: Core Features — Parallel (10:00–13:00)
- **Person 3:** Complete all mock data files + reference ranges
- **Person 2:** Build explain_node + lab_kb.py (test with direct LLM call first, no graph yet)
- **Person 4:** Build guard_node + severity_node (pure Python, testable standalone)
- **Person 1:** Build lab results table with color coding, patient profile card
- **Person 5:** Build LangGraph graph skeleton, connect nodes as they become available
- **Person 6:** Research Streamlit styling, plan integration approach

### Phase 3: Integration (13:00–16:00)
- **Person 5:** Complete graph wiring, expose `run_workflow(patient_id) → ExplanationResult`
- **Person 1 + 6:** Connect Streamlit button to workflow call, render AI output
- **Person 2 + 4:** Fix node bugs from integration testing
- **All:** Run end-to-end with all 3 patients, fix crashes

### Phase 4: Polish + Demo Prep (16:00–18:00)
- **Person 6:** CSS polish (Vinmec blue #0078BE), loading spinner, error messages
- **Person 1:** Finalize UX layout, add feedback buttons
- **Person 2:** Tune prompts based on actual outputs
- **All:** Rehearse demo flow with Patient 1 → 2 → 3 (normal → mildly abnormal → critical)
- **Person 6:** Write `demo_script.md` with talking points

### Buffer (if needed): 18:00–19:00
- Fix critical bugs only; NO new features

---

## 9. ⚠️ Scope Control

### MUST HAVE (Phase 1 MVP — non-negotiable)
- [ ] 3 sample patients selectable from sidebar
- [ ] Lab results table with color-coded flags (green/yellow/red)
- [ ] "Giải thích với AI" button → real LLM response
- [ ] Severity badge (NORMAL / THEO DÕI / GẶP BÁC SĨ / KHẨN CẤP)
- [ ] Per-test explanation in plain Vietnamese
- [ ] Follow-up suggestions (3 items)
- [ ] Critical value → hard-coded red alert (no LLM wait)
- [ ] Guardrail: no diagnosis/medication keywords in output
- [ ] Fallback message when LLM is uncertain

### OUT OF SCOPE (do NOT build)
- ❌ Real database / SQL / SQLite
- ❌ User authentication / login
- ❌ Trend analysis / historical comparison
- ❌ Multi-language (English only if needed for fallback)
- ❌ PDF export / report download
- ❌ Real-time data from hospital LIS/HIS
- ❌ Doctor review interface
- ❌ Feedback storage to DB
- ❌ Vector DB / proper RAG (use inline KB text)
- ❌ Docker / deployment pipeline
- ❌ Mobile responsive layout
- ❌ Multiple simultaneous users

### Scope creep warning signs
If anyone says "let's also add…" → redirect to backlog. Demo quality > feature count.

---

## Appendix: File Structure

```
Day06-401-X1-VinMecLumina/
├── app.py                          # Streamlit entrypoint
├── src/
│   ├── data/
│   │   ├── mock_patients.py        # 3 patient dicts
│   │   ├── reference_ranges.py     # thresholds + severity rules
│   │   └── lab_kb.py              # inline KB text per test_code
│   ├── nodes/
│   │   ├── guard_node.py          # critical check (pure Python)
│   │   ├── severity_node.py       # rule-based severity
│   │   ├── explain_node.py        # LLM explain call
│   │   └── suggest_node.py        # LLM suggest call
│   ├── workflow.py                # LangGraph graph assembly
│   └── models.py                  # Pydantic models (ExplanationResult etc.)
├── docs/
│   └── demo_script.md             # talking points for demo
└── .env                           # API keys (gitignored)
```

---

*"AI hiểu dữ liệu — Bác sĩ hiểu bệnh nhân."*

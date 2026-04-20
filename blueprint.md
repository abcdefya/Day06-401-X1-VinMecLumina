# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata

- [GROUP_NAME]: C401-X4
- [REPO_URL]: https://github.com/thiennguyen37-qn/NhomX4-401-Day13.git
- [MEMBERS]:
  - Member 1: Vo Thanh Chung | Role: Logging & PII
  - Member 2: Do The Anh | Role: Tracing & Enrichment
  - Member 3: Nguyen Ho Bao Thien | Role: SLO & Alerts
  - Member 4: Duong Khoa Diem | Role: Load Test & Dashboard
  - Member 5: Le Bao Khang | Role: Demo & Report
  - Member 6: Hoang Thi Thanh Tuyen | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)

- [VALIDATE_LOGS_FINAL_SCORE]: N/A (chua co file/artifact validator trong repo de suy ra diem /100)
- [TOTAL_TRACES_COUNT]: 26 (theo bo loc Tracing trong evidence screenshot ngay 2026-04-20)
- [PII_LEAKS_FOUND]: 0 (kiem tra log `logs/2026-04-20.log` thay `patient_id` da duoc redaction thanh `[PATIENT_ID]`)

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing

- [EVIDENCE_CORRELATION_ID_SCREENSHOT]:
- [EVIDENCE_PII_REDACTION_SCREENSHOT]:
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]:
- [TRACE_WATERFALL_EXPLANATION]: Trong waterfall, span Ä‘Ã¡ng chÃº Ã½ lÃ  chuá»—i child span `explain-HBA1C` -> `explain-LDL` -> `explain-GLUCOSE_F` dÆ°á»›i `lumina-workflow`. á»ž khoáº£ng `2026-04-20 22:17:08` Ä‘áº¿n `22:17:51`, cÃ¡c span `explain-*` lÃªn `Level = ERROR`, cho tháº¥y lá»—i xáº£y ra khi gá»i LLM Ä‘á»ƒ sinh diá»…n giáº£i cho tá»«ng xÃ©t nghiá»‡m. Tuy váº­y span cha `lumina-workflow` váº«n káº¿t thÃºc thÃ nh cÃ´ng (Ä‘á»‘i chiáº¿u log `logs/2026-04-20.log:4`, `correlation_id=f11e2e76-89ff-4b57-8aa7-71167f700d5c`, `error=null`) vÃ¬ `explain_node` cÃ³ cÆ¡ cháº¿ fallback deterministic khi LLM lá»—i. Insight chÃ­nh: há»‡ thá»‘ng Ä‘ang cÃ³ tÃ­nh chá»‹u lá»—i tá»‘t á»Ÿ má»©c workflow, nhÆ°ng cáº§n giÃ¡m sÃ¡t riÃªng error-rate cá»§a span `explain-*` Ä‘á»ƒ phÃ¡t hiá»‡n sá»›m suy giáº£m cháº¥t lÆ°á»£ng tráº£ lá»i.

### 3.2 Dashboard & SLOs

- [DASHBOARD_6_PANELS_SCREENSHOT]:
- [SLO_TABLE]:
  | SLI | Target | Window | Current Value |
  |---|---:|---|---:|
  | Latency P95 | < 3000ms | 28d | 24535ms |
  | Error Rate | < 2% | 28d | 0.00% |
  | Cost Budget | < $2.5/day | 1d | $0.2502/day |

### 3.3 Alerts & Runbook

- [ALERT_RULES_SCREENSHOT]:
- [SAMPLE_RUNBOOK_LINK]: `high_latency -> docs/runbooks/high-latency; high_error_rate -> docs/runbooks/high-error-rate; cost_budget -> docs/runbooks/cost-budget; hallucination_proxy -> docs/runbooks/hallucination-proxy`

---

## 4. Incident Response (Group)

- [SCENARIO_NAME]: `llm_tool_span_error_but_workflow_survives`
- [SYMPTOMS_OBSERVED]:
  - TrÃªn Tracing, cÃ¡c span `explain-HBA1C`, `explain-LDL`, `explain-GLUCOSE_F` xuáº¥t hiá»‡n `Level = ERROR` (khung thá»i gian khoáº£ng `2026-04-20 22:17:08` Ä‘áº¿n `22:17:51`).
  - Tuy nhiÃªn `lumina-workflow` váº«n hoÃ n táº¥t (khÃ´ng crash toÃ n luá»“ng), ngÆ°á»i dÃ¹ng váº«n nháº­n pháº£n há»“i nhÆ°ng cháº¥t lÆ°á»£ng cÃ³ lÃºc giáº£m (vÃ­ dá»¥ cÃ¢u tráº£ lá»i xin lá»—i/chung chung).
- [ROOT_CAUSE_PROVED_BY]:
  - **Trace evidence**: nhiá»u child span `explain-*` bá»‹ `ERROR` trong cÃ¹ng phiÃªn cháº¡y, cho tháº¥y lá»—i xáº£y ra táº¡i bÆ°á»›c gá»i LLM Ä‘á»ƒ giáº£i thÃ­ch tá»«ng chá»‰ sá»‘.
  - **Log evidence**: `logs/2026-04-20.log:4` cÃ³ `event=workflow.complete`, `correlation_id=f11e2e76-89ff-4b57-8aa7-71167f700d5c`, `latency_ms=57196`, `error=null` -> chá»©ng minh workflow chÃ­nh váº«n sá»‘ng nhá» cÆ¡ cháº¿ fallback.
  - **Code evidence**: `src/nodes/explain_node.py` báº¯t lá»—i trong `_llm_explanation(...)` vÃ  `pass` Ä‘á»ƒ giá»¯ deterministic fallback, nÃªn span con lá»—i nhÆ°ng workflow khÃ´ng fail.
- [FIX_ACTION]:
  - Cáº¥u hÃ¬nh/kiá»ƒm tra láº¡i provider LLM (API key, endpoint, háº¡n má»©c), Ä‘á»“ng thá»i báº­t fallback provider (`azure` <-> `groq`) khi má»™t nhÃ  cung cáº¥p lá»—i.
  - Bá»• sung logging chi tiáº¿t trong khá»‘i `except` cá»§a `explain_node` (ghi loáº¡i lá»—i + test_code + correlation_id) Ä‘á»ƒ truy váº¿t nhanh hÆ¡n thay vÃ¬ chá»‰ tháº¥y `ERROR` trÃªn trace.
- [PREVENTIVE_MEASURE]:
  - Thiáº¿t láº­p alert theo tá»· lá»‡ `ERROR` cá»§a span `explain-*` (vÃ­ dá»¥ >5% trong 5 phÃºt thÃ¬ cáº£nh bÃ¡o).
  - ThÃªm circuit breaker/retry cÃ³ backoff cho gá»i LLM theo tá»«ng test.
  - Theo dÃµi SLI riÃªng cho `explain-*` (error-rate, latency) vÃ  runbook xá»­ lÃ½ sá»± cá»‘ provider.

---

## 5. Individual Contributions & Evidence

### Vo Thanh Chung

- [TASKS_COMPLETED]: Logging/PII redaction, metrics va Langfuse tracing integration.
- [EVIDENCE_LINK]: https://github.com/thiennguyen37-qn/NhomX4-401-Day13/commit/53bc88a ;

### Do The Anh

- [TASKS_COMPLETED]: Tracing enrichment, thiet ke/cap nhat app flow va deploy config.
- [EVIDENCE_LINK]: https://github.com/thiennguyen37-qn/NhomX4-401-Day13/commit/6049b53 ;

### Nguyen Ho Bao Thien

- [TASKS_COMPLETED]: ÄÃ³ng gÃ³p cho SLO vÃ  Alerts flow.
- [EVIDENCE_LINK]:

### Duong Khoa Diem

- [TASKS_COMPLETED]: Testing, monitoring, theo dÃµi dashboard
- [EVIDENCE_LINK]:

### Le Bao Khang

- [TASKS_COMPLETED]: Dashboard/observability enhancement
- [EVIDENCE_LINK]: https://github.com/thiennguyen37-qn/NhomX4-401-Day13/commit/e195a62

### Hoang Thi Thanh Tuyen

- [TASKS_COMPLETED]: Runbook/hallucination updates, prototype va demo/report support.
- [EVIDENCE_LINK]:47056e9411e7928b9e8a22ccc5e020c9faf82fe2; https://github.com/thiennguyen37-qn/NhomX4-401-Day13/commit/8e4ee94;

---

# Vinmec Lab Result Explainer — Database Schema (No OCR)

---

## 1. Overview

Database phục vụ:
- Lưu hồ sơ bệnh nhân
- Lưu kết quả xét nghiệm (structured)
- Cung cấp context để AI giải thích
- Lưu output AI + feedback

**Không bao gồm OCR (chỉ dùng data structured từ hệ thống Vinmec)**

---

## 2. Entity Relationship (Simplified)

```text
PATIENTS
 ├── PATIENT_CONTEXT
 ├── ENCOUNTERS
 │     └── DIAGNOSTIC_REPORTS
 │            └── LAB_RESULTS
 │                   └── TEST_REFERENCE_RANGES
 └── AI_EXPLANATIONS
        └── AI_FEEDBACK
```

---

## 3. Tables

### 3.1 patients
Thông tin định danh bệnh nhân

| Field | Type | Description |
|---|---|---|
| patient_id | UUID PK | ID nội bộ |
| vinmec_mrn | VARCHAR | mã bệnh án |
| full_name | VARCHAR | họ tên |
| date_of_birth | DATE | ngày sinh |
| sex_at_birth | VARCHAR | giới tính |
| phone | VARCHAR | số điện thoại |
| email | VARCHAR | email |
| created_at | TIMESTAMP | tạo |
| updated_at | TIMESTAMP | cập nhật |

---

### 3.2 patient_profiles
Context cá nhân

| Field | Type | Description |
|---|---|---|
| profile_id | UUID PK |
| patient_id | UUID FK |
| height_cm | DECIMAL |
| weight_kg | DECIMAL |
| pregnancy_status | VARCHAR |
| preferred_language | VARCHAR |
| updated_at | TIMESTAMP |

---

### 3.3 patient_conditions
Tiền sử bệnh

| Field | Type | Description |
|---|---|---|
| condition_id | UUID PK |
| patient_id | UUID FK |
| condition_code | VARCHAR |
| condition_name | VARCHAR |
| status | VARCHAR |
| onset_date | DATE |
| notes | TEXT |
| source | VARCHAR |

---

### 3.4 patient_allergies
Dị ứng

| Field | Type | Description |
|---|---|---|
| allergy_id | UUID PK |
| patient_id | UUID FK |
| allergy_type | VARCHAR |
| substance_name | VARCHAR |
| reaction | VARCHAR |
| severity | VARCHAR |
| status | VARCHAR |
| noted_at | DATE |

---

### 3.5 patient_medications
Thuốc nền

| Field | Type | Description |
|---|---|---|
| medication_id | UUID PK |
| patient_id | UUID FK |
| medication_name | VARCHAR |
| dose | VARCHAR |
| frequency | VARCHAR |
| route | VARCHAR |
| start_date | DATE |
| end_date | DATE |
| status | VARCHAR |

---

### 3.6 patient_lifestyle
Lifestyle

| Field | Type | Description |
|---|---|---|
| lifestyle_id | UUID PK |
| patient_id | UUID FK |
| nutrition_note | TEXT |
| fluid_intake_level | VARCHAR |
| smoking_status | VARCHAR |
| sleep_hours_avg | DECIMAL |
| physical_activity_level | VARCHAR |
| mental_health_note | TEXT |
| updated_at | TIMESTAMP |

---

## 4. Lab Data

### 4.1 encounters

| Field | Type |
|---|---|
| encounter_id | UUID PK |
| patient_id | UUID FK |
| encounter_type | VARCHAR |
| department | VARCHAR |
| encounter_datetime | TIMESTAMP |
| practitioner_id | VARCHAR |
| notes | TEXT |

---

### 4.2 diagnostic_reports

| Field | Type |
|---|---|
| report_id | UUID PK |
| patient_id | UUID FK |
| encounter_id | UUID FK |
| report_code | VARCHAR |
| report_name | VARCHAR |
| source_system | VARCHAR |
| report_status | VARCHAR |
| collected_at | TIMESTAMP |
| reported_at | TIMESTAMP |
| lab_name | VARCHAR |
| file_url | TEXT |
| is_structured | BOOLEAN |

---

### 4.3 lab_test_catalog

| Field | Type |
|---|---|
| test_code | VARCHAR PK |
| test_name | VARCHAR |
| short_name | VARCHAR |
| category | VARCHAR |
| specimen_type | VARCHAR |
| unit_default | VARCHAR |
| description_patient_friendly | TEXT |
| critical_low_threshold | DECIMAL |
| critical_high_threshold | DECIMAL |
| active | BOOLEAN |

---

### 4.4 test_reference_ranges

| Field | Type |
|---|---|
| range_id | UUID PK |
| test_code | VARCHAR FK |
| sex_at_birth | VARCHAR |
| age_min | INT |
| age_max | INT |
| pregnancy_status | VARCHAR |
| unit | VARCHAR |
| ref_low | DECIMAL |
| ref_high | DECIMAL |
| critical_low | DECIMAL |
| critical_high | DECIMAL |
| source_guideline | VARCHAR |

---

### 4.5 lab_results

| Field | Type |
|---|---|
| result_id | UUID PK |
| report_id | UUID FK |
| patient_id | UUID FK |
| test_code | VARCHAR FK |
| test_name_raw | VARCHAR |
| result_value_numeric | DECIMAL |
| result_value_text | VARCHAR |
| unit | VARCHAR |
| ref_low | DECIMAL |
| ref_high | DECIMAL |
| abnormal_flag | VARCHAR |
| analyzer_name | VARCHAR |
| measured_at | TIMESTAMP |
| source_type | VARCHAR |
| confidence_score | DECIMAL |
| raw_row_text | TEXT |

---

## 5. AI Layer

### 5.1 ai_explanations

| Field | Type |
|---|---|
| explanation_id | UUID PK |
| patient_id | UUID FK |
| report_id | UUID FK |
| request_type | VARCHAR |
| context_snapshot_json | JSONB |
| model_name | VARCHAR |
| prompt_version | VARCHAR |
| output_summary | TEXT |
| output_severity | VARCHAR |
| output_next_step | TEXT |
| confidence_band | VARCHAR |
| fallback_triggered | BOOLEAN |
| created_at | TIMESTAMP |

---

### 5.2 ai_explanation_items

| Field | Type |
|---|---|
| item_id | UUID PK |
| explanation_id | UUID FK |
| result_id | UUID FK |
| explanation_text | TEXT |
| priority_rank | INT |
| used_patient_context | BOOLEAN |

---

### 5.3 ai_feedback

| Field | Type |
|---|---|
| feedback_id | UUID PK |
| explanation_id | UUID FK |
| patient_id | UUID FK |
| feedback_type | VARCHAR |
| feedback_text | TEXT |
| action_taken | VARCHAR |
| created_at | TIMESTAMP |

---

### 5.4 doctor_review_flags

| Field | Type |
|---|---|
| review_id | UUID PK |
| explanation_id | UUID FK |
| reviewer_role | VARCHAR |
| safety_flag | VARCHAR |
| issue_type | VARCHAR |
| comments | TEXT |
| reviewed_at | TIMESTAMP |

---

## 6. Rule & Knowledge

### 6.1 severity_rules

| Field | Type |
|---|---|
| rule_id | UUID PK |
| test_code | VARCHAR FK |
| condition_expr | TEXT |
| severity_label | VARCHAR |
| patient_context_required | VARCHAR |
| action_text | TEXT |
| active | BOOLEAN |
| priority_order | INT |

---

### 6.2 lab_explanation_kb

| Field | Type |
|---|---|
| kb_id | UUID PK |
| test_code | VARCHAR FK |
| panel_code | VARCHAR |
| patient_friendly_meaning | TEXT |
| common_causes_high | TEXT |
| common_causes_low | TEXT |
| safe_next_step | TEXT |
| red_flag_note | TEXT |
| language | VARCHAR |
| version | VARCHAR |
| approved_by | VARCHAR |
| approved_at | TIMESTAMP |

---

## 7. Core Relationships

- patients 1:N diagnostic_reports
- diagnostic_reports 1:N lab_results
- lab_test_catalog 1:N lab_results
- lab_test_catalog 1:N test_reference_ranges
- patients 1:N ai_explanations
- ai_explanations 1:N ai_feedback

---

## 8. Minimal version (for prototype)

If cần demo nhanh:

- patients
- patient_conditions
- diagnostic_reports
- lab_results
- lab_test_catalog
- test_reference_ranges
- ai_explanations

---

## 9. One-line summary

**Structured lab data + patient context → AI explanation → feedback loop**


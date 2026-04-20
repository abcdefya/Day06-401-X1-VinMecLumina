import streamlit as st

from src.data.mock_patients import get_all_patients, get_patient
from src.data.reference_ranges import classify_severity
from src.services.models import LabResult, ResultFlag
from src.agents.agent import run_workflow

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Vinmec Lumina", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0a1628; }
    [data-testid="stSidebar"] * { color: #e0e6ed !important; }
    .lab-table { width: 100%; border-collapse: collapse; font-size: 0.97rem; }
    .lab-table th {
        background-color: #0078BE; color: white;
        padding: 10px 14px; text-align: left;
    }
    .lab-table td { padding: 9px 14px; border-bottom: 1px solid #e8ecf1; }
    .row-normal   { background-color: rgba(46,204,113,0.08); }
    .row-watch    { background-color: rgba(243,156,18,0.12); }
    .row-see-doc  { background-color: rgba(231,76,60,0.12); }
    .row-critical { background-color: rgba(192,57,43,0.18); }
    .badge {
        display: inline-block; padding: 6px 18px; border-radius: 20px;
        font-weight: 700; font-size: 1.05rem; margin-bottom: 8px;
    }
    .badge-normal   { background: #d5f5e3; color: #1a7a45; }
    .badge-watch    { background: #fef9e7; color: #b7770d; }
    .badge-see-doc  { background: #fdecea; color: #c0392b; }
    .badge-critical { background: #c0392b; color: white; animation: pulse 1.2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.7} }
    div.stButton > button[kind="primary"] {
        background-color: #0078BE; color: white;
        border-radius: 8px; font-size: 1.1rem; padding: 0.55rem 2.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
SEVERITY_LABEL_VI = {
    "NORMAL":     "BÌNH THƯỜNG",
    "WATCH":      "THEO DÕI",
    "SEE_DOCTOR": "GẶP BÁC SĨ",
    "CRITICAL":   "KHẨN CẤP",
}
SEVERITY_ICON = {
    "NORMAL": "🟢", "WATCH": "🟡", "SEE_DOCTOR": "🔴", "CRITICAL": "🚨",
}
SEVERITY_BADGE_CLASS = {
    "NORMAL": "badge-normal", "WATCH": "badge-watch",
    "SEE_DOCTOR": "badge-see-doc", "CRITICAL": "badge-critical",
}
SEVERITY_ROW_CLASS = {
    "NORMAL": "row-normal", "WATCH": "row-watch",
    "SEE_DOCTOR": "row-see-doc", "CRITICAL": "row-critical",
}
FLAG_LABEL_VI = {
    "NORMAL":       "Bình thường",
    "HIGH":         "Cao",
    "LOW":          "Thấp",
    "CRITICAL_HIGH":"Nguy kịch cao",
    "CRITICAL_LOW": "Nguy kịch thấp",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _format_ref(ref_low, ref_high, unit):
    if ref_low is not None and ref_high is not None:
        return f"{ref_low}–{ref_high} {unit}"
    if ref_high is not None:
        return f"<{ref_high} {unit}"
    if ref_low is not None:
        return f">{ref_low} {unit}"
    return "—"


def _lab_severity(lab) -> str:
    """Quick severity for table colouring (before workflow runs)."""
    try:
        flag_enum = ResultFlag(lab.flag.value if hasattr(lab.flag, "value") else lab.flag)
        obj = LabResult(
            test_code=lab.test_code, test_name=lab.test_name,
            value=float(lab.value), unit=lab.unit,
            ref_low=lab.ref_low, ref_high=lab.ref_high, flag=flag_enum,
        )
        return classify_severity(obj).value
    except Exception:
        return "NORMAL"


def _render_lab_table(patient):
    rows_html = ""
    for lab in patient.lab_results:
        sev = _lab_severity(lab)
        row_cls = SEVERITY_ROW_CLASS.get(sev, "row-normal")
        icon = SEVERITY_ICON.get(sev, "🟢")
        flag_str = lab.flag.value if hasattr(lab.flag, "value") else str(lab.flag)
        ref_str = _format_ref(lab.ref_low, lab.ref_high, lab.unit)
        rows_html += f"""
        <tr class="{row_cls}">
            <td>{icon}</td>
            <td><b>{lab.test_name}</b></td>
            <td>{lab.value} {lab.unit}</td>
            <td>{ref_str}</td>
            <td>{FLAG_LABEL_VI.get(flag_str, flag_str)}</td>
        </tr>"""
    st.markdown(f"""
    <table class="lab-table">
      <thead><tr>
        <th></th><th>Chỉ số</th><th>Kết quả</th><th>Tham chiếu</th><th>Trạng thái</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


def _render_action_buttons():
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📅 Đặt lịch Vinmec", "https://www.vinmec.com/vi/dat-lich-kham/")
    with c2:
        st.button("👍 Hữu ích", key="fb_up")
    with c3:
        st.button("👎 Chưa tốt", key="fb_down")
    st.caption("⚕️ *Lưu ý: Kết quả phân tích chỉ mang tính tham khảo. Vui lòng tham khảo ý kiến bác sĩ để được tư vấn chính xác.*")


def _render_ai_output(result: dict):
    st.divider()

    if result.get("is_critical"):
        st.error("🚨 KHẨN CẤP — Phát hiện chỉ số nguy kịch!")
        alert = result.get("critical_alert") or {}
        for a in alert.get("alerts", []):
            st.markdown(f"**{a.get('test_name', a.get('test_code'))}**: "
                        f"{a.get('value')} {a.get('unit', '')} — {a.get('issue', '')}")
        st.warning("⚠️ Vui lòng gặp bác sĩ hoặc đến cơ sở y tế ngay.")
        st.markdown("### 📌 Bước tiếp theo:")
        for i, s in enumerate(result.get("suggestions", []), 1):
            st.markdown(f"{i}. {s}")
        _render_action_buttons()
        return

    overall = result.get("overall_severity", "NORMAL")
    badge_cls = SEVERITY_BADGE_CLASS.get(overall, "badge-normal")
    icon = SEVERITY_ICON.get(overall, "🟢")
    label = SEVERITY_LABEL_VI.get(overall, overall)

    st.markdown(
        f'<span class="badge {badge_cls}">{icon} MỨC ĐỘ TỔNG QUÁT: {label}</span>',
        unsafe_allow_html=True,
    )
    summary = result.get("summary", "")
    if summary:
        st.markdown(f"📋 **Tóm tắt:** {summary}")

    explanations = result.get("explanations") or []
    if explanations:
        st.markdown("### 📊 Chi tiết từng chỉ số:")
        for exp in explanations:
            sev = exp.get("severity", "NORMAL")
            exp_icon = SEVERITY_ICON.get(sev, "🟢")
            exp_label = SEVERITY_LABEL_VI.get(sev, sev)
            header = f"{exp_icon} {exp['test_name']} — {exp['value']} {exp.get('unit','')} ({exp_label})"
            with st.expander(header, expanded=(sev != "NORMAL")):
                st.write(exp.get("explanation", ""))
    else:
        st.info("Tất cả các chỉ số nằm trong giới hạn bình thường. Không có gì đặc biệt cần giải thích.")

    suggestions = result.get("suggestions") or []
    if suggestions:
        st.markdown("### 📌 Bước tiếp theo:")
        for i, s in enumerate(suggestions, 1):
            st.markdown(f"{i}. {s}")

    _render_action_buttons()


def _build_context_prompt(patient, result: dict) -> str:
    """Build a patient-aware system prompt for the follow-up chat agent."""
    lab_lines = "\n".join(
        f"  - {r.test_name}: {r.value} {r.unit} [{r.flag.value if hasattr(r.flag, 'value') else r.flag}]"
        for r in patient.lab_results
    )
    abnormal = [e for e in (result.get("explanations") or []) if e.get("severity") != "NORMAL"]
    abnormal_str = (
        ", ".join(f"{e['test_name']} ({SEVERITY_LABEL_VI.get(e['severity'], e['severity'])})" for e in abnormal)
        or "Không có chỉ số bất thường"
    )
    overall = SEVERITY_LABEL_VI.get(result.get("overall_severity", "NORMAL"), "BÌNH THƯỜNG")

    return f"""Bạn là Vinmec Lumina — trợ lý giải thích kết quả xét nghiệm của Vinmec.
Bạn đang tư vấn cho bệnh nhân sau:
  - Tên: {patient.name} | Tuổi: {patient.age} | Giới tính: {patient.sex}
  - Tiền sử: {', '.join(patient.conditions)}
  - Ngày xét nghiệm: {patient.test_date}

KẾT QUẢ XÉT NGHIỆM:
{lab_lines}

ĐÁNH GIÁ HỆ THỐNG:
  - Mức độ tổng quát: {overall}
  - Chỉ số cần chú ý: {abnormal_str}
  - Tóm tắt: {result.get('summary', '')}

GIỚI HẠN BẮT BUỘC:
  - Chỉ giải thích dựa trên kết quả xét nghiệm trên — không bịa thêm thông tin
  - KHÔNG chẩn đoán bệnh cụ thể, KHÔNG tư vấn thuốc hoặc liều dùng
  - Dùng tiếng Việt dễ hiểu, tránh thuật ngữ y khoa phức tạp
  - Luôn kèm gợi ý "tham khảo bác sĩ" khi không chắc chắn
  - Nếu câu hỏi vượt phạm vi kết quả xét nghiệm này, từ chối lịch sự"""


def _render_followup_chat(patient, result: dict):
    st.divider()
    st.markdown("#### 💬 Hỏi thêm Lumina về kết quả")

    # Render existing conversation
    for msg in st.session_state.get("chat_display", []):
        avatar = "🏥" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    user_q = st.chat_input("Ví dụ: Tại sao HbA1c cao? Tôi nên ăn uống thế nào?")
    if not user_q:
        return

    # Append user message and persist before calling LLM
    display = list(st.session_state.get("chat_display", []))
    display.append({"role": "user", "content": user_q})
    st.session_state.chat_display = display

    # Build initial history with context prompt on first turn
    history = list(st.session_state.get("chat_history", []))
    if not history:
        from langchain_core.messages import SystemMessage
        history = [SystemMessage(content=_build_context_prompt(patient, result))]

    # Call the existing chat agent
    reply = "Xin lỗi, tôi không thể trả lời lúc này. Vui lòng thử lại."
    try:
        from src.agents.agent import run_agent_turn
        from langchain_core.messages import AIMessage
        with st.spinner("Lumina đang trả lời..."):
            updated_history = run_agent_turn(user_q, history, provider=llm_provider_key)
        last_ai = next((m for m in reversed(updated_history) if isinstance(m, AIMessage)), None)
        if last_ai:
            reply = getattr(last_ai, "content", reply) or reply
        st.session_state.chat_history = updated_history
    except RuntimeError as e:
        if "OPENAI_API_KEY" in str(e) or "GROQ_API_KEY" in str(e):
            if llm_provider_key == "groq":
                reply = "⚠️ Chưa cấu hình Groq API. Vui lòng thêm `GROQ_API_KEY` vào file `.env` để dùng tính năng hỏi đáp."
            else:
                reply = "⚠️ Chưa cấu hình Azure API. Vui lòng thêm `OPENAI_API_KEY` vào file `.env` để dùng tính năng hỏi đáp."
    except Exception:
        pass  # keep default reply

    display.append({"role": "assistant", "content": reply})
    st.session_state.chat_display = display
    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — Screen 1: Patient selector
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🏥 Vinmec Lumina")
st.sidebar.caption("Trợ lý giải thích kết quả xét nghiệm")
st.sidebar.divider()

# API Provider selector
st.sidebar.markdown("**⚙️ Cấu hình API:**")
llm_provider = st.sidebar.radio(
    "Chọn nhà cung cấp LLM:",
    ["Azure OpenAI", "Groq"],
    key="llm_provider_choice",
    horizontal=False
)
llm_provider_key = "azure" if llm_provider == "Azure OpenAI" else "groq"

st.sidebar.divider()

@st.cache_data
def _patient_options():
    patients = get_all_patients()
    return {f"{p.name} ({p.patient_id})": p.patient_id for p in patients}

options = _patient_options()
selected_label = st.sidebar.radio("Chọn bệnh nhân:", list(options.keys()))
patient_id = options[selected_label]

# Reset everything when patient changes
if st.session_state.get("selected_patient_id") != patient_id:
    st.session_state.selected_patient_id = patient_id
    st.session_state.workflow_result = None
    st.session_state.chat_history = []
    st.session_state.chat_display = []

st.sidebar.divider()
st.sidebar.info("🤖 AI hiểu dữ liệu — Bác sĩ hiểu bệnh nhân.")

# ──────────────────────────────────────────────────────────────────────────────
# Main area — Screen 2: Patient card + lab table
# ──────────────────────────────────────────────────────────────────────────────
patient = get_patient(patient_id)

st.markdown(f"### 👤 {patient.name} &nbsp;|&nbsp; {patient.age} tuổi &nbsp;|&nbsp; {patient.sex}")
st.markdown(f"**Tiền sử:** {', '.join(patient.conditions)} &nbsp;&nbsp; **Ngày xét nghiệm:** {patient.test_date}")

st.markdown("#### Kết quả xét nghiệm")
_render_lab_table(patient)

st.markdown("")
_, mid, _ = st.columns([1, 2, 1])
with mid:
    analyze = st.button("🤖 Giải thích với AI", use_container_width=True, type="primary")

if analyze:
    with st.spinner("Lumina đang phân tích..."):
        st.session_state.workflow_result = run_workflow(patient_id=patient_id, llm_provider=llm_provider_key)
    # Reset chat so follow-up starts fresh for new analysis
    st.session_state.chat_history = []
    st.session_state.chat_display = []

# ──────────────────────────────────────────────────────────────────────────────
# Main area — Screen 3: AI output panel + follow-up chat
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.get("workflow_result"):
    _render_ai_output(st.session_state.workflow_result)
    _render_followup_chat(patient, st.session_state.workflow_result)

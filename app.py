import streamlit as st
import pandas as pd
import time

# ==========================================
# 1. CẤU HÌNH TRANG & STYLING (Vinmec Theme)
# ==========================================
st.set_page_config(page_title="Vinmec Lumina", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    /* Nút màu xanh Vinmec */
    div.stButton > button:first-child {
        background-color: #0078BE;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #005a8f;
        border-color: #005a8f;
    }
    /* Các badge mức độ */
    .badge-normal { color: #155724; background-color: #d4edda; padding: 5px 10px; border-radius: 5px; font-weight: bold;}
    .badge-watch { color: #856404; background-color: #fff3cd; padding: 5px 10px; border-radius: 5px; font-weight: bold;}
    .badge-doctor { color: #721c24; background-color: #f8d7da; padding: 5px 10px; border-radius: 5px; font-weight: bold;}
    .badge-critical { color: white; background-color: #dc3545; padding: 10px; border-radius: 5px; font-weight: bold; text-align: center; font-size: 1.2em;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. MOCK DATA (Từ Section 6)
# ==========================================
MOCK_PATIENTS = {
    "Nguyễn Thị A": {
        "patient_id": "P001",
        "name": "Nguyễn Thị A",
        "age": 45,
        "sex": "Nữ",
        "conditions": ["Đái tháo đường type 2"],
        "lab_results": [
            {"test_name": "HbA1c", "value": "8.2", "unit": "%", "ref": "4.0–5.6", "flag": "HIGH", "status": "🔴 Cao"},
            {"test_name": "LDL Cholesterol", "value": "3.4", "unit": "mmol/L", "ref": "<3.0", "flag": "HIGH", "status": "🟡 Theo dõi"},
            {"test_name": "Creatinine", "value": "78", "unit": "μmol/L", "ref": "44–97", "flag": "NORMAL", "status": "🟢 Bình thường"},
            {"test_name": "Glucose (đói)", "value": "9.1", "unit": "mmol/L", "ref": "3.9–6.1", "flag": "HIGH", "status": "🔴 Cao"}
        ],
        "ai_mock": {
            "severity": "GẶP BÁC SĨ",
            "summary": "2 chỉ số cần chú ý, 1 cần theo dõi",
            "explanations": [
                {"name": "HbA1c — 8.2% (Cao)", "desc": "Chỉ số này phản ánh mức đường huyết trung bình trong 3 tháng qua. Với bạn (tiền sử đái tháo đường), kết quả này cho thấy đường huyết chưa được kiểm soát tốt. Tham chiếu cho người khỏe mạnh là 4–5.6%."},
                {"name": "Glucose (đói) — 9.1 mmol/L (Cao)", "desc": "Lượng đường trong máu tại thời điểm lấy mẫu đang ở mức cao. Điều này đồng nhất với chỉ số HbA1c, cho thấy cần can thiệp để ổn định đường huyết."},
                {"name": "LDL Cholesterol — 3.4 mmol/L (Theo dõi)", "desc": "Mỡ 'xấu' hơi cao so với khuyến nghị. Cần chú ý vì mỡ máu cao kết hợp với tiểu đường có thể tăng nguy cơ tim mạch."}
            ],
            "next_steps": [
                "Tái khám và điều chỉnh phác đồ kiểm soát đường huyết với bác sĩ nội tiết.",
                "Tái xét nghiệm HbA1c sau 3 tháng.",
                "Theo dõi chế độ ăn giảm tinh bột và duy trì vận động nhẹ nhàng."
            ]
        }
    },
    "Trần Văn B": {
        "patient_id": "P002",
        "name": "Trần Văn B",
        "age": 62,
        "sex": "Nam",
        "conditions": ["Tăng huyết áp"],
        "lab_results": [
            {"test_name": "Bạch cầu", "value": "6.8", "unit": "×10⁹/L", "ref": "4.0–10.0", "flag": "NORMAL", "status": "🟢 Bình thường"},
            {"test_name": "Hemoglobin", "value": "138", "unit": "g/L", "ref": "130–170", "flag": "NORMAL", "status": "🟢 Bình thường"},
            {"test_name": "Creatinine", "value": "91", "unit": "μmol/L", "ref": "62–106", "flag": "NORMAL", "status": "🟢 Bình thường"},
            {"test_name": "LDL Cholesterol", "value": "2.8", "unit": "mmol/L", "ref": "<3.0", "flag": "NORMAL", "status": "🟢 Bình thường"}
        ],
        "ai_mock": {
            "severity": "BÌNH THƯỜNG",
            "summary": "Tất cả các chỉ số xét nghiệm đều nằm trong giới hạn bình thường.",
            "explanations": [],
            "next_steps": [
                "Tiếp tục duy trì phác đồ điều trị tăng huyết áp hiện tại.",
                "Khám sức khỏe định kỳ theo lịch hẹn của bác sĩ."
            ]
        }
    },
    "Lê Thị C": {
        "patient_id": "P003",
        "name": "Lê Thị C",
        "age": 38,
        "sex": "Nữ",
        "conditions": ["Đang mang thai tuần 28"],
        "lab_results": [
            {"test_name": "Hemoglobin", "value": "68", "unit": "g/L", "ref": "110–160", "flag": "CRITICAL_LOW", "status": "🚨 KHẨN CẤP"},
            {"test_name": "Bạch cầu", "value": "18.5", "unit": "×10⁹/L", "ref": "4.0–10.0", "flag": "HIGH", "status": "🔴 Cao"},
            {"test_name": "Tiểu cầu", "value": "89", "unit": "×10⁹/L", "ref": "150–400", "flag": "LOW", "status": "🔴 Thấp"},
            {"test_name": "AST", "value": "245", "unit": "U/L", "ref": "0–40", "flag": "HIGH", "status": "🔴 Cao"}
        ]
        # Không có ai_mock vì ca khẩn cấp sẽ chặn ngay lập tức
    }
}


# ==========================================
# 3. SIDEBAR (Screen 1)
# ==========================================
st.sidebar.title("🏥 Vinmec Lumina")
st.sidebar.caption("Trợ lý giải thích kết quả xét nghiệm")
st.sidebar.divider()

selected_name = st.sidebar.radio(
    "Danh sách bệnh nhân",
    options=list(MOCK_PATIENTS.keys())
)
patient = MOCK_PATIENTS[selected_name]

# Reset state khi đổi bệnh nhân
if "last_patient" not in st.session_state or st.session_state.last_patient != selected_name:
    st.session_state.show_ai = False
    st.session_state.last_patient = selected_name

# ==========================================
# 4. GIAO DIỆN CHÍNH (Screen 2)
# ==========================================
# Patient Profile Card
st.markdown(f"### 👤 {patient['name']} | {patient['age']} tuổi | {patient['sex']}")
st.markdown(f"**Tiền sử:** {', '.join(patient['conditions'])} &nbsp;&nbsp;|&nbsp;&nbsp; **Ngày xét nghiệm:** 2026-04-08")
st.divider()

# Lab Results Table
df_labs = pd.DataFrame(patient['lab_results'])
df_display = df_labs[['test_name', 'value', 'unit', 'ref', 'status']].rename(columns={
    'test_name': 'Chỉ số',
    'value': 'Kết quả',
    'unit': 'Đơn vị',
    'ref': 'Tham chiếu',
    'status': 'Trạng thái'
})

st.dataframe(df_display, use_container_width=True, hide_index=True)

# Guardrail Check: Kiểm tra xem có chỉ số CRITICAL không
is_critical = any("CRITICAL" in res['flag'] for res in patient['lab_results'])

# ==========================================
# 5. XỬ LÝ AI & KẾT QUẢ (Screen 3)
# ==========================================
if st.button("🤖 Giải thích với AI"):
    st.session_state.show_ai = True

if st.session_state.show_ai:
    st.divider()
    
    if is_critical:
        # LUỒNG ESCALATE: Ngay lập tức hiển thị cảnh báo đỏ, không gọi AI
        st.markdown("<div class='badge-critical'>🚨 KẾT QUẢ KHẨN CẤP</div>", unsafe_allow_html=True)
        st.error("Phát hiện chỉ số nguy hiểm (Hemoglobin quá thấp). Vui lòng gặp bác sĩ hoặc đến cơ sở y tế gần nhất NGAY LẬP TỨC. Lumina tạm ngưng giải thích chi tiết để ưu tiên cấp cứu.")
        
    else:
        # LUỒNG BÌNH THƯỜNG / THEO DÕI: Giả lập chờ LLM
        with st.spinner("Lumina đang phân tích..."):
            time.sleep(1.5) # Fake network delay
            
        ai_data = patient['ai_mock']
        
        # Hiển thị mức độ tổng quát (Severity Badge)
        if ai_data['severity'] == "GẶP BÁC SĨ":
            st.markdown("<div class='badge-doctor'>🔴 MỨC ĐỘ TỔNG QUÁT: GẶP BÁC SĨ</div>", unsafe_allow_html=True)
        elif ai_data['severity'] == "BÌNH THƯỜNG":
            st.markdown("<div class='badge-normal'>🟢 MỨC ĐỘ TỔNG QUÁT: BÌNH THƯỜNG</div>", unsafe_allow_html=True)
            
        st.write("")
        st.write(f"📋 **Tóm tắt:** {ai_data['summary']}")
        st.write("")
        
        # Expanders cho từng chỉ số bất thường
        if ai_data['explanations']:
            for exp in ai_data['explanations']:
                # Mở sẵn mặc định (expanded=True)
                with st.expander(exp['name'], expanded=True):
                    st.write(exp['desc'])
        
        # Follow-up Suggestion
        st.markdown("### 📌 Bước tiếp theo:")
        for idx, step in enumerate(ai_data['next_steps'], 1):
            st.markdown(f"{idx}. {step}")
            
        st.write("")
        
        # Mock Actions
        col1, col2, col3, col4 = st.columns([2, 1, 1, 4])
        with col1:
            st.button("📅 Đặt lịch Vinmec", type="primary", use_container_width=True)
        with col2:
            st.button("👍", use_container_width=True)
        with col3:
            st.button("👎", use_container_width=True)
import streamlit as st
import pandas as pd
import time
import os
import json

# ==========================================
# 1. CẤU HÌNH TRANG & STYLING (Vinmec Theme)
# ==========================================
st.set_page_config(page_title="Vinmec Lumina", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    /* Tổng thể khung chat */
    .chat-container {
        background-color: #0b0c10;
        color: #e0e6ed;
        font-family: 'Inter', sans-serif;
        padding: 20px;
        border-radius: 10px;
    }

    /* Cấu trúc chung cho mỗi dòng tin nhắn */
    .message {
        margin-bottom: 20px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        width: 100%;
    }

    /* TIN NHẮN BOT: Căn trái */
    .bot-message { justify-content: flex-start; }

    /* TIN NHẮN USER: Căn phải */
    .user-message { justify-content: flex-end; }

    /* Avatar */
    .message-avatar {
        width: 40px; height: 40px; border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        font-size: 1.2rem; font-weight: bold; flex-shrink: 0;
    }

    .bot-avatar {
        background: linear-gradient(135deg, #0078BE, #00c6ff);
        color: white;
        box-shadow: 0 4px 15px rgba(0, 120, 190, 0.4);
    }

    .user-avatar {
        background: rgba(255,255,255,0.1);
        color: #e0e6ed;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* Bong bóng chat */
    .message-content {
        font-size: 1.05rem; line-height: 1.6;
        padding: 12px 18px; border-radius: 18px;
        max-width: 70%; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .bot-message .message-content {
        background: rgba(22, 24, 29, 0.8);
        border: 1px solid rgba(255,255,255,0.05);
        border-top-left-radius: 4px;
    }

    .user-message .message-content {
        background: rgba(0, 120, 190, 0.25);
        border: 1px solid rgba(0, 163, 255, 0.3);
        border-top-right-radius: 4px;
        color: #ffffff;
    }

    div.stButton > button:first-child {
        background-color: #0078BE;
        color: white;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HÀM NẠP DỮ LIỆU TỪ JSON
# ==========================================
@st.cache_data # Dùng cache để không phải đọc file liên tục mỗi khi UI reload
def load_patients_from_json():
    patients = {}
    # Đường dẫn tương đối từ file app.py
    data_path = os.path.join("src", "data", "patients")
    
    if os.path.exists(data_path):
        for filename in os.listdir(data_path):
            if filename.endswith(".json"):
                with open(os.path.join(data_path, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Lấy 'name' làm key để hiển thị trên Sidebar
                    patients[data["name"]] = data
    return patients

MOCK_PATIENTS = load_patients_from_json()

# Kiểm tra nếu không có dữ liệu
if not MOCK_PATIENTS:
    st.error("Không tìm thấy dữ liệu bệnh nhân trong thư mục src/data/patients/")
    st.stop()

# ==========================================
# 3. SIDEBAR & LOGIC
# ==========================================
st.sidebar.title("🏥 Vinmec Lumina")
st.sidebar.caption("Trợ lý giải thích kết quả xét nghiệm")
st.sidebar.divider()

selected_name = st.sidebar.radio("Danh sách bệnh nhân", options=list(MOCK_PATIENTS.keys()))
patient = MOCK_PATIENTS[selected_name]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Reset chat khi đổi bệnh nhân
if "last_patient" not in st.session_state or st.session_state.last_patient != selected_name:
    st.session_state.chat_history = []
    st.session_state.last_patient = selected_name
    st.session_state.chat_history.append({
        "role": "bot",
        "content": f"Xin chào! Tôi là Vinmec Lumina. Bạn vừa chọn bệnh án của <b>{selected_name}</b> ({patient['age']} tuổi, {patient['sex']}). Tiền sử: {', '.join(patient['conditions'])}. Tôi có thể giúp gì cho bạn?"
    })

# ==========================================
# 4. HIỂN THỊ NỘI DUNG CHAT
# ==========================================
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.chat_history:
    if message["role"] == "bot":
        st.markdown(f"""
        <div class="message bot-message">
            <div class="message-avatar bot-avatar">L</div>
            <div class="message-content">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message user-message">
            <div class="message-content">{message["content"]}</div>
            <div class="message-avatar user-avatar">👤</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. INPUT VÀ XỬ LÝ CÂU HỎI
# ==========================================
user_input = st.chat_input("Nhập câu hỏi của bạn tại đây...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    with st.spinner("Đang phân tích..."):
        time.sleep(0.8)
    
    # Ở đây bạn có thể thêm logic xử lý dựa trên dữ liệu 'lab_results' có trong file JSON
    bot_reply = f"Tôi đã nhận được câu hỏi về bệnh nhân {selected_name}. Hệ thống đang phân tích {len(patient['lab_results'])} chỉ số xét nghiệm..."
    st.session_state.chat_history.append({"role": "bot", "content": bot_reply})
    
    st.rerun()
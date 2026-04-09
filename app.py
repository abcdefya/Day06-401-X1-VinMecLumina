import streamlit as st
import pandas as pd
import time

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

    /* TIN NHẮN BOT: Căn trái (Mặc định) */
    .bot-message {
        justify-content: flex-start;
    }

    /* TIN NHẮN USER: Căn phải */
    .user-message {
        justify-content: flex-end;
    }

    /* Avatar */
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 1.2rem;
        font-weight: bold;
        flex-shrink: 0;
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
        font-size: 1.05rem;
        line-height: 1.6;
        padding: 12px 18px;
        border-radius: 18px;
        max-width: 70%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .bot-message .message-content {
        background: rgba(22, 24, 29, 0.8);
        border: 1px solid rgba(255,255,255,0.05);
        border-top-left-radius: 4px; /* Bo góc đặc trưng bên trái */
    }

    .user-message .message-content {
        background: rgba(0, 120, 190, 0.25);
        border: 1px solid rgba(0, 163, 255, 0.3);
        border-top-right-radius: 4px; /* Bo góc đặc trưng bên phải */
        color: #ffffff;
    }

    /* Tùy chỉnh nút Sidebar và các thành phần khác */
    div.stButton > button:first-child {
        background-color: #0078BE;
        color: white;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOCK DATA
# ==========================================
MOCK_PATIENTS = {
    "Nguyễn Thị A": {
        "age": 45, "sex": "Nữ", "conditions": ["Đái tháo đường type 2"]
    },
    "Trần Văn B": {
        "age": 62, "sex": "Nam", "conditions": ["Tăng huyết áp"]
    },
    "Lê Thị C": {
        "age": 38, "sex": "Nữ", "conditions": ["Đang mang thai tuần 28"]
    }
}

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
        # User message: Nội dung trước, Avatar sau để hiện bên phải
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
    # Thêm tin nhắn user vào lịch sử
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Hiệu ứng chờ phản hồi
    with st.spinner("Đang phân tích..."):
        time.sleep(0.8)
    
    # Phản hồi mẫu của Bot
    bot_reply = "Tôi đã nhận được thông tin. Đây là phản hồi từ trợ lý Vinmec dành cho bạn."
    st.session_state.chat_history.append({"role": "bot", "content": bot_reply})
    
    # Làm mới trang để cập nhật giao diện
    st.rerun()
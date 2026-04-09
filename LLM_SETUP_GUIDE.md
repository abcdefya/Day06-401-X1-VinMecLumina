# LLM Setup Guide - Vinmec Lumina

Vinmec Lumina hiện hỗ trợ hai nhà cung cấp LLM:
- **Azure OpenAI** (mặc định)
- **Groq** (giải pháp thay thế khi Azure bị rate limit)

## Cấu hình

Thêm các API keys vào file `.env` trong thư mục gốc của project:

### Option 1: Azure OpenAI (Recommended)

```env
OPENAI_API_KEY=your_azure_api_key_here
```

**Lấy API Key:**
1. Truy cập [Azure AI Services](https://portal.azure.com/)
2. Tạo hoặc chọn Azure OpenAI resource
3. Lấy API key từ "Keys and Endpoint" section
4. Lưu vào `.env`

**Models hỗ trợ:**
- `gpt-4o` (hiện tại)
- Các model OpenAI khác cũng có thể sử dụng

---

### Option 2: Groq (Alternative)

```env
GROQ_API_KEY=your_groq_api_key_here
```

**Lấy API Key:**
1. Truy cập [Groq Console](https://console.groq.com)
2. Đăng ký hoặc đăng nhập tài khoản Groq
3. Tạo API key từ dashboard
4. Lưu vào `.env`

**Models hỗ trợ:**
- `mixtral-8x7b-32768` (hiện tại - miễn phí và nhanh)
- `llama2-70b-4096`
- Các model Groq khác

**Lợi ích:**
- Hoàn toàn miễn phí với mức sử dụng hợp lý
- Tốc độ response nhanh
- Không bị rate limit quá nghiêm khắc

---

## Sử dụng

### Trong Streamlit App

1. Mở ứng dụng Streamlit
2. Ở sidebar, chọn **"⚙️ Cấu hình API"**
3. Chọn nhà cung cấp LLM:
   - **Azure OpenAI** (nếu Azure API key được cấu hình)
   - **Groq** (nếu Groq API key được cấu hình)
4. Nhấn "🤖 Giải thích với AI" - ứng dụng sẽ sử dụng provider đã chọn

### Trong Code

```python
from src.agents.agent import run_workflow

# Sử dụng Groq
result = run_workflow(patient_id="P001", llm_provider="groq")

# Sử dụng Azure (mặc định)
result = run_workflow(patient_id="P001", llm_provider="azure")

# Hoặc không chỉ định (sẽ dùng Azure mặc định)
result = run_workflow(patient_id="P001")
```

---

## Troubleshooting

### Lỗi: "OPENAI_API_KEY not set"
- **Giải pháp:** Thêm `OPENAI_API_KEY` vào file `.env` nếu muốn sử dụng Azure

### Lỗi: "GROQ_API_KEY not set"
- **Giải pháp:** Thêm `GROQ_API_KEY` vào file `.env` nếu muốn sử dụng Groq

### Chọn Groq nhưng không có API key
- **Giải pháp:** 
  1. Đăng ký tài khoản tại [groq.com](https://groq.com)
  2. Tạo API key
  3. Thêm vào `.env`

### Rate limit từ Azure OpenAI
- **Giải pháp:** Chuyển sang sử dụng Groq tạm thời

---

## So Sánh

| Tiêu chí | Azure OpenAI | Groq |
|---------|-------------|------|
| Chi phí | Có phí | Miễn phí |
| Tốc độ | Trung bình | Rất nhanh |
| Rate limit | Có giới hạn | Rất cao |
| Mô hình | GPT-4o | Mixtral, Llama2 |
| Chất lượng | Xuất sắc | Rất tốt |

---

## Chú ý

- Nếu cầu hình cả hai API keys, bạn có thể chuyển đổi giữa chúng bất cứ lúc nào
- Luôn giữ API keys bí mật (không commit vào git)
- File `.env` nên được thêm vào `.gitignore`

---

Hãy liên hệ nếu gặp vấn đề!

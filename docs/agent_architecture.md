# Tổng quan Kiến trúc Agent & AI Logic (Vinmec Lumina)

Tài liệu này giải thích cách thức hoạt động của Agent và luồng xử lý AI (AI Logic) trong dự án Vinmec Lumina dựa trên việc phân tích mã nguồn Python (LangGraph) hiện tại trong thư mục `src/`.

---

## 1. Mô hình Agent: Cấu trúc Đồ thị Trạng thái (StateGraph)

Ứng dụng **không** sử dụng mô hình Agent tự do (ReAct hay Plan-and-Solve) nơi AI được tự quyết định quy trình hở. Thay vào đó, nó sử dụng kiến trúc **Deterministic Workflow (Quy trình tiền định)** được xây dựng bằng thư viện `LangGraph`.

Quy trình này gồm các "Nút" (Nodes) kết nối với nhau. Luồng chạy như sau:
```
[START] -> Guard Node -> (Rẽ nhánh: Khẩn cấp hoặc Bình thường)
                              |
                     [Bình thường] -> Severity Node -> Explain Node -> Suggest Node -> [END]
                              |
                        [Khẩn cấp] -> (Cắt ngang LLM, cảnh báo trực tiếp) -> [END]
```

### Các Nút (Nodes) cốt lõi:
1. **`guard_node.py` (Lớp bảo vệ y tế):** 
   - Đóng vai trò là "người gác cổng" bằng mã Code thuần (không dùng AI). 
   - Node này quét các giá trị xét nghiệm và so sánh với bộ quy tắc `CRITICAL_THRESHOLDS` (Panic values). 
   - Nếu phát hiện chỉ số đe dọa sinh mạng, nó bật cờ `is_critical = True` và ngắt hoàn toàn luồng LLM để trả về cảnh báo khẩn cấp đỏ, ngăn không cho AI đưa ra các lời khuyên dài dòng gây chậm trễ việc cấp cứu.
2. **`severity_node.py` (Phân loại tự động):**
   - Đánh giá mức độ nghiêm trọng (Bình thường / Theo dõi / Gặp bác sĩ) dựa trên độ lệch chuẩn của khoảng tham chiếu trước khi đẩy vào AI.
3. **`explain_node.py` (AI Phân tích nội dung):**
   - Là bộ não ngôn ngữ của Agent. Nó lấy các kết quả bất thường + hồ sơ tiền sử bệnh án + Bách khoa toàn thư y khoa nhỏ (`lab_kb.py`) để truyền vào Prompt.
   - LLM (Azure OpenAI `gpt-4o`) sẽ được gọi để dịch các con số phức tạp ra ngôn ngữ tự nhiên. 
   - Đặc biệt, Node này chứa **Fallback Logic**: Nếu Server LLM bị đứt hoặc mất API Key, nó sẽ tự lùi về mốc phân tích bằng câu chữ định sẵn (deterministic format) đảm bảo UI luôn hiển thị được lỗi.
4. **`suggest_node.py` (Hành động tiếp theo):**
   - LLM dựa vào tóm tắt bệnh lý để lựa chọn các "Next Steps" an toàn nhất (ví dụ: khuyên khám lại ở bệnh viện, thay đổi dinh dưỡng).

---

## 2. Các Cơ chế An toàn trong AI Logic (Safety Guardrails)

Bởi vì AI y tế luôn tiềm ẩn rủi ro "Ảo giác" (Hallucination) hoặc vi phạm pháp lý y tế, chương trình duy trì 3 lớp Guardrails được mã hóa cứng:

1. **Rule-over-AI (Quy tắc đè lên AI):**
   - Như đã nói ở `guard_node`, logic nhị phân kiểm tra giới hạn cận trên/dưới của ngưỡng xét nghiệm luôn được ưu tiên chạy trước và cao hơn bất cứ suy luận nào của AI. AI không có quyền can thiệp vào các chỉ số đỏ (Panic values).

2. **Grounding Prompt bằng RAG nội bộ:**
   - Trong `explain_node.py`, AI không được tự "tra Google" hay tự học dữ liệu trên mạng. Nó bị ép phải dùng Bách khoa từ điển `lab_kb.py` tiêm vào ngữ cảnh. 
   - Prompt bắt buộc: *"Explain this abnormal lab result... Avoid diagnosis and medication advice."*

3. **Keyword Filtering (Bộ lọc kiểm duyệt sau Output):**
   - Tại `explain_node.py`, hệ thống áp dụng Regex chặn các từ vựng nhạy cảm: `_BANNED_PATTERNS` (chứa các từ như `diagnose`, `ke don`, `chan doan`, `dung thuoc`...). 
   - Nếu AI tự ý trả về câu: *"Bạn đang bị suy thận, hãy dùng thuốc"*, bộ lọc sẽ phát hiện cụm từ vi phạm và ghi đè nội dung thành cụm từ phòng thủ an toàn trung lập, không để lọt ra giao diện người dùng `app.py` hay `main.js`.

---

## 3. Tương tác với Giao diện ứng dụng

Agent giao tiếp thông qua Payload (dict) được định nghĩa trong `src/state.py` (đối tượng `AgentState`). 

- Trong hệ thống Front-end cũ (`app.py` - bản MVP), Giao diện Import trực tiếp `run_workflow(patient_id)` từ Python.
- Trong hệ thống Front-end mới (`index.html` + `main.js`), các "Ổ cắm" (Plugs) đã được thiết lập để kết nối vào luồng Backend FastAPI/Flask ở dạng JSON - chứa toàn bộ `summary`, `explanations`, và `next_steps` được Graph xuất ra tại Node cuối cùng `[END]`.

### Tóm tắt cốt lõi
> Hệ thống này sử dụng **AI như một cỗ máy diễn giải văn bản phụ trợ** thay vì một dạng trí tuệ tổng hợp tự ra quyết định. Toàn bộ con đường đi từ Input -> Output được vạch sẵn một cách bảo thủ, đặt sự ổn định và an toàn y tế lên hàng đầu thông qua cấu trúc phân tầng Node của LangGraph.

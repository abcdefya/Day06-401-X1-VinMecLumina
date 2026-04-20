# Prototype README — VinMec Lumina

## Mô tả prototype

**VinMec Lumina** là chatbot AI giải thích kết quả xét nghiệm cho bệnh nhân Vinmec theo ngữ cảnh cá nhân hóa — dựa trên hồ sơ bệnh nhân (tuổi, giới tính, tiền sử bệnh) và dữ liệu xét nghiệm có cấu trúc từ hệ thống HIS/LIS. Prototype phân loại mức độ nghiêm trọng của từng chỉ số (bình thường / theo dõi / gặp bác sĩ / khẩn cấp), giải thích bằng tiếng Việt dễ hiểu, và gợi ý bước tiếp theo an toàn. Guardrail tích hợp sẵn ngăn AI chẩn đoán bệnh hoặc đề xuất thuốc.

## Level

**Working** — chạy end-to-end với 3 bệnh nhân mẫu, bao gồm cả critical path (bệnh nhân khẩn cấp bypass LLM → hiển thị cảnh báo cứng).

```bash
streamlit run app.py
```

## Link prototype

- **GitHub repo:** https://github.com/abcdefya/NhomX1-401-Day06

## Tools và API đã dùng

| Layer | Tool / API |
|---|---|
| UI | Streamlit |
| Workflow orchestration | LangGraph |
| LLM | OpenAI API (Azure AI endpoint, `OPENAI_API_KEY`) |
| LLM abstraction | LangChain, `langchain-openai`, `langchain-azure-ai`, `langchain-groq` |
| Config | python-dotenv |
| Data validation | Pydantic |

## Phân công

| Thành viên | MSSV | Vai trò | Trách nhiệm |
|---|---|---|---|
| Hoàng Thị Thanh Tuyền | 2A202600074 | UI Lead | Streamlit UI: sidebar chọn bệnh nhân, bảng kết quả xét nghiệm màu, panel AI output, nút feedback |
| Lê Minh Khang | 2A202600102 | AI Logic | System prompt, `explain_node`, `suggest_node`, `lab_kb.py` |
| Võ Thanh Chung | 2A202600040 | Data & Mock API | 3 file JSON bệnh nhân mẫu, `reference_ranges.py`, data loader |
| Nguyễn Hồ Bảo Thiên | 2A202600163 | Guardrails | `guard_node` (critical threshold), `severity_node` (rule-based), post-LLM keyword filter |
| Dương Khoa Điềm | 2A202600366 | LangGraph Orchestration | Wiring toàn bộ graph, `AgentState`, routing normal vs critical path, `run_workflow()` |
| Đỗ Thế Anh | 2A202600335 | Integration & Demo | Kết nối UI ↔ workflow, CSS Vinmec colors, QA end-to-end, demo script |

# SPEC — AI Product Hackathon

**Nhóm:** X1  
**Track:** ☐ VinFast · ☑ Vinmec · ☐ VinUni-VinSchool · ☐ XanhSM · ☐ Open  
**Problem statement (1 câu):** Bệnh nhân Vinmec thường hoang mang khi đọc kết quả xét nghiệm dù có sẵn dữ liệu, AI giúp giải thích cá nhân hóa dựa trên hồ sơ bệnh án để giảm tải cho bác sĩ và tăng trải nghiệm an tâm cho người bệnh.

**Phân công nhóm:**
- Hoàng Thị Thanh Tuyền - 2A202600074: AI Product Canvas
- Lê Minh Khang - 2A202600102: User Stories 4 paths
- Đỗ Thế Anh - 2A202600040: Eval metrics + threshold 
- Nguyễn Hồ Bảo Thiên - 2A202600163: Top 3 failure modes
- Dương Khoa Điềm - 2A202600366: ROI 3 kịch bản
- Võ Thanh Chung - 2A202600335: Mini AI spec

---

## 1. AI Product Canvas
## Canvas

|             | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Trust                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Feasibility                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Trả lời** | **User:** Bệnh nhân Vinmec đang chat trong app/web Vinmec sau khi có kết quả xét nghiệm; hệ thống đã có **hồ sơ cá nhân cơ bản** như tuổi, giới tính, tiền sử bệnh đã khai báo, lần khám gần nhất, và kết quả xét nghiệm dạng có cấu trúc từ HIS/LIS. Người nhà có thể hỗ trợ đọc kết quả nhưng user chính vẫn là bệnh nhân. <br><br> **Pain:** Dù đã có hồ sơ cá nhân, bệnh nhân vẫn không hiểu các chỉ số như HGB, WBC, glucose, HbA1c, LDL, AST/ALT, creatinine; thấy cao/thấp thì lo nhưng không biết mức độ liên quan tới bản thân mình; phải chờ bác sĩ giải thích hoặc tự tra Google dễ sai. <br><br> **AI giải quyết:** Chatbot đọc **kết quả xét nghiệm structured data** + dùng **context từ hồ sơ cá nhân** để giải thích cá nhân hóa hơn. Ví dụ: cùng một chỉ số nhưng cách diễn giải có thể khác theo tuổi/giới/tình trạng nền. AI sẽ: (1) xác định chỉ số bình thường/cao/thấp theo reference range phù hợp, (2) giải thích bằng ngôn ngữ dễ hiểu, (3) tóm tắt các điểm bất thường quan trọng nhất, (4) gợi ý mức độ ưu tiên hành động, và (5) đề xuất bước tiếp theo an toàn như đọc thêm, theo dõi, đặt lịch bác sĩ. <br><br> **Vì sao cách hiện tại chưa tốt:** Portal thường chỉ hiển thị số + khoảng tham chiếu; bệnh nhân phải tự nối các thông tin rời rạc. Việc có hồ sơ cá nhân nhưng chưa được dùng để giải thích đúng ngữ cảnh khiến trải nghiệm vẫn khó hiểu và thiếu tin cậy. | **Khi AI sai, ảnh hưởng:** Bệnh nhân có thể hiểu sai mức độ quan trọng của kết quả trong chính bối cảnh sức khỏe của mình: lo lắng quá mức, chủ quan, hoặc hiểu nhầm bước tiếp theo. Với chatbot y tế, rủi ro lớn nhất là **nói quá chắc**, **suy diễn thành chẩn đoán**, hoặc **bỏ qua context cá nhân** đã có trong hồ sơ. <br><br> **User biết AI sai khi:** (1) phần giải thích không khớp với chỉ số gốc hoặc khoảng tham chiếu, (2) AI nói khác với bác sĩ, (3) AI bỏ qua thông tin hồ sơ đã biết như giới tính/tiền sử bệnh, hoặc (4) AI trả lời quá chắc kiểu “bạn bị bệnh X”. <br><br> **User sửa bằng cách:** xem lại dữ liệu gốc ngay trong chat, chọn “không đúng / khó hiểu”, hỏi lại theo câu hỏi hẹp hơn, hoặc chuyển sang “đặt lịch bác sĩ / liên hệ Vinmec”. <br><br> **Cách tăng trust:** (1) luôn hiển thị **giá trị gốc + đơn vị + khoảng tham chiếu**, (2) nói rõ AI đang dùng thêm **hồ sơ cá nhân nào** để giải thích, (3) chỉ dùng ngôn ngữ dạng **gợi ý / tham khảo**, không chẩn đoán, (4) có fallback rõ: “trao đổi bác sĩ”, “đặt lịch”, “liên hệ y tế”, và (5) với câu hỏi vượt scope, chatbot phải nói thẳng là không đủ dữ liệu để kết luận. | **Ước lượng cost/latency:** Vì đầu vào là dữ liệu đã có cấu trúc từ hệ thống Vinmec, pipeline đơn giản hơn, rẻ hơn, và ổn định hơn. Có thể target cost khoảng **$0.003–0.01/request** cho flow giải thích ngắn, latency mục tiêu **< 2–3 giây**. <br><br> **Data giả định đã có sẵn trong công ty:** (1) kết quả xét nghiệm structured từ LIS/HIS: tên xét nghiệm, giá trị, đơn vị, khoảng tham chiếu, cờ high/low/normal; (2) hồ sơ cá nhân cơ bản: tuổi, giới tính, tiền sử bệnh đã khai báo, danh sách thuốc nền nếu có, khoa khám gần nhất; (3) knowledge base nội bộ để giải thích từng nhóm xét nghiệm bằng ngôn ngữ bệnh nhân; (4) rule severity an toàn cho một số panel xét nghiệm phổ biến. <br><br> **Risk chính:** Khoảng tham chiếu thay đổi theo giới/tuổi nhưng mapping sai; AI dùng hồ sơ cá nhân quá mức để suy diễn; AI trả lời vượt scope sang chẩn đoán/điều trị; các case nhiều bất thường cùng lúc vượt khả năng giải thích an toàn của chatbot. <br><br> **Hướng an toàn:** Giới hạn scope vào một số nhóm xét nghiệm structured như CBC, đường huyết, mỡ máu, chức năng gan/thận; output chỉ gồm **giải thích + severity + next step**; không chẩn đoán, không kê thuốc, không xử lý cấp cứu ngoài việc escalate. |

## Automation hay augmentation?

- [ ] Automation — AI làm thay, user không can thiệp
- [x] Augmentation — AI gợi ý, user quyết định cuối cùng

**Justify:** Augmentation. Đây là chatbot giải thích kết quả trong ngữ cảnh cá nhân, không phải hệ thống tự động kết luận y khoa. AI có thể tận dụng hồ sơ cá nhân để trả lời hữu ích hơn, nhưng quyền kết luận vẫn thuộc bác sĩ và quyền quyết định hành động vẫn thuộc bệnh nhân. Cost of reject thấp: user có thể bỏ qua câu trả lời, xem dữ liệu gốc, hoặc chuyển sang đặt lịch bác sĩ.

## Learning signal

| #   | Câu hỏi                                          | Trả lời                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | User correction đi vào đâu?                      | Mỗi lần user chọn “không đúng”, “khó hiểu”, “giải thích lại”, hoặc chuyển sang gặp bác sĩ sau khi đọc câu trả lời, hệ thống ghi log theo: loại xét nghiệm, pattern bất thường, loại context cá nhân đã dùng, câu trả lời AI, và loại lỗi gặp phải. Dữ liệu này đi vào cải thiện prompt, template giải thích, rule severity, và guardrail cho câu hỏi vượt phạm vi.                                                                                                                        |
| 2   | Product thu signal gì để biết tốt lên hay tệ đi? | **Implicit:** tỷ lệ user đọc hết câu trả lời, tỷ lệ mở phần “vì sao AI nói vậy”, tỷ lệ hỏi follow-up, tỷ lệ thoát sang “đặt lịch bác sĩ”, thời gian đọc trước khi thoát. <br><br> **Explicit:** thumbs up/down, rating “hữu ích / không hữu ich”, feedback “đúng ngữ cảnh cá nhân / bỏ sót hồ sơ của tôi / quá chung chung”. <br><br> **Correction:** bác sĩ hoặc CSKH gắn cờ câu trả lời chưa an toàn; user báo “AI bỏ qua tiền sử bệnh của tôi” hoặc “AI hiểu sai mức độ nghiêm trọng”. |
| 3   | Data thuộc loại nào?                             | - [x] User-specific <br> - [x] Domain-specific <br> - [x] Real-time <br> - [x] Human-judgment <br> - [ ] Khác: <br><br> **Giải thích:** Bài toán này không còn chỉ là domain-specific chung chung, vì chatbot có dùng user-specific context từ hồ sơ cá nhân. Nó cũng là real-time vì phản hồi dựa trên kết quả xét nghiệm hiện tại, và cần human-judgment vì cách diễn giải an toàn cho bệnh nhân không thể chỉ tối ưu bằng accuracy thuần túy.                                          |

**Có marginal value không?**

Có. Model nền có thể biết ý nghĩa chung của các chỉ số xét nghiệm, nhưng không tự biết hồ sơ cá nhân cụ thể của bệnh nhân Vinmec, không biết panel nào đang được Vinmec trả kết quả, và không biết cách diễn giải nào là an toàn trong UX của chatbot y tế. Giá trị riêng của sản phẩm nằm ở: (1) tích hợp structured lab data + hồ sơ cá nhân, (2) rule severity và fallback an toàn, (3) feedback loop từ bệnh nhân và bác sĩ về câu nào hữu ích, câu nào gây hiểu nhầm.


---

## 2. User Stories — 4 paths


### Feature: Explain Result  
**Trigger:** User mở kết quả xét nghiệm → AI đọc dữ liệu + context cá nhân → trả lời giải thích

| Path | Câu hỏi thiết kế | Mô tả |
|------|-----------------|------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | HGB thấp → AI giải thích “có thể gợi ý thiếu máu nhẹ” (confidence cao) → highlight bất thường + hiển thị context (tuổi/giới) → user hiểu → dừng |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | Chỉ số ít phổ biến → AI hiển thị “không chắc” + giải thích ngắn, trung lập → gợi ý hỏi bác sĩ → user tự quyết tiếp |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | AI giải thích không khớp với range → user thấy lệch so với số liệu hoặc khác bác sĩ → user bỏ qua AI → xem raw data / hỏi bác sĩ |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | User bấm “Báo sai/khó hiểu” → log (chỉ số + context + response) → cải thiện prompt / template |

---

### Feature: Severity Classification  
**Trigger:** User xem kết quả → AI phân loại mức độ (bình thường / theo dõi / gặp bác sĩ)

| Path | Câu hỏi thiết kế | Mô tả |
|------|-----------------|------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | LDL cao → AI gắn “Theo dõi” + lý do ngắn → user hiểu mức độ → tiếp tục |
| Low-confidence — AI không chắc | System báo bằng cách nào? | Case borderline → AI hiển thị “không chắc” → default “Theo dõi” → khuyến nghị hỏi bác sĩ |
| Failure — AI sai | User biết sai bằng cách nào? | AI đánh giá nhẹ nhưng bác sĩ nói nặng → user nhận ra mismatch → bỏ qua AI → follow bác sĩ |
| Correction — user sửa | User sửa bằng cách nào? Data đi vào đâu? | User chọn “bác sĩ đánh giá khác” → log mismatch (case + label) → calibrate severity rule |

---

### Feature: Follow-up Suggestion  
**Trigger:** Sau khi hiểu kết quả → AI gợi ý bước tiếp theo

| Path | Câu hỏi thiết kế | Mô tả |
|------|-----------------|------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | AI gợi ý “theo dõi 3 tháng” hoặc “tái khám” → user thấy hợp lý → hành động |
| Low-confidence — AI không chắc | System báo bằng cách nào? | AI không chắc → hiển thị “không chắc” → chỉ đưa gợi ý chung → user tự quyết |
| Failure — AI sai | User biết sai bằng cách nào? | AI không gợi ý đi khám dù bất thường rõ → user thấy risk → bỏ qua AI → tự đặt lịch |
| Correction — user sửa | User sửa bằng cách nào? Data đi vào đâu? | User đánh giá “không hữu ích/sai” → log pattern → điều chỉnh recommendation logic |

---

### Feature: Trend Analysis  
**Trigger:** User có lịch sử xét nghiệm → AI phân tích xu hướng

| Path | Câu hỏi thiết kế | Mô tả |
|------|-----------------|------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | HGB giảm qua 3 lần → AI hiển thị trend ↓ + summary → user hiểu tiến triển |
| Low-confidence — AI không chắc | System báo bằng cách nào? | Chỉ có 1–2 data point → AI hiển thị “không đủ dữ liệu” → không suy luận |
| Failure — AI sai | User biết sai bằng cách nào? | AI đọc sai lịch sử → trend không khớp → user nhận ra → bỏ qua AI |
| Correction — user sửa | User sửa bằng cách nào? Data đi vào đâu? | User báo “trend sai” → system kiểm tra data → log lỗi data pipeline |

---

## Notes
- Mỗi feature có đủ 4 paths (Happy / Low-confidence / Failure / Correction)
- Failure path dựa trên mismatch với data gốc hoặc bác sĩ
- Correction path → đi vào feedback loop (log → cải thiện hệ thống)
- AI chỉ hỗ trợ (augmentation), không thay thế quyết định y khoa

---

## 3. Eval metrics + threshold

## 3.1. Triết lý đánh giá (Evaluation Philosophy)

Hệ thống AI hỗ trợ bệnh nhân đọc kết quả xét nghiệm là một **high-stakes AI system**, nơi sai sót có thể ảnh hưởng trực tiếp đến sức khỏe và tâm lý người dùng.

Do AI mang tính **xác suất (probabilistic)**, không thể đánh giá theo kiểu đúng/sai tuyệt đối như phần mềm truyền thống. Thay vào đó, hệ thống đánh giá tập trung vào hai yếu tố cốt lõi:

- **Precision (độ chính xác khi cảnh báo)** → tránh gây hoảng loạn không cần thiết  
- **Recall (độ bao phủ khi phát hiện bất thường)** → không bỏ sót dấu hiệu nguy hiểm  

> Nguyên tắc cốt lõi:  
> “Không bỏ sót dấu hiệu nguy hiểm, nhưng cũng không được gây lo lắng sai lệch cho bệnh nhân.”

---

## 3.2. Các chỉ số cốt lõi (Core Metrics)

| Metric | Threshold | Ý nghĩa đối với hệ thống |
|-------|----------|--------------------------|
| **Recall** | ≥ 99.9% | Đảm bảo AI không bỏ sót bất kỳ chỉ số nguy hiểm (Red Flag) như Kali, Glucose, men gan vượt ngưỡng. Missing = rủi ro y tế nghiêm trọng, thà bắt nhầm còn hơn bỏ sót. |
| **Hallucination Rate** | < 1% | Tỷ lệ AI tự bịa ra bệnh lý, quy tắc y khoa hoặc ngưỡng xét nghiệm không có trong guideline. |
|**Human Handoff/Acceptance Rate**|>70%|Tỷ lệ người dùng cảm thấy hài lòng với lời giải thích của AI và không cần phải nhấn nút "Kết nối bác sĩ" ngay lập tức.. Metric này đo lường Value thực tế. Nếu 90% người dùng sau khi nghe AI giải thích vẫn phải gọi bác sĩ vì không hiểu hoặc không tin, thì AI của bạn chưa mang lại giá trị kinh tế (ROI).|
---

## 3.3. Quy trình đo lường (Evaluation Process)

### 3.3.1 Bộ dữ liệu đánh giá (Eval Set)

- Xây dựng bộ **50–100 case test chuẩn hóa**
- Bao gồm:
  - Ca bình thường (normal)
  - Ca cận ngưỡng (borderline)
  - Ca bất thường nhẹ
  - Ca nguy hiểm (critical)

**Lưu ý:**
- Dữ liệu được nhập **trực tiếp (structured input)**  
- Mỗi case bao gồm:
  - Tên chỉ số (Glucose, AST, ALT, etc.)
  - Giá trị
  - Đơn vị đo (mg/dL, mmol/L, etc.)
  - Khoảng tham chiếu (reference range)

---

### 3.3.2 Phương pháp đánh giá

#### LLM-as-a-Judge (có kiểm soát)

Sử dụng model (GPT-4o / Claude 3.5) để đánh giá output của AI theo rubric:

| Tiêu chí | Mô tả |
|--------|------|
| Đúng y khoa | Kết luận có phù hợp guideline không |
| Không hallucinate | Không bịa thông tin ngoài dữ liệu |
| Diễn giải dễ hiểu | Người không chuyên vẫn hiểu |
| Tone phù hợp | Không gây hoảng loạn |

---

#### Human-in-the-loop (bắt buộc)

- 10–20% sample được review bởi bác sĩ hoặc chuyên gia y khoa  
- Dùng để:
  - Xác thực kết quả từ LLM judge  
  - Xây dựng bộ dữ liệu “gold standard”

---

### 3.3.3 Phân tích lỗi (Error Analysis)

Tất cả lỗi được phân loại theo **Failure Mode Library**:

| Failure Type | Ví dụ |
|-------------|------|
| Missed Critical | Không phát hiện Kali nguy hiểm |
| False Alarm | Báo bất thường nhưng thực tế bình thường |
| Hallucination | Bịa bệnh hoặc kết luận không có cơ sở |
| Over-interpretation | Suy diễn vượt quá dữ liệu |
| Under-clarification | Không hỏi thêm khi thiếu thông tin |

**Mục tiêu:**
- Xác định nguyên nhân gốc (prompt, logic, data)
- Cải thiện model và UX qua từng vòng lặp

---

## 4. Top 3 failure modes

| # | Trigger | Hậu quả | Mitigation |
|---|---|---|---|
| 1 | **Bỏ qua bối cảnh lâm sàng (Missing Patient Context):** Người dùng đưa thẳng tờ xét nghiệm vào mà không nói rõ họ bao nhiêu tuổi, giới tính gì, có đang mang thai không, hoặc có bệnh nền (như tiểu đường) không. | Đánh giá sai vì "khoảng bình thường" của mỗi nhóm người là khác nhau (ví dụ: chỉ số thiếu máu ở người khỏe mạnh sẽ bị đánh giá khác với phụ nữ đang mang thai tháng thứ 7). | Luôn có bước onboarding/prompt đầu vào bắt buộc: "Để kết quả chính xác, vui lòng cho tôi biết Giới tính, Tuổi và bạn có đang mang thai/có bệnh lý nền nào không?".<br><br>Thêm Disclaimer cố định: "Đánh giá này chỉ dựa trên các thông số chung..." |
| 2 | **Phản hồi thiếu độ khẩn cấp với "Chỉ số báo động đỏ":** Kết quả xét nghiệm có chứa các chỉ số đe dọa tính mạng ngay lập tức (Panic values) - ví dụ: Kali máu quá cao (> 6.0 mmol/L), men tim (Troponin) tăng vọt. | AI vẫn dùng giọng điệu tư vấn bình thản, từ tốn liệt kê nguyên nhân khiến người dùng chủ quan, không đi cấp cứu kịp thời dẫn đến nguy hiểm tính mạng. | Xây dựng một bộ lọc riêng biệt chuyên bắt các "Panic values".<br><br>Khi AI phát hiện các giá trị này, nó phải ngắt luồng phân tích bình thường, chuyển sang luồng cảnh báo đỏ (Red flag): "CẢNH BÁO: Chỉ số [X] của bạn đang ở mức RẤT NGUY HIỂM. Vui lòng gặp bác sĩ hoặc đến phòng khám gần nhất ngay lập tức!" |
| 3 | **Bỏ qua tính lịch sử và xu hướng:** Người dùng tải lên một kết quả có các chỉ số "rất xấu" (ví dụ: Men gan AST/ALT cao gấp đôi mức bình thường), nhưng thực chất tháng trước các chỉ số này của họ còn cao gấp 10 lần. | AI chỉ nhìn vào một điểm dữ liệu hiện tại và đánh giá tình trạng "đang rất tệ", khiến bệnh nhân hoang mang hoặc thất vọng. Trong khi thực tế, dưới góc nhìn lâm sàng, đây là một sự cải thiện đáng mừng. | Thiết kế luồng hỏi thêm thông tin (Context gathering): "Đây là lần đầu bạn xét nghiệm các chỉ số này hay đang trong quá trình theo dõi bệnh? Nếu có kết quả cũ, bạn có thể cung cấp thêm để tôi so sánh sự tiến triển nhé." |


---
## 5. ROI 3 kịch bản

### Phân tích Kinh tế và Chi phí Vận hành LLM

### 1. Chi phí ước tính mỗi yêu cầu (per-request cost)
*Giả định mỗi yêu cầu tiêu tốn ~1,500 token đầu vào + 500 token đầu ra:*

| Mô hình | Chi phí ước tính / yêu cầu |
| :--- | :--- |
| GPT-4o Mini | ~$0.00045 |
| Claude Sonnet 4.6 | ~$0.001 |
| DeepSeek V3.2 | ~$0.00035 |
| Gemini 3.1 Flash-Lite | ~$0.0003 |

**Chi phí vận hành hàng tháng** (ví dụ với Claude Sonnet 4.6, 5,000 yêu cầu/ngày):
> Chi phí/tháng = 5,000 req/ngày × 30 ngày × $0.001/req = **$150/tháng**

Mức chi phí này cực kỳ tối ưu so với giá trị tiết kiệm được từ hàng nghìn giờ làm việc của đội ngũ y tế.

### 2. Phân tích ROI qua 3 Kịch bản (Scenarios)

| Kịch bản | Tỷ lệ sử dụng (Adoption) | Tác động giảm tải | Kết quả hoàn vốn & ROI |
| :--- | :--- | :--- | :--- |
| **Thận trọng** (Conservative) | < 15% (Người dùng chưa tin tưởng) | Giảm 5–10% cuộc gọi CSKH, chưa giảm tải rõ rệt cho bác sĩ. | Âm hoặc hòa vốn trong 12 tháng đầu. Giá trị chủ yếu ở mặt thương hiệu. |
| **Thực tế** (Realistic - Kỳ vọng) | 30–40% (Hệ thống ổn định, UX tốt) | Giảm 20–30% cuộc gọi CSKH; tiết kiệm 1–2 phút giải thích/ca cho bác sĩ. | Hòa vốn vào tháng 6. ROI ước tính đạt 300–500%. |
| **Lạc quan** (Optimistic) | > 60% (Tích hợp sâu, độ tin cậy cao) | Giảm 40–60% lượng hỗ trợ (tổng đài/tin nhắn); thúc đẩy tái khám thông qua tự động hóa "next step". | Hoàn vốn nhanh trong 3 tháng đầu. Mức sinh lời rất cao. |

---

## Các tiêu chí dừng dự án (Kill Criteria)

### 🚩 Kill Criterion 1 — An toàn lâm sàng (Clinical Safety Kill Switch)
* **Mô tả:** AI vượt quyền, tự đưa ra chẩn đoán tên bệnh, kê thuốc hoặc quyết định điều trị thay bác sĩ.
* **Ngưỡng kích hoạt:**
    * Phát hiện **≥ 1 ca** AI đưa ra lời khuyên sai lệch dẫn đến nguy cơ sức khỏe nghiêm trọng (Red zone).
    * Hoặc tỷ lệ "hallucination" (đọc sai khoảng tham chiếu) **vượt 0.5%** trong giai đoạn Beta.
* **Mức độ nghiêm trọng:** Dừng ngay lập tức — không thương lượng.

### 🚩 Kill Criterion 2 — Tài chính & Hiệu năng (Business/Performance Kill Switch)
* **Mô tả:** Hệ thống tốn quá nhiều chi phí mà không mang lại đủ giá trị; tỷ lệ fallback quá cao khiến tính năng vô dụng với người dùng.
* **Ngưỡng kích hoạt:**
    * Chi phí API/Server **vượt 200%** so với ngân sách Conservative trong 3 tháng liên tiếp.
    * Hoặc tỷ lệ AI trả về Fallback (do độ tự tin thấp) **vượt 40%**.
* **Mức độ nghiêm trọng:** Review khẩn cấp → có thể dừng nếu không cải thiện.

### 🚩 Kill Criterion 3 — Pháp lý & Bảo mật dữ liệu
* **Mô tả:** Hệ thống không đảm bảo quyền riêng tư dữ liệu y tế bệnh nhân khi xử lý qua AI.
* **Ngưỡng kích hoạt:**
    * Không vượt qua bài kiểm tra bảo mật nội bộ.
    * Hoặc vi phạm các quy định hiện hành về lưu trữ và xử lý dữ liệu y tế (**Nghị định 98/2021**).
* **Mức độ nghiêm trọng:** Dừng triển khai cho đến khi khắc phục hoàn toàn.

---

## Kết luận

Dự án **Vinmec Lumina** đứng trước cơ hội lớn để dẫn đầu thị trường y tế số tại Việt Nam. Kịch bản **Realistic** (adoption 30–40%, hòa vốn tháng 6 và ROI 300–500%) là mục tiêu hoàn toàn khả thi nếu:
1. UX được thiết kế đơn giản, trực quan.
2. Knowledge base được kiểm chứng nghiêm ngặt.
3. Boundary Spec được tuân thủ tuyệt đối.

> **One-line business case:** > *"Dùng AI để giảm tải bệnh viện và tăng trải nghiệm bệnh nhân — trong khi giữ rủi ro y tế bằng 0."*
 Sự thành công không chỉ phụ thuộc vào công nghệ LLM mạnh mẽ, mà còn nằm ở sự tinh tế trong việc giữ vững ranh giới đặc tả: **AI hiểu kết quả, bác sĩ hiểu bệnh nhân.**
---

## 6. Mini AI spec

**Dự án:** Vinmec Lumina (Phân hệ AI Lab Result Explainer)

**1. Mục tiêu cốt lõi:**
Chuyển đổi các con số vô tri trong phiếu xét nghiệm thành kiến thức có thể hành động (Actionable Insights) cho bệnh nhân. Thay vì giải thích chung chung như Google, AI sử dụng chính hồ sơ sức khỏe (tuổi, tiền sử) để đưa ra lời giải thích "may đo" riêng cho từng người.

**2. Cơ chế AI:**
* **Input:** Structured Data (JSON) từ hệ thống LIS/HIS (tên chỉ số, giá trị, đơn vị, range) + User Profile (tuổi, giới tính, tiền sử bệnh).
* **Processing (Augmentation):** Sử dụng LLM (Claude 3.5/GPT-4o) kết hợp với **RAG (Retrieval-Augmented Generation)** trên bộ Knowledge Base y khoa của Vinmec. AI không tự ý suy luận mà "ánh xạ" kết quả của user vào các quy tắc y khoa chuẩn hóa.
* **Output:** Một báo cáo ngôn ngữ tự nhiên gồm: (1) Trạng thái tổng quát, (2) Giải thích chi tiết các chỉ số bất thường theo mức độ ưu tiên, (3) Xu hướng so với quá khứ, (4) Khuyến nghị hành động tiếp theo.

**3. Đảm bảo chất lượng (Quality & Safety):**
* **Guardrails:** Hệ thống lọc từ khóa (Keyword filter) để chặn các kết luận khẳng định bệnh hoặc kê đơn thuốc trái phép. 
* **Severity Logic:** Một lớp code truyền thống (Deterministic) nằm trên LLM để quét các chỉ số nguy cấp (Red flag). Nếu phát hiện, hệ thống sẽ ưu tiên hiển thị cảnh báo đỏ thay vì đợi LLM giải thích.

**4. Rủi ro chính:**
Mối nguy lớn nhất là sự chủ quan của bệnh nhân nếu AI đánh giá quá nhẹ nhàng. Chúng tôi xử lý bằng cách giữ tone giọng trung lập, luôn đi kèm Disclaimer và ưu tiên tính "biết thì thưa thốt, không biết thì gợi ý gặp bác sĩ".

---
*Sự thành công của Vinmec Lumina nằm ở việc giữ vững ranh giới: AI hiểu dữ liệu - Bác sĩ hiểu bệnh nhân.*


# Runbook: Cảnh báo Hallucination Proxy tăng cao

**Alert:** High Hallucination Proxy Rate  
**Severity:** P2 (Warning)  
**Owner:** Integration team (Võ Thanh Chung)

## Trigger

- Dashboard bắn alert khi `hallucination_rate > SLO_HALLUCINATION_RATE_PCT`.
- Ngưỡng hiện tại trong dashboard: `SLO_HALLUCINATION_RATE_PCT = 0.5%`.
- Alert chỉ được tính khi có feedback vote (`feedback_total > 0`).

Lưu ý đúng theo dashboard hiện tại:

- Panel 6 là `Hallucination Proxy Rate (from Useful/Not Useful feedback)`.
- `hallucination_rate` được tính từ trường `is_hallucination_proxy` trong sự kiện `feedback`.

## Ý nghĩa

Chỉ số này là proxy chất lượng dựa trên feedback người dùng, không phải phát hiện hallucination trực tiếp bằng model evaluator. Khi tỷ lệ "Không hữu ích" tăng, nguy cơ câu trả lời sai hoặc không phù hợp tăng theo.

## Cách check

1. **Xác nhận điều kiện alert trên dashboard**
   - Mở KPI `Hallucination Proxy` và so sánh với `SLO 0.5%`.
   - Mở Panel 6 để xem đường `hallucination_rate` có vượt đường `SLO_line` không.

2. **Kiểm tra mẫu số feedback**
   - Kiểm tra KPI `Feedback Votes`.
   - Nếu số vote quá ít, cần đánh dấu mức độ tin cậy thấp của chỉ số.

3. **Đối chiếu dữ liệu feedback gốc**
   - Mở Raw metrics data, lọc `event = feedback`.
   - Xem các trường `is_helpful` và `is_hallucination_proxy` theo thời gian.
   - Xác định đợt tăng bất thường sau một thay đổi prompt/provider.

4. **Khoanh vùng nguyên nhân gốc**
   - Đối chiếu cùng thời điểm với Panel 1 (Latency), Panel 3 (Error Rate), Panel 5 (Tokens).
   - Nếu token tăng mạnh hoặc latency cao, ưu tiên nghi ngờ prompt quá dài hoặc model trả lời kém ổn định.

## Cách fix

1. **Mitigation ngay lập tức**
   - Chuyển provider/model đang ổn định hơn nếu vừa có thay đổi gần đây.
   - Tạm thời rút gọn độ dài câu trả lời, ưu tiên câu trả lời ngắn và bám sát dữ liệu đầu vào.

2. **Tối ưu prompt để giảm sai lệch**
   - Thêm ràng buộc rõ ràng: không bịa dữ liệu, không kết luận khi thiếu thông tin.
   - Yêu cầu model nêu giới hạn và đề nghị bổ sung dữ liệu khi cần.

3. **Tăng chất lượng feedback loop**
   - Khuyến khích người dùng bấm Hữu ích/Không hữu ích để có đủ mẫu đánh giá.
   - Kiểm tra UI/lưu trữ feedback để đảm bảo sự kiện `feedback` được ghi nhận đầy đủ.

4. **Rollback thay đổi gần nhất nếu cần**
   - Nếu alert tăng ngay sau một thay đổi prompt/model, rollback về cấu hình trước đó.
   - Theo dõi lại Panel 6 trong 10-15 phút sau rollback.

## Verify sau khi fix

- Trong 10-15 phút sau mitigation:
- `Hallucination Proxy` giảm và duy trì dưới 0.5%.
- Panel 6 quay về dưới `SLO_line`.
- Tỷ lệ `Useful` cải thiện, không còn xu hướng tăng liên tục của `Not useful`.

## Resolution

Incident được coi là resolved khi Hallucination Proxy ổn định dưới ngưỡng SLO với số feedback đủ tin cậy và không còn đợt tăng bất thường.

## Contact

Team X1 - NhomX1-401-Day06 repository issues tab.

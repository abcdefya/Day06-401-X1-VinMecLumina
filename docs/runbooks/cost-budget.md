# Runbook: Cảnh báo vượt ngân sách chi phí

**Alert:** Cumulative API cost > $10/tháng  
**Severity:** P2 (Warning)  
**Owner:** Integration team (Võ Thanh Chung)

## Trigger

- Dashboard hiển thị tổng chi phí tích lũy vượt mốc $10.
- API bắt đầu trả lỗi `402 Monthly cost limit reached` khi chạm ngưỡng chặn chi phí theo user.
- Rule này tương ứng với ngân sách demo theo tháng, cần xử lý ngay để tránh gián đoạn khi demo.

## Ý nghĩa

Chi phí ước tính của LLM đã vượt ngân sách tháng. Với công thức hiện tại khoảng $0.01 cho mỗi 1K tokens, tình trạng này thường do lưu lượng tăng đột biến hoặc prompt quá dài.

## Cách check

1. **Xác nhận alert có thật trên dashboard**
   - Mở Dashboard -> Panel 4 (Cost over time), kiểm tra đường `cumulative_cost` đã vượt `budget` chưa.
   - Đối chiếu thêm KPI `Total Cost` ở phần tổng quan.

2. **Khoanh vùng nguyên nhân chi phí tăng**
   - Mở Panel 5 (Tokens in/out), kiểm tra `prompt_tokens` và `completion_tokens` có tăng bất thường không.
   - Mở Panel 2 (Traffic), xem có spike request bất thường theo thời gian không.

3. **Kiểm tra dấu hiệu loop hoặc spam request**
   - Mở Raw metrics data, lọc theo `patient_id`, `provider`, `ts`.
   - Nếu thấy cùng bệnh nhân hoặc cùng luồng gọi lặp nhanh, nghi ngờ bug vòng lặp hoặc retry quá mức.

4. **Xác nhận phạm vi ảnh hưởng**
   - Kiểm tra log/API response xem đã có lỗi `402 Monthly cost limit reached` chưa.
   - Nếu đã xuất hiện 402, xem như đã ảnh hưởng trực tiếp người dùng.

## Cách fix

1. **Giảm burn rate ngay lập tức**
   - Chuyển provider sang Groq (free tier) trong Streamlit sidebar để dừng phát sinh chi phí LLM trả phí.
   - Tạm dừng các luồng test không cần thiết.

2. **Giảm số tokens mỗi request**
   - Rút gọn prompt hệ thống trong hàm `_build_context_prompt()` của `app.py`.
   - Giới hạn dữ liệu xét nghiệm đưa vào prompt, chỉ giữ phần cần thiết cho trả lời.

3. **Xử lý lưu lượng bất thường**
   - Nếu có loop/retry bất thường, tắt tác vụ gây spam và sửa logic retry.
   - Theo dõi lại Panel 2 để xác nhận traffic về bình thường.

4. **Điều chỉnh ngân sách tạm thời (nếu bắt buộc)**
   - Chỉ nâng limit tạm thời khi cần đảm bảo demo và đã có thống nhất trong team.
   - Ghi lại lý do, thời điểm thay đổi và kế hoạch rollback sau khi incident ổn định.

## Verify sau khi fix

- Trong 10-15 phút sau khi áp dụng mitigation:
- Không còn phát sinh mới lỗi `402 Monthly cost limit reached`.
- Tốc độ tăng của `cumulative_cost` giảm rõ rệt.
- Token/request trở về mức bình thường.

## Resolution

Sự cố được coi là resolved khi:

- Alert không còn active.
- Không còn request bị chặn bởi cost guard.
- Chi phí tăng ổn định trong giới hạn cho phép.

Lưu ý: ngân sách sẽ reset đầu tháng, nhưng không chờ reset mới xử lý incident.

## Tài liệu tham chiếu chi phí

- Azure GPT-4o: khoảng $0.005/1K input, $0.015/1K output.
- Groq Llama 3.3-70b: free tier (có giới hạn tốc độ).
- Mục tiêu demo: dưới $10/tháng.

## Contact

Team X1 - NhomX1-401-Day06 repository issues tab.

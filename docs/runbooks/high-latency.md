# Runbook: Cảnh báo độ trễ P95 cao

**Alert:** P95 request latency > 5000 ms  
**Severity:** P2 (Warning)  
**Owner:** Integration team (Võ Thanh Chung)

## Trigger

- P95 latency vượt 5000 ms trong khoảng thời gian quan sát.
- Dashboard hiển thị đường P95 vượt đường SLO ở panel Latency.
- Có thể đi kèm phản ánh người dùng về phản hồi chậm hoặc timeout.

## Ý nghĩa

Percentile 95 của độ trễ đã vượt ngưỡng 5 giây, tức khoảng 1 trên 20 request chậm bất thường. Điều này làm giảm trải nghiệm người dùng và có thể do provider LLM chậm, traffic tăng đột biến, hoặc prompt/context quá nặng.

## Cách check

1. **Xác nhận alert trên dashboard**
   - Mở Dashboard -> Panel 1 (Latency), kiểm tra đường P95 có vượt SLO hay không.
   - So sánh cùng thời điểm với Panel 2 (Traffic) để loại trừ nguyên nhân do tải tăng.

2. **Khoanh vùng provider gây chậm**
   - Mở Raw metrics data, nhóm theo `provider` và so sánh `latency_ms` giữa Azure và Groq.
   - Nếu một provider cao hơn rõ rệt, nghi ngờ bottleneck phía provider đó.

3. **Phân biệt chậm do LLM hay logic nội bộ**
   - Guard node chạy Python thuần, thường rất nhanh.
   - Nếu request `is_critical=True` vẫn chậm, kiểm tra luồng gọi model và xử lý dữ liệu đầu vào.

4. **Kiểm tra tình trạng dịch vụ ngoài**
   - Azure status: https://status.azure.com
   - Groq status: https://status.groq.com

## Cách fix

1. **Mitigation ngay lập tức**
   - Chuyển provider trong Streamlit sidebar (Azure <-> Groq) để giảm latency tức thời.
   - Giảm lượng request test không cần thiết khi đang incident.

2. **Giảm khối lượng xử lý mỗi request**
   - Rút gọn prompt/context không cần thiết.
   - Giới hạn dữ liệu lab đưa vào một lần suy luận.

3. **Tối ưu nhánh xử lý chậm**
   - Kiểm tra các bước explain/suggest, tránh prompt quá dài hoặc gọi model lặp.
   - Nếu đang bật kịch bản gây chậm (ví dụ incident toggle), tắt sau khi xác nhận để phục hồi dịch vụ.

4. **Khôi phục dịch vụ ổn định**
   - Restart API nếu có dấu hiệu treo/tắc tài nguyên.
   - Theo dõi dashboard liên tục sau khi đổi cấu hình.

## Verify sau khi fix

- Trong 10-15 phút sau mitigation:
- P95 giảm xuống dưới 5000 ms và giữ ổn định.
- Không còn phản ánh timeout tăng thêm.
- Traffic và error rate không xấu đi sau khi đổi provider hoặc giảm prompt.

## Resolution

Sự cố được coi là resolved khi P95 duy trì dưới ngưỡng SLO trong cửa sổ theo dõi và hệ thống hoạt động ổn định trở lại.

## Contact

Team X1 - NhomX1-401-Day06 repository issues tab.

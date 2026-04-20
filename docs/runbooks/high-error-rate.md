# Runbook: Cảnh báo tỷ lệ lỗi cao

**Alert:** Error rate > 5%  
**Severity:** P1 (Critical)  
**Owner:** Integration team (Võ Thanh Chung)

## Trigger

- Tỷ lệ lỗi vượt 5% trong cửa sổ theo dõi.
- Dashboard hiển thị Error Rate vượt ngưỡng SLO.
- Người dùng bắt đầu gặp lỗi khi gọi các endpoint phân tích/chat.

## Ý nghĩa

Hơn 1 trên 20 request đang thất bại. Đây là incident ảnh hưởng trực tiếp chất lượng dịch vụ vì người dùng nhận lỗi thay vì kết quả phân tích xét nghiệm.

## Cách check

1. **Xác nhận tình trạng lỗi trên dashboard**
   - Mở Dashboard -> Panel 3 (Error Rate), kiểm tra đường error rate có vượt ngưỡng 5% không.
   - Đối chiếu thêm Panel 2 (Traffic) để xem lỗi có trùng với thời điểm traffic spike không.

2. **Kiểm tra mẫu lỗi trong dữ liệu thô**
   - Mở Raw metrics data, xem cột `error` để xác định lỗi phổ biến.
   - Thống kê lỗi theo thời gian, provider và loại request để khoanh vùng nhanh.

3. **Đối chiếu log dịch vụ**
   - Kiểm tra log API để xác nhận stack trace và tần suất lỗi.
   - Mục tiêu là xác định nguyên nhân gốc (thiếu env, Redis, rate limit, timeout provider...).

4. **Mẫu lỗi thường gặp**

   | Mẫu lỗi                  | Nguyên nhân khả dĩ        | Hướng xử lý                                     |
   | ------------------------ | ------------------------- | ----------------------------------------------- |
   | `OPENAI_API_KEY not set` | Thiếu biến môi trường     | Cấu hình API key trong `.env` và restart API    |
   | `GROQ_API_KEY not set`   | Thiếu biến môi trường     | Cấu hình API key trong `.env` và restart API    |
   | `Connection refused`     | Redis không hoạt động     | Khởi động lại Redis (`docker compose up redis`) |
   | `Rate limit`             | Vượt quota/tốc độ gọi API | Chuyển provider hoặc giảm tốc độ gọi            |

## Cách fix

1. **Sửa theo nguyên nhân chính**
   - Bổ sung env thiếu, sửa secret sai, hoặc khôi phục Redis theo lỗi quan sát được.
   - Với rate limit, chuyển provider tạm thời và giảm tần suất request.

2. **Khởi động lại dịch vụ sau khi sửa cấu hình**

   ```bash
   docker compose restart api
   ```

3. **Giảm tác động trong lúc khắc phục**
   - Tạm dừng các luồng test load cao.
   - Ưu tiên các request phục vụ demo chính.

4. **Xác nhận hết lỗi phát sinh mới**
   - Theo dõi log realtime để chắc không còn lỗi lặp lại.

   ```bash
   tail -f logs/$(date +%Y-%m-%d).log
   ```

## Verify sau khi fix

- Trong 10-15 phút sau xử lý:
- Error rate giảm xuống dưới 5% và duy trì ổn định.
- Không xuất hiện thêm nhóm lỗi cũ trong log.
- Các endpoint chính phản hồi bình thường.

## Resolution

Incident được coi là resolved khi error rate về dưới ngưỡng SLO, không còn lỗi lặp theo cùng nguyên nhân và dịch vụ hoạt động ổn định trở lại.

## Contact

Team X1 - NhomX1-401-Day06 repository issues tab.

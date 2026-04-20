# Dashboard Spec

## Required Layer-2 panels (Đã kiểm chứng qua hình ảnh):
1. **Latency P50/P95/P99**: Hiển thị rõ ràng ở Panel 1 (Biểu đồ đường).
2. **Traffic (Total Requests)**: Đã ghi nhận tổng số "Total Requests" là 37 requests.
3. **Error rate with breakdown**: Hệ thống đã ghi nhận "Error Rate" đạt 8.1% (Vượt ngưỡng và kích hoạt cảnh báo đỏ).
4. **Cost over time**: Đo lường tổng chi phí "Total Cost" hiện tại là $0.2590 (Ngưỡng budget là $10.0).
5. **Tokens in/out**: Quan sát rõ ở Panel 5 "Token Usage - Prompt vs Completion" (Phân tách rõ ràng bằng màu xanh và cam).
6. **Quality proxy**: Đo lường thông qua "Hallucination Proxy Rate" tại Panel 6 (Đang ở mức 0.00%, dưới ngưỡng SLO 0.5%).

## Quality bar checklist:
- [x] **Default time range**: 1 hour (Đúng theo đặc tả).
- [x] **Auto refresh**: Đã được cấu hình tự động làm mới mỗi 2 giây (Hiển thị rõ thanh đếm ngược trong mục Dashboard settings).
- [x] **Visible threshold/SLO line**: Các đường SLO line được cấu hình trong bảng "SLO Table" và hiển thị target trên các thẻ KPI.
- [x] **Units clearly labeled**: Đơn vị chuẩn (ms cho Latency, % cho Error/Quality, $ cho Cost).
- [x] **No more than 6-8 panels**: Giao diện chính tuân thủ chính xác 6 panel yêu cầu, gọn gàng và không bị rối mắt.
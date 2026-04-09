from __future__ import annotations

from typing import Any


def _suggestions_for_severity(severity: str) -> list[str]:
    severity = (severity or "NORMAL").upper()
    if severity == "CRITICAL":
        return [
            "Đến cơ sở y tế gần nhất ngay lập tức.",
            "Không tự ý dùng thuốc. Mang theo kết quả xét nghiệm để bác sĩ xem xét khẩn cấp.",
            "Liên hệ tổng đài Vinmec hoặc bác sĩ của bạn ngay.",
        ]
    if severity == "SEE_DOCTOR":
        return [
            "Đặt lịch khám bác sĩ trong vòng 24–72 giờ.",
            "Tái xét nghiệm các chỉ số liên quan theo hướng dẫn của bác sĩ.",
            "Theo dõi triệu chứng và chia sẻ với bác sĩ khi tái khám.",
        ]
    if severity == "WATCH":
        return [
            "Theo dõi tình trạng sức khỏe và duy trì lối sống lành mạnh.",
            "Lên lịch xét nghiệm theo dõi theo hướng dẫn của bác sĩ.",
            "Đến khám sớm hơn nếu xuất hiện triệu chứng mới.",
        ]
    return [
        "Tiếp tục duy trì sức khỏe và khám định kỳ.",
        "Giữ lối sống hiện tại và tuân theo phác đồ điều trị của bác sĩ.",
    ]


def suggest_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate safe, constrained follow-up suggestions from overall severity.
    """
    if state.get("is_critical"):
        return {"suggestions": _suggestions_for_severity("CRITICAL")}

    overall = state.get("overall_severity", "NORMAL")
    return {"suggestions": _suggestions_for_severity(overall)}

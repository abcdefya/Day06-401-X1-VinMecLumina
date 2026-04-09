"""
Inline knowledge base for common lab tests in MVP scope (Vietnamese).
"""

from __future__ import annotations

LAB_KB: dict[str, dict[str, str]] = {
    "HBA1C": {
        "meaning": "Chỉ số phản ánh mức đường huyết trung bình trong 2–3 tháng qua.",
        "high_hint": "Có thể cho thấy đường huyết chưa được kiểm soát tốt.",
        "low_hint": "Có thể xảy ra trong một số trường hợp đặc biệt, nên tham khảo bác sĩ.",
        "safe_next_step": "Tái khám và xét nghiệm lại theo hướng dẫn của bác sĩ.",
    },
    "GLUCOSE_F": {
        "meaning": "Đường huyết lúc đói sau khi nhịn ăn vài giờ.",
        "high_hint": "Có thể gợi ý đường huyết đang ở mức cao.",
        "low_hint": "Có thể là dấu hiệu đường huyết thấp, cần chú ý nếu có triệu chứng.",
        "safe_next_step": "Theo dõi triệu chứng và tham khảo ý kiến bác sĩ.",
    },
    "LDL": {
        "meaning": "Cholesterol LDL (mỡ 'xấu') trong máu.",
        "high_hint": "Giá trị cao có liên quan đến nguy cơ tim mạch.",
        "low_hint": "Giá trị thấp thường không đáng lo ngại trong bối cảnh thông thường.",
        "safe_next_step": "Trao đổi với bác sĩ về lối sống và quản lý nguy cơ tim mạch.",
    },
    "HGB": {
        "meaning": "Nồng độ huyết sắc tố liên quan đến khả năng vận chuyển oxy của máu.",
        "high_hint": "Có thể liên quan đến mất nước hoặc một số tình trạng khác.",
        "low_hint": "Có thể gợi ý thiếu máu, cần được đánh giá lâm sàng.",
        "safe_next_step": "Gặp bác sĩ để đánh giá trong bối cảnh cụ thể của bạn.",
    },
    "WBC": {
        "meaning": "Số lượng bạch cầu, thường liên quan đến viêm nhiễm hoặc nhiễm trùng.",
        "high_hint": "Có thể gợi ý viêm, phản ứng stress hoặc nhiễm trùng.",
        "low_hint": "Có thể gợi ý số lượng tế bào miễn dịch giảm, cần theo dõi.",
        "safe_next_step": "Kết hợp với triệu chứng lâm sàng để đánh giá.",
    },
    "PLATELET": {
        "meaning": "Số lượng tiểu cầu liên quan đến khả năng đông máu.",
        "high_hint": "Có thể làm tăng nguy cơ đông máu trong một số trường hợp.",
        "low_hint": "Có thể làm tăng nguy cơ chảy máu, cần theo dõi y tế.",
        "safe_next_step": "Tham khảo bác sĩ, đặc biệt nếu có dấu hiệu bầm tím hoặc chảy máu.",
    },
    "AST": {
        "meaning": "Enzyme gan có thể tăng khi tế bào gan hoặc cơ bị tổn thương.",
        "high_hint": "Có thể gợi ý gan hoặc cơ đang chịu áp lực.",
        "low_hint": "Thường không có ý nghĩa lâm sàng khi giá trị thấp.",
        "safe_next_step": "Đánh giá cùng ALT và bối cảnh lâm sàng với bác sĩ.",
    },
    "ALT": {
        "meaning": "Enzyme gan thường dùng để theo dõi tổn thương tế bào gan.",
        "high_hint": "Có thể gợi ý viêm hoặc tổn thương gan.",
        "low_hint": "Thường không có ý nghĩa lâm sàng khi giá trị thấp.",
        "safe_next_step": "Tái kiểm tra và trao đổi với bác sĩ.",
    },
    "CREATININE": {
        "meaning": "Chỉ số dùng để đánh giá chức năng lọc của thận.",
        "high_hint": "Có thể gợi ý chức năng lọc thận giảm trong một số trường hợp.",
        "low_hint": "Thường không đáng lo ngại khi xét riêng lẻ.",
        "safe_next_step": "Theo dõi xu hướng và tình trạng hydrat hóa cùng bác sĩ.",
    },
}


def get_kb_entry(test_code: str) -> dict[str, str]:
    """Return KB entry or a neutral fallback when test code is unknown."""
    return LAB_KB.get(
        test_code,
        {
            "meaning": "Chỉ số xét nghiệm cần được đánh giá trong bối cảnh lâm sàng cụ thể.",
            "high_hint": "Giá trị cao có thể có ý nghĩa lâm sàng tùy trường hợp.",
            "low_hint": "Giá trị thấp có thể có ý nghĩa lâm sàng tùy trường hợp.",
            "safe_next_step": "Trao đổi kết quả này với bác sĩ của bạn.",
        },
    )

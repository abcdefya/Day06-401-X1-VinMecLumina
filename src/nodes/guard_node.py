from src.data.reference_ranges import CRITICAL_THRESHOLDS, REFERENCE_RANGES

def guard_node(state: dict) -> dict:
    """
    Quét danh sách kết quả xét nghiệm để tìm các chỉ số vượt ngưỡng nguy kịch.
    Khớp với cấu trúc AgentState: lab_results: list[dict] -> is_critical, critical_alert
    """
    lab_results = state.get("lab_results", [])
    alerts = []
    
    for lab in lab_results:
        test_code = lab.get("test_code")
        value = lab.get("value")
        
        if not test_code or value is None:
            continue
            
        if test_code in CRITICAL_THRESHOLDS:
            thresholds = CRITICAL_THRESHOLDS[test_code]
            crit_low = thresholds.get("critical_low")
            crit_high = thresholds.get("critical_high")
            
            # Ưu tiên lấy unit và test_name trực tiếp từ data bệnh nhân (JSON)
            unit = lab.get("unit") or REFERENCE_RANGES.get(test_code, {}).get("unit", "")
            test_name = lab.get("test_name", test_code)
            
            if (crit_low is not None and value <= crit_low) or \
               (crit_high is not None and value >= crit_high):
                alerts.append({
                    "test_code": test_code,
                    "test_name": test_name, # Thêm test_name để cảnh báo rõ nghĩa hơn
                    "value": value,
                    "unit": unit,
                    "issue": "Chỉ số thấp hơn ngưỡng an toàn" if value <= crit_low else "Chỉ số cao hơn ngưỡng an toàn"
                })
                
    # Đóng gói critical_alert thành 1 dict (hoặc None) theo đúng AgentState
    alert_payload = {"alerts": alerts} if alerts else None
    
    return {
        "is_critical": len(alerts) > 0,
        "critical_alert": alert_payload
    }
from src.services.models import LabResult, ResultFlag
from src.data.reference_ranges import classify_severity, classify_overall_severity

def severity_node(state: dict) -> dict:
    """
    Use logic to assess the severity level for each test and the overall patient.
    """
    lab_data = state.get("lab_results", [])
    lab_objects = []
    
    test_name_map = {}
    
    # 1. Map dict state to object for Team Lead's function
    for item in lab_data:
        test_code = item.get("test_code", "")
        test_name = item.get("test_name", test_code)
        
        test_name_map[test_code] = test_name
        
        # Safe handling for ResultFlag enum
        flag_val = item.get("flag")
        try:
            flag_enum = ResultFlag(flag_val) if flag_val else ResultFlag.NORMAL
        except ValueError:
            flag_enum = ResultFlag.NORMAL

        # FIXED: Add test_name during LabResult initialization
        lab_obj = LabResult(
            test_code=test_code,
            test_name=test_name,  # <--- Dòng này vừa được thêm vào
            value=item.get("value", 0.0),
            unit=item.get("unit", ""),
            ref_low=item.get("ref_low"),
            ref_high=item.get("ref_high"),
            flag=flag_enum
        )
        lab_objects.append(lab_obj)
        
    # 2. Call the existing classification logic
    overall = classify_overall_severity(lab_objects)
    
    per_test_results = []
    for obj in lab_objects:
        sev = classify_severity(obj)
        per_test_results.append({
            "test_code": obj.test_code,
            "test_name": test_name_map.get(obj.test_code, obj.test_code),
            "severity": sev.name if hasattr(sev, 'name') else str(sev)
        })
        
    # 3. Return the exact format of AgentState
    return {
        "overall_severity": overall.name if hasattr(overall, 'name') else str(overall),
        "per_test_severity": per_test_results
    }
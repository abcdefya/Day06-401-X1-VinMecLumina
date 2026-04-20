from src.data.reference_ranges import CRITICAL_THRESHOLDS, REFERENCE_RANGES

def guard_node(state: dict) -> dict:
    """
    Scan the list of lab results to find indicators exceeding critical thresholds.
    Matches AgentState structure: lab_results: list[dict] -> is_critical, critical_alert
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
            
            # Prefer to get unit and test_name directly from patient data (JSON)
            unit = lab.get("unit") or REFERENCE_RANGES.get(test_code, {}).get("unit", "")
            test_name = lab.get("test_name", test_code)
            
            if (crit_low is not None and value <= crit_low) or \
               (crit_high is not None and value >= crit_high):
                alerts.append({
                    "test_code": test_code,
                    "test_name": test_name, # Add test_name for clearer alerts
                    "value": value,
                    "unit": unit,
                    "issue": "Indicator lower than safe threshold" if value <= crit_low else "Indicator higher than safe threshold"
                })
                
    # Package critical_alert into 1 dict (or None) according to AgentState
    alert_payload = {"alerts": alerts} if alerts else None
    
    return {
        "is_critical": len(alerts) > 0,
        "critical_alert": alert_payload
    }
# Runbook: Cost Budget Alert

**Alert:** Cumulative API cost > $10/month  
**Severity:** Warning  
**Owner:** Integration team (Võ Thanh Chung)

## What this means
The estimated LLM API cost has exceeded the $10/month demo budget. At ~$0.01 per 1K tokens this typically means > 1,000,000 tokens consumed.

## Immediate steps

1. **Identify cost drivers**
   - Open Dashboard → Panel 4 (Cost) and Panel 5 (Tokens)
   - Check if token counts are unusually high (prompt bloat?)

2. **Switch to free provider**
   - Groq (Llama 3.3-70b) is free-tier — switch in Streamlit sidebar
   - This brings LLM cost to $0 immediately

3. **Check for runaway requests**
   - Open Dashboard → Panel 2 (Traffic) — look for unexpected spikes
   - Check raw metrics for repeated patient IDs (loop bug?)

4. **Reduce prompt size if needed**
   - Shorten system prompt in `_build_context_prompt()` in `app.py`
   - Consider truncating lab result list for patients with many tests

## Budget reference
- Azure GPT-4o: ~$0.005/1K input, $0.015/1K output
- Groq Llama 3.3-70b: Free tier (rate limited)
- Target: < $10/month for demo usage

## Resolution
Budget resets at the start of each calendar month. Switch to Groq to stop accumulating cost immediately.

## Contact
Team X1 — NhomX1-401-Day06 repository issues tab.

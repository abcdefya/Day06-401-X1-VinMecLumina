# Runbook: High P95 Latency

**Alert:** P95 request latency > 5000 ms  
**Severity:** Warning  
**Owner:** Integration team (Võ Thanh Chung)

## What this means
The 95th percentile of workflow latency has exceeded 5 seconds, meaning 1 in 20 requests is unacceptably slow. This degrades patient experience and may indicate LLM provider slowness or resource exhaustion.

## Immediate steps

1. **Check which provider is slow**
   - Open the Dashboard → Panel 1 (Latency) and filter by `provider`
   - Compare Azure vs Groq latency in raw metrics table

2. **Switch provider if needed**
   - In the Streamlit sidebar, switch from "Azure OpenAI" to "Groq" (or vice versa)
   - Groq (Llama 3.3-70b) typically has lower latency

3. **Check if it's the LLM or the graph**
   - Guard node is pure Python — if latency is high, the bottleneck is the LLM nodes (explain/suggest)
   - Critical-path requests (is_critical=True) should have near-zero latency

4. **Check external API status**
   - Azure: https://status.azure.com
   - Groq: https://status.groq.com

## Resolution
Alert clears automatically when P95 drops below 5000 ms over a 5-minute window.

## Contact
Team X1 — NhomX1-401-Day06 repository issues tab.

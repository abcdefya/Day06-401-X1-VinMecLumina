# Runbook: High Error Rate

**Alert:** Error rate > 5%  
**Severity:** Critical  
**Owner:** Integration team (Võ Thanh Chung)

## What this means
More than 1 in 20 requests are failing. This means patients are seeing error messages instead of lab result analysis.

## Immediate steps

1. **Check error types in raw metrics**
   - Open Dashboard → Raw metrics data expander
   - Look at the `error` column for common patterns

2. **Common causes and fixes**

   | Error pattern | Likely cause | Fix |
   |---|---|---|
   | `OPENAI_API_KEY not set` | Missing env var | Add key to `.env` |
   | `GROQ_API_KEY not set` | Missing env var | Add key to `.env` |
   | `Connection refused` | Redis down | `docker compose up redis` |
   | `Rate limit` | API quota exceeded | Switch provider or wait |

3. **Restart services if needed**
   ```bash
   docker compose restart api
   ```

4. **Check logs**
   ```bash
   tail -f logs/$(date +%Y-%m-%d).log
   ```

## Resolution
Alert clears when error rate drops below 5% over a 5-minute window.

## Contact
Team X1 — NhomX1-401-Day06 repository issues tab.

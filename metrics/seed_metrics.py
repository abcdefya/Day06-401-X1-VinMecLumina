"""Run once to seed demo metrics for the dashboard."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time, random, json
from pathlib import Path

METRICS_PATH = Path(__file__).parent / "metrics.jsonl"
METRICS_PATH.parent.mkdir(exist_ok=True)

providers = ["azure", "groq"]
now = time.time()

entries = []
for i in range(30):
    ts = now - (30 - i) * 120  # every 2 min, last hour
    provider = random.choice(providers)
    latency = random.gauss(1800, 600)
    latency = max(200, latency)
    prompt_tok = random.randint(300, 800)
    comp_tok = random.randint(150, 400)
    total_tok = prompt_tok + comp_tok
    is_error = random.random() < 0.05
    is_critical = random.random() < 0.15
    entries.append({
        "ts": ts,
        "event": "workflow",
        "provider": provider,
        "patient_id": f"P{random.randint(1,5):03d}",
        "latency_ms": int(latency),
        "prompt_tokens": prompt_tok,
        "completion_tokens": comp_tok,
        "total_tokens": total_tok,
        "cost_usd": (total_tok / 1000) * 0.01,
        "is_critical": is_critical,
        "error": "RuntimeError: timeout" if is_error else None,
    })

with open(METRICS_PATH, "w") as f:
    for e in entries:
        f.write(json.dumps(e) + "\n")

print(f"Seeded {len(entries)} metrics to {METRICS_PATH}")

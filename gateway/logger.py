import json
import time
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"

# Prices per 1M tokens (input / output) as of 2025
MODEL_PRICES = {
    "gpt-4o":      {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini": {"input": 0.15,  "output": 0.60},
}
STRONG_MODEL = "gpt-4o"


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prices = MODEL_PRICES.get(model, MODEL_PRICES[STRONG_MODEL])
    return (
        prompt_tokens * prices["input"] / 1_000_000
        + completion_tokens * prices["output"] / 1_000_000
    )


def log_request(customer_id: str, req: dict, resp: dict, latency_ms: int):
    usage = resp.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    model_used = resp.get("model", STRONG_MODEL)

    actual_cost = _cost(model_used, prompt_tokens, completion_tokens)
    baseline_cost = _cost(STRONG_MODEL, prompt_tokens, completion_tokens)

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "customer": customer_id,
        "model_requested": req.get("model"),
        "model_used": model_used,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(actual_cost, 6),
        "saved_usd": round(baseline_cost - actual_cost, 6),
        "latency_ms": latency_ms,
    }

    LOGS_DIR.mkdir(exist_ok=True)
    with open(LOGS_DIR / f"{customer_id}.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

# Promptware

A drop-in API gateway that reduces LLM inference costs automatically — no code changes beyond swapping the API endpoint.

**Core levers:** query routing (route simple requests to cheaper models), prompt compression (strip redundant tokens), prompt caching (deduplicate repeated prefixes).

**Target customer:** Engineering teams spending $10k–$100k+/month on LLM API calls who want automated cost reduction without building it in-house.

## MVP Plan

**Scope:** Router only. OpenAI-compatible endpoint customers point at instead of `api.openai.com`. No dashboard, no compression, no caching — just routing. Flat monthly fee.

**Success criterion:** First paying customer running production traffic through it.

### Architecture

```
Customer app
    │  POST /v1/chat/completions (same OpenAI schema)
    ▼
Promptware Gateway  ←── classifier: simple or complex?
    │                        │
    ├── simple ──────────────▶  gpt-4o-mini  (cheap)
    └── complex ─────────────▶  gpt-4o       (full)
    │
    ▼
Response proxied back to customer (transparent)
```

**Classifier:** lightweight heuristic first (token count, keyword signals, presence of code/tools). Swap for a trained model later if needed.

### Build Milestones

| Week | Milestone |
|---|---|
| 1 | FastAPI server with `/v1/chat/completions` proxy — passes all requests through unchanged. Customers can point at it and nothing breaks. |
| 1 | Add API key auth: customers send their own OpenAI key, gateway forwards it. No key management on our side. |
| 2 | Classifier v1: heuristic routing. Simple requests → gpt-4o-mini. Log every decision + cost delta. |
| 2 | Deploy to a VPS (Hetzner/Fly.io). Latency target: <50ms added overhead. |
| 3 | Per-customer usage logging (tokens in/out, model used, estimated cost saved). No UI — just a daily email or Slack summary. |
| 3 | Onboard first beta customer. Route their real traffic, show them savings in a spreadsheet. |
| 4 | Collect feedback, tune classifier thresholds. Charge first invoice. |

### Out of Scope (MVP)

- Dashboard / UI
- Prompt compression or caching
- Multi-provider support (Anthropic, Gemini) — OpenAI only
- Our own model keys / markup model — customers bring their own keys
- SLA guarantees / uptime monitoring

### Stack

- **Runtime:** Python + FastAPI (async, minimal overhead)
- **Deploy:** Single VPS behind nginx, systemd
- **Logging:** Append-only JSONL per customer, daily summary script
- **Billing:** Manual invoice (Stripe later)

### Key Risks

- Open-source competition: RouteLLM, LiteLLM reduce willingness to pay
- Incumbents: OpenRouter, Anthropic prompt caching already exist
- Commoditization: LLM prices falling faster than the pain grows

---

## Prompt Compression: Cost vs. Accuracy

Representative results across published benchmarks (numbers vary by task — see [empirical study](https://arxiv.org/abs/2505.00019) for apples-to-apples comparison across 6 methods × 13 datasets):

| Method | Type | Compression Ratio | Accuracy Retention | Notes |
|---|---|---|---|---|
| **SelectiveContext** | Token dropping (perplexity) | 2–4x | ~90–95% | Best on short contexts |
| **LLMLingua** | Token dropping (small LM) | 2–20x | ~98.5% at 20x (GSM8K) | Task-agnostic |
| **LLMLingua-2** | Distilled token classifier | 2–14x | Similar to LLMLingua, 3–6x faster | Faster inference |
| **LongLLMLingua** | Query-aware dropping | ~4x | +21.4% vs baseline on NaturalQuestions | Can *improve* accuracy |
| **RECOMP** | Retrieval + abstractive summary | 2–5x | Competitive on RAG tasks | Query-aware; needs retriever |
| **SCOPE** | Generative rewriting | 2–5x | <2% F1 variance across ratios | Most stable across compression levels |
| **CompactPrompt** | Hybrid (drop + abbreviation) | variable | Task-dependent | End-to-end pipeline |

**Key takeaways:**
- Moderate compression (2–5x) is nearly lossless across most methods
- Query-aware methods (LongLLMLingua, RECOMP) can outperform uncompressed baselines by removing noise
- Generative methods (SCOPE) are most stable but slower to compress
- Extreme compression (10–20x) is viable mainly on reasoning tasks

**References:** [LLMLingua](https://arxiv.org/abs/2310.05736) · [LLMLingua-2](https://arxiv.org/html/2403.12968v2) · [LongLLMLingua](https://arxiv.org/abs/2310.06839) · [SCOPE](https://arxiv.org/abs/2508.15813) · [Prompt Compression Survey NAACL 2025](https://aclanthology.org/2025.naacl-long.368/) · [Empirical Study 2025](https://arxiv.org/abs/2505.00019)

## Slack

[#proj-promptware](https://jspace-headquarters.slack.com/channels/proj-promptware)

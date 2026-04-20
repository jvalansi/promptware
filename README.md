# Promptware

A drop-in API gateway that reduces LLM inference costs automatically — no code changes beyond swapping the API endpoint.

**Core levers:** query routing (route simple requests to cheaper models), prompt compression (strip redundant tokens), prompt caching (deduplicate repeated prefixes).

**Target customer:** Engineering teams spending $10k–$100k+/month on LLM API calls who want automated cost reduction without building it in-house.

## MVP Plan

**Scope:** Host [RouteLLM](https://github.com/lm-sys/routellm) (UC Berkeley/Anyscale) as a managed OpenAI-compatible proxy. Add auth, per-customer logging, and billing on top. No custom classifier, no dashboard.

**Success criterion:** First paying customer running production traffic through it.

### Architecture

```
Customer app
    │  POST /v1/chat/completions (OpenAI schema, customer's own API key)
    ▼
Auth shim (FastAPI)  ──── validates customer key, injects OpenAI key
    │
    ▼
RouteLLM server  ──── classifies request complexity
    │                        │
    ├── simple ──────────────▶  gpt-4o-mini  (cheap)
    └── complex ─────────────▶  gpt-4o       (full)
    │
    ▼
Response proxied back to customer (transparent)
```

Customers bring their own OpenAI key — no key management or markup on our side.

### Build Milestones

| Week | Milestone |
|---|---|
| 1 | Deploy RouteLLM server on a VPS (Hetzner/Fly.io). Verify it proxies correctly with default router. |
| 1 | Auth shim: FastAPI layer that validates customer API keys and forwards their OpenAI key to RouteLLM. |
| 2 | Per-customer usage logging: tokens in/out, model routed to, estimated cost saved. Daily Slack/email summary — no UI. |
| 2 | Onboard first beta customer. Route real traffic, show savings in a spreadsheet. |
| 3 | Tune RouteLLM cost threshold per customer based on their quality tolerance. Charge first invoice. |

### Out of Scope (MVP)

- Dashboard / UI
- Prompt compression or caching
- Multi-provider support (Anthropic, Gemini) — OpenAI only
- Holding customer API keys or markup model
- SLA guarantees / uptime monitoring

### Stack

- **Router:** [RouteLLM](https://github.com/lm-sys/routellm) (open-source, UC Berkeley + Anyscale)
- **Auth shim:** Python + FastAPI
- **Deploy:** Single VPS behind nginx, systemd
- **Logging:** Append-only JSONL per customer, daily summary script
- **Billing:** Manual invoice (Stripe later)

### Why RouteLLM

Research-validated: the [RouteLLM paper](https://arxiv.org/abs/2406.18665) shows ~50% cost reduction with <5% quality degradation on MMLU/MT-Bench using a classifier trained on LMSYS Chatbot Arena preference data. Building our own classifier would take weeks and perform worse. RouteLLM is the hard ML problem solved — Promptware is the productized, hosted, zero-setup wrapper.

### Key Risks

- Open-source competition: customers can self-host RouteLLM for free — value prop is the managed service
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

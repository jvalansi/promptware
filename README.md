# Promptware

A drop-in API gateway that reduces LLM inference costs automatically — no code changes beyond swapping the API endpoint.

**Core levers:** query routing (route simple requests to cheaper models), prompt compression (strip redundant tokens), prompt caching (deduplicate repeated prefixes).

**Target customer:** Engineering teams spending $10k–$100k+/month on LLM API calls who want automated cost reduction without building it in-house.

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

## Validation

See [docs/validation-plan.md](docs/validation-plan.md) for the full validation approach and current status.

## Slack

[#proj-promptware](https://jspace-headquarters.slack.com/channels/proj-promptware)

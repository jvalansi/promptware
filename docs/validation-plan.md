# Validation Plan

**Goal:** Find a paying customer before writing any code. Kill it in 1 week if no one bites.

## Approach: Google Ads + Landing Page

Run paid search ads targeting people actively searching for LLM cost optimization. Measure click-through and email signups as demand signal.

**Why this over Reddit:**
- Paid search intent is a stronger signal than upvotes
- No EC2 IP blocks, no karma requirements, no token expiry
- Quantifiable: cost per click, conversion rate, signups

**Kill signals:** <5 signups in 7 days, cost per signup >$50, nobody answers the spend question on outreach.

---

## Day-by-Day Plan

**Day 1–2 — Landing page**
- One-pager: problem, solution, "cut your LLM bill 30% — join the beta"
- Typeform collecting: name, email, monthly LLM spend
- Host on GitHub Pages

**Day 3 — Google Ads campaign**
- Keywords: "reduce LLM API costs", "openai cost optimization", "llm query routing", "llm cost reduction"
- Budget: $20–50/day
- Ad copy: "Cut Your OpenAI Bill 30% — Drop-in API proxy, no code changes. Join beta."
- Target: engineers, CTOs at companies spending on LLM APIs

**Day 4–5 — Outreach to signups**
- DM/email top signups: "What's your monthly LLM bill? Would you pay $X/mo for a drop-in gateway that cuts it 30%?"
- Offer 5 live demos — route their actual API traffic manually, show savings in a spreadsheet
- Ask for $99 pre-order

**Day 6–7 — Kill or build decision**
- 0 pre-orders → kill
- 3+ pre-orders → build MVP (router only, no dashboard)

---

## Validation Signals Already Gathered

- 8 HN posts on query routing (Switchpoint AI, PureRouter, Humiris)
- RouteLLM open-source framework by UC Berkeley + Anyscale — confirms technical approach
- NadirClaw (Feb 2026 Reddit) — community-built OpenAI-compatible router, no commercial winner yet
- Google Trends: "LLM cost optimization" peaked Mar 2026 (100/100)
- 5 Product Hunt products in adjacent space — existing paying audience

## Key Risks

- Open-source competition: RouteLLM, LiteLLM reduce willingness to pay
- Incumbent encroachment: OpenRouter, Anthropic prompt caching already exist
- Commoditization: LLM prices dropping faster than the pain grows

---

## Reddit Posts (Day 1 problem research)

Posted to gauge pain and build karma for r/LocalLLaMA:

| Subreddit | URL |
|---|---|
| r/artificial | https://www.reddit.com/r/artificial/comments/1s5sufx |
| r/PromptEngineering | https://www.reddit.com/r/PromptEngineering/comments/1s5sug0 |
| r/MachineLearning | https://www.reddit.com/r/MachineLearning/comments/1s5sukj |

Monitored daily via `reddit-tool/monitor.py` → reports to [#proj-promptware](https://jspace-headquarters.slack.com/channels/proj-promptware).

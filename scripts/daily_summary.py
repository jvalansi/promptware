#!/usr/bin/env python3
"""
Reads per-customer JSONL logs and posts a daily cost savings summary to Slack.
Run via cron: 0 8 * * * /path/to/daily_summary.py
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import httpx

LOGS_DIR = Path(__file__).parent.parent / "logs"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")


def load_yesterday(log_file: Path) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    entries = []
    for line in log_file.read_text().splitlines():
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
            if ts >= cutoff:
                entries.append(e)
        except (json.JSONDecodeError, KeyError):
            continue
    return entries


def summarize(entries: list[dict]) -> dict:
    total = len(entries)
    routed_cheap = sum(1 for e in entries if "mini" in e.get("model_used", ""))
    saved = sum(e.get("saved_usd", 0) for e in entries)
    cost = sum(e.get("cost_usd", 0) for e in entries)
    return {
        "requests": total,
        "routed_to_mini": routed_cheap,
        "cost_usd": round(cost, 4),
        "saved_usd": round(saved, 4),
        "routing_pct": round(100 * routed_cheap / total, 1) if total else 0,
    }


def build_message(date_str: str, summaries: dict[str, dict]) -> str:
    lines = [f"*Promptware Daily Summary — {date_str}*\n"]
    total_saved = 0.0
    for customer_id, s in summaries.items():
        lines.append(
            f"• *{customer_id}*: {s['requests']} requests · "
            f"{s['routing_pct']}% routed to mini · "
            f"saved *${s['saved_usd']:.4f}* · spent ${s['cost_usd']:.4f}"
        )
        total_saved += s["saved_usd"]
    lines.append(f"\n*Total saved yesterday: ${total_saved:.4f}*")
    return "\n".join(lines)


def post_to_slack(message: str):
    if not SLACK_WEBHOOK:
        print(message)
        return
    resp = httpx.post(SLACK_WEBHOOK, json={"text": message})
    if resp.status_code != 200:
        print(f"Slack error: {resp.status_code} {resp.text}", file=sys.stderr)


def main():
    date_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    summaries = {}
    for log_file in sorted(LOGS_DIR.glob("*.jsonl")):
        entries = load_yesterday(log_file)
        if entries:
            summaries[log_file.stem] = summarize(entries)

    if not summaries:
        post_to_slack(f"*Promptware* — no traffic yesterday ({date_str})")
        return

    post_to_slack(build_message(date_str, summaries))


if __name__ == "__main__":
    main()

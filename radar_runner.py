#!/usr/bin/env python3
"""Market Radar Main Orchestrator CLI.

Executes end-to-end collection of global market quotes (TW/US/HK/JP/Macro),
Anue financial news, Gatekeeper validation, Gemini AI synthesis, and Slack dispatch.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

from cnyes_news_fetcher import fetch_all_market_news
from market_data_fetcher import fetch_all_market_quotes
from market_summarizer import get_market_summary
from slack_notifier import build_slack_payload, send_slack_payload

BASE_DIR = Path(__file__).resolve().parent
SEEN_FILE = BASE_DIR / "seen_news.json"
SNAPSHOT_FILE = BASE_DIR / "latest_market_snapshot.json"


def check_gatekeeper(
    quotes: Dict[str, List[Dict[str, Any]]],
    news: Dict[str, List[Dict[str, Any]]],
) -> Tuple[bool, str]:
    """Validate minimum data completeness before dispatching notifications."""
    non_empty_quote_sectors = sum(1 for v in quotes.values() if len(v) > 0)
    non_empty_news_sectors = sum(1 for v in news.values() if len(v) > 0)
    total_quotes = sum(len(v) for v in quotes.values())
    total_news = sum(len(v) for v in news.values())

    if non_empty_quote_sectors < 3 or total_quotes < 5:
        return (
            False,
            f"行情數據不足（有效市場數: {non_empty_quote_sectors}/5, 總指標數: {total_quotes}）",
        )
    if non_empty_news_sectors < 3 or total_news < 5:
        return (
            False,
            f"新聞資料不足（有效板塊數: {non_empty_news_sectors}/5, 總新聞數: {total_news}）",
        )
    return (
        True,
        f"Gatekeeper 通過（行情指標: {total_quotes} 項, 精選新聞: {total_news} 則）",
    )


def run_pipeline(dry_run: bool = False, enforce_gate: bool = True) -> int:
    """Execute the full Market Radar pipeline."""
    print("📡 [1/4] 正在抓取全球五大市場即時行情與總經指標...")
    quotes = fetch_all_market_quotes()

    print("📰 [2/4] 正在抓取鉅亨網五大板塊財經新聞與編輯摘要...")
    seen_target = None if dry_run else SEEN_FILE
    news = fetch_all_market_news(seen_file=seen_target, per_sector_limit=4)

    ok, gate_msg = check_gatekeeper(quotes, news)
    if not ok:
        print(f"❌ Gatekeeper 檢驗未通過：{gate_msg}", file=sys.stderr)
        if enforce_gate:
            return 1
    else:
        print(f"✅ {gate_msg}")

    print("🧠 [3/4] 正在生成跨市場投資策略綜述...")
    summary_info = get_market_summary(quotes, news)
    print(f"   ➔ 摘要來源：{summary_info['source']}")

    payload = build_slack_payload(quotes, news, summary_info)

    snapshot = {
        "quotes": quotes,
        "news": news,
        "summary": summary_info,
    }
    SNAPSHOT_FILE.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if dry_run:
        print("🧪 [4/4] Dry-run 模式完成，已輸出快照至 latest_market_snapshot.json，略過 Slack 發送。")
        print("\n--- 摘要預覽 ---")
        print(summary_info["summary"])
        return 0

    print("🚀 [4/4] 正在推播情報卡片至 Slack...")
    sent = send_slack_payload(payload)
    if not sent and os.getenv("SLACK_WEBHOOK_URL"):
        return 1
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Market Radar Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="僅抓取與驗證，不實際推播 Slack 或更新已讀狀態")
    parser.add_argument("--no-gate", action="store_true", help="略過 Gatekeeper 門檻強制執行")
    args = parser.parse_args(argv)
    return run_pipeline(dry_run=args.dry_run, enforce_gate=not args.no_gate)


if __name__ == "__main__":
    sys.exit(main())

"""Slack Block Kit Intelligence Card Builder & Dispatcher for Market Radar."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, Dict, List
import urllib.request

from cnyes_news_fetcher import SECTOR_LABELS
from market_data_fetcher import MARKET_LABELS, format_quote_badge

TW_TZ = timezone(timedelta(hours=8))


def format_sector_news_block(sector_key: str, articles: List[Dict[str, Any]], max_items: int = 3) -> str:
    """Format a sector's top news items into Slack mrkdwn with clickable links and brief summaries."""
    label = SECTOR_LABELS.get(sector_key, sector_key)
    if not articles:
        return f"*{label}*\n_暫無最新焦點新聞_"

    lines: List[str] = [f"*{label}*"]
    for art in articles[:max_items]:
        title = art.get("title", "無標題").replace("|", "｜").replace("<", "‹").replace(">", "›")
        url = art.get("url", "https://news.cnyes.com")
        badge = "🆕 " if art.get("is_new", False) else "• "
        summary = (art.get("summary") or "").strip()

        if summary:
            first_point = summary.split(" / ")[0].strip()
            if len(first_point) > 80:
                first_point = first_point[:78] + "…"
            lines.append(f"{badge}<{url}|*{title}*>\n   └ _{first_point}_")
        else:
            lines.append(f"{badge}<{url}|*{title}*>")

    return "\n".join(lines)


def build_slack_payload(
    quotes: Dict[str, List[Dict[str, Any]]],
    news: Dict[str, List[Dict[str, Any]]],
    summary_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Assemble the complete Slack Block Kit payload for all 5 markets."""
    now_tw = datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M (UTC+8)")
    total_articles = sum(len(v) for v in news.values())

    blocks: List[Dict[str, Any]] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🌏 MARKET RADAR｜全球五大市場財經情報與數據雷達",
                "emoji": True,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"🕒 *推播時間*：`{now_tw}`  ｜  "
                        f"📡 *精選新聞*：`{total_articles} 則`  ｜  "
                        f"🌐 *版圖*：`台股・美股・港股・日股・總經`"
                    ),
                }
            ],
        },
        {"type": "divider"},
    ]

    # 1. Global Market Quotes Dashboard
    quote_lines: List[str] = ["📊 *【全球五大市場即時行情與總經指標】*"]
    for sector_key in ("tw_stock", "us_stock", "hk_stock", "jp_stock", "macro"):
        label = MARKET_LABELS.get(sector_key, sector_key)
        sector_quotes = quotes.get(sector_key, [])
        if sector_quotes:
            badges = "  ｜  ".join(format_quote_badge(q) for q in sector_quotes)
            quote_lines.append(f"• *{label}*：{badges}")

    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(quote_lines),
            },
        }
    )
    blocks.append({"type": "divider"})

    # 2. Gemini AI Cross-Market Strategy Summary
    ai_badge = (
        "🧠 *【Gemini AI 跨市場首席策略綜述】*"
        if summary_info.get("is_llm")
        else "📈 *【跨市場量化指標綜述】*"
    )
    summary_text = summary_info.get("summary", "").strip()
    quoted_summary = "\n".join(f"> {ln}" for ln in summary_text.splitlines() if ln.strip())

    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{ai_badge}\n{quoted_summary}",
            },
        }
    )
    blocks.append({"type": "divider"})

    # 3. Five Market News Sections (TW / US / HK / JP / Macro)
    for sector_key in ("tw_stock", "us_stock", "hk_stock", "jp_stock", "macro"):
        sector_articles = news.get(sector_key, [])
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": format_sector_news_block(sector_key, sector_articles, max_items=3),
                },
            }
        )

    blocks.append({"type": "divider"})
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 *Market Radar* • 資料來源：鉅亨網 (Anue) & Yahoo Finance • Gemini AI 跨市場投研引擎",
                }
            ],
        }
    )

    return {
        "attachments": [
            {
                "color": "#0A84FF",
                "blocks": blocks,
            }
        ]
    }


def send_slack_payload(payload: Dict[str, Any], webhook_url: str | None = None) -> bool:
    """POST the Block Kit payload to Slack Incoming Webhook."""
    target_url = (webhook_url or os.getenv("SLACK_WEBHOOK_URL") or "").strip()
    if not target_url:
        print("⚠️ 未設定 SLACK_WEBHOOK_URL 環境變數，略過 Slack 推播。")
        return False

    try:
        req = urllib.request.Request(
            target_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                print("✅ 成功推播【全球五大市場財經情報卡片】至 Slack！")
                return True
            print(f"⚠️ Slack 回應狀態碼異常: {resp.status}")
            return False
    except Exception as e:
        print(f"❌ 發送 Slack 失敗: {e}")
        return False

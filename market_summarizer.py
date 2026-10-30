"""Cross-Market Intelligence Summarizer (Gemini AI + Rule-Based Fallback).

Synthesizes real-time market quotes and Anue financial news across
TW, US, HK, JP, and Macro sectors into actionable investment commentary.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from cnyes_news_fetcher import SECTOR_LABELS
from market_data_fetcher import MARKET_LABELS

CANDIDATE_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)


def build_prompt_context(
    quotes: Dict[str, List[Dict[str, Any]]],
    news: Dict[str, List[Dict[str, Any]]],
) -> str:
    """Format market quotes and top news summaries into a structured LLM prompt."""
    lines: List[str] = ["【一、全球五大市場即時行情數據】"]
    for sector_key, label in MARKET_LABELS.items():
        sector_quotes = quotes.get(sector_key, [])
        if not sector_quotes:
            continue
        q_parts = [
            f"{q['name']} {q['price']:,.2f} ({q['change_pct']:+.2f}%)"
            for q in sector_quotes
        ]
        lines.append(f"- {label}：{' | '.join(q_parts)}")

    lines.append("\n【二、鉅亨網五大板塊重點新聞與編輯摘要】")
    for sector_key, label in SECTOR_LABELS.items():
        articles = news.get(sector_key, [])
        if not articles:
            continue
        lines.append(f"\n[{label}]")
        for idx, art in enumerate(articles[:4], 1):
            title = art.get("title", "")
            summary = art.get("summary", "")
            if summary:
                lines.append(f"{idx}. {title}\n   摘要：{summary}")
            else:
                lines.append(f"{idx}. {title}")

    return "\n".join(lines)


def generate_gemini_summary(
    quotes: Dict[str, List[Dict[str, Any]]],
    news: Dict[str, List[Dict[str, Any]]],
    api_key: str,
) -> Optional[str]:
    """Call Google Gemini API to produce cross-market macro and equity analysis."""
    context_block = build_prompt_context(quotes, news)
    prompt = f"""你是一位管理跨國部位的資深宏觀與股票策略長（CIO）。
請根據以下最新的【全球五大市場即時行情數據】與【鉅亨網五大板塊重點新聞與編輯摘要】，撰寫一份精煉、高資訊密度的跨市場投資洞察：

{context_block}

請嚴格依下列三點結構輸出（每點 1~2 句話，直接切入數據與具體事件，不講空話）：
1. *【全球宏觀與資金風向】*：結合美債殖利率、美元/日圓、美元/台幣與美台日港指數漲跌，點出當前資金是趨險（Risk-On）或避險（Risk-Off）及其核心驅動因素。
2. *【台・美・日・港 跨市場連動】*：剖析美股科技/費半、日股半導體與權值、台股AI供應鏈（如台積電/鴻海）及港股科網之間的最新產業傳導與財報/政策催化劑。
3. *【焦點標的與風險雷達】*：點出本時段最值得關注的受惠/受害族群與短線必須留意的總經或政策風險。

撰寫要求：
- 使用繁體中文，語氣專業精準，總字數控制在 220~320 字以內。
- 不要加任何開場白或結語，直接輸出三點內容。"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 650,
        },
    }

    for model_name in CANDIDATE_MODELS:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            text = str(parts[0]["text"]).strip()
                            if text:
                                return text
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            print(f"⚠️ Gemini API HTTP {e.code} ({model_name})")
        except Exception as e:
            print(f"⚠️ Gemini API 調用異常 ({model_name}): {e}")

    return None


def generate_rule_based_summary(
    quotes: Dict[str, List[Dict[str, Any]]],
    news: Dict[str, List[Dict[str, Any]]],
) -> str:
    """Generate a data-driven fallback summary when Gemini API key is unavailable."""
    index_Map: List[str] = []
    for sector_key in ("tw_stock", "us_stock", "hk_stock", "jp_stock", "macro"):
        items = quotes.get(sector_key, [])
        if items:
            lead = items[0]
            index_Map.append(f"{lead['name']} {lead['price']:,.2f} ({lead['change_pct']:+.2f}%)")

    quote_line = "、".join(index_Map) if index_Map else "全球主要指數持續波動"

    top_headlines: List[str] = []
    for sector_key, label in SECTOR_LABELS.items():
        arts = news.get(sector_key, [])
        if arts:
            top_headlines.append(f"{label}聚焦「{arts[0]['title']}」")

    news_line = "；".join(top_headlines[:3]) if top_headlines else "各市場焦點新聞持續更新中"

    return (
        f"1. *【全球宏觀與資金風向】*：最新跨市場指標顯示 {quote_line}，資金圍繞利率預期與匯率波動進行跨區配置。\n"
        f"2. *【台・美・日・港 跨市場連動】*：{news_line}，科技硬體供應鏈與大型權值股維持高度連動。\n"
        f"3. *【焦點標的與風險雷達】*：建議密切追蹤美債殖利率、日圓與台幣匯率走勢對外資籌碼面的即時影響。"
    )


def get_market_summary(
    quotes: Dict[str, List[Dict[str, Any]]],
    news: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Main entry point: returns Gemini AI summary or falls back to rule engine."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        llm_text = generate_gemini_summary(quotes, news, api_key)
        if llm_text:
            return {
                "source": "Gemini AI 跨市場首席策略綜述",
                "summary": llm_text,
                "is_llm": True,
            }

    return {
        "source": "量化指標規則引擎（離線降級模式）",
        "summary": generate_rule_based_summary(quotes, news),
        "is_llm": False,
    }

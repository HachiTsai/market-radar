"""Unit tests for slack_notifier.py and radar_runner.py Gatekeeper."""
from __future__ import annotations

from radar_runner import check_gatekeeper
from slack_notifier import build_slack_payload, format_sector_news_block


def test_format_sector_news_block():
    articles = [
        {
            "id": "1",
            "title": "台積電營收創高",
            "summary": "10月營收突破3000億 / 法人看好Q4",
            "url": "https://news.cnyes.com/news/id/1",
            "is_new": True,
        }
    ]
    block_text = format_sector_news_block("tw_stock", articles)
    assert "🇹🇼 台股焦點" in block_text
    assert "🆕 <https://news.cnyes.com/news/id/1|*台積電營收創高*>" in block_text
    assert "10月營收突破3000億" in block_text


def test_build_slack_payload_structure():
    quotes = {
        "tw_stock": [{"name": "台股加權", "price": 23000.0, "change_pct": 0.5}],
        "us_stock": [{"name": "S&P 500", "price": 5800.0, "change_pct": -0.2}],
        "hk_stock": [{"name": "恆生指數", "price": 20500.0, "change_pct": 1.1}],
        "jp_stock": [{"name": "日經225", "price": 39000.0, "change_pct": 0.8}],
        "macro": [{"name": "美債10Y殖利率", "price": 4.2, "change_pct": -0.5}],
    }
    news = {
        k: [{"id": "1", "title": f"{k} 焦點", "summary": "摘要", "url": "https://news.cnyes.com", "is_new": True}]
        for k in ("tw_stock", "us_stock", "hk_stock", "jp_stock", "macro")
    }
    summary_info = {"source": "Gemini AI", "summary": "1. 測試綜述", "is_llm": True}

    payload = build_slack_payload(quotes, news, summary_info)
    assert "attachments" in payload
    blocks = payload["attachments"][0]["blocks"]
    assert blocks[0]["type"] == "header"
    assert any("Gemini AI 跨市場首席策略綜述" in str(b) for b in blocks)


def test_check_gatekeeper():
    good_quotes = {
        k: [{"name": k, "price": 100.0, "change_pct": 1.0}, {"name": f"{k}2", "price": 50.0, "change_pct": 0.5}]
        for k in ("tw_stock", "us_stock", "hk_stock")
    }
    good_news = {
        k: [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
        for k in ("tw_stock", "us_stock", "hk_stock")
    }
    ok, msg = check_gatekeeper(good_quotes, good_news)
    assert ok is True
    assert "通過" in msg

    bad_quotes = {"tw_stock": [{"name": "TW", "price": 100.0, "change_pct": 1.0}]}
    ok_bad, _ = check_gatekeeper(bad_quotes, good_news)
    assert ok_bad is False

"""Unit tests for market_summarizer.py."""
from __future__ import annotations

from market_summarizer import build_prompt_context, generate_rule_based_summary, get_market_summary


def test_build_prompt_context_and_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    quotes = {
        "tw_stock": [{"name": "台股加權", "price": 23000.0, "change_pct": 1.2}],
        "us_stock": [{"name": "費城半導體", "price": 5200.0, "change_pct": 2.1}],
        "hk_stock": [],
        "jp_stock": [],
        "macro": [],
    }
    news = {
        "tw_stock": [{"title": "台積電法說報喜", "summary": "Q4毛利率超預期"}],
        "us_stock": [{"title": "輝達Blackwell出貨強勁", "summary": ""}],
        "hk_stock": [],
        "jp_stock": [],
        "macro": [],
    }

    ctx = build_prompt_context(quotes, news)
    assert "台股加權 23,000.00 (+1.20%)" in ctx
    assert "台積電法說報喜" in ctx
    assert "Q4毛利率超預期" in ctx

    rule_txt = generate_rule_based_summary(quotes, news)
    assert "全球宏觀與資金風向" in rule_txt
    assert "台積電法說報喜" in rule_txt

    res = get_market_summary(quotes, news)
    assert res["is_llm"] is False
    assert "全球宏觀與資金風向" in res["summary"]

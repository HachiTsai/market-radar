"""Unit tests for market_data_fetcher.py."""
from __future__ import annotations

from market_data_fetcher import format_quote_badge, parse_yahoo_chart_payload


def test_parse_yahoo_chart_payload_valid():
    sample = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": 1050.0,
                        "chartPreviousClose": 1000.0,
                        "currency": "TWD",
                    }
                }
            ]
        }
    }
    res = parse_yahoo_chart_payload(sample, name="台積電", symbol="2330.TW")
    assert res is not None
    assert res["name"] == "台積電"
    assert res["symbol"] == "2330.TW"
    assert res["price"] == 1050.0
    assert res["change"] == 50.0
    assert res["change_pct"] == 5.0
    assert res["currency"] == "TWD"


def test_parse_yahoo_chart_payload_empty_or_invalid():
    assert parse_yahoo_chart_payload({}, name="X", symbol="X") is None
    assert parse_yahoo_chart_payload({"chart": {"result": []}}, name="X", symbol="X") is None
    assert parse_yahoo_chart_payload({"chart": {"result": [{"meta": {}}]}}, name="X", symbol="X") is None


def test_format_quote_badge():
    up_quote = {"name": "台股加權", "price": 23500.5, "change_pct": 1.25}
    down_quote = {"name": "美元/台幣", "price": 32.5, "change_pct": -0.4}
    flat_quote = {"name": "美債10Y", "price": 4.2, "change_pct": 0.0}

    assert "🔺+1.25%" in format_quote_badge(up_quote)
    assert "23,500.50" in format_quote_badge(up_quote)
    assert "🔻-0.40%" in format_quote_badge(down_quote)
    assert "➖+0.00%" in format_quote_badge(flat_quote)

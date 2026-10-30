"""Global Market & Macroeconomic Data Fetcher (TW / US / HK / JP / Macro).

Fetches real-time/latest index, benchmark stock, yield, FX, and commodity quotes
from Yahoo Finance v8 Chart API using Python standard library only.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0"
YAHOO_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")

# 5 Core Market & Macro Indicator Groups
MARKET_INDICATORS: Dict[str, List[Dict[str, str]]] = {
    "tw_stock": [
        {"name": "台股加權", "symbol": "^TWII"},
        {"name": "台積電", "symbol": "2330.TW"},
        {"name": "鴻海", "symbol": "2317.TW"},
        {"name": "聯發科", "symbol": "2454.TW"},
    ],
    "us_stock": [
        {"name": "S&P 500", "symbol": "^GSPC"},
        {"name": "那斯達克", "symbol": "^IXIC"},
        {"name": "費城半導體", "symbol": "^SOX"},
        {"name": "輝達(NVDA)", "symbol": "NVDA"},
        {"name": "台積電ADR", "symbol": "TSM"},
    ],
    "hk_stock": [
        {"name": "恆生指數", "symbol": "^HSI"},
        {"name": "恆生科技ETF", "symbol": "3032.HK"},
        {"name": "騰訊控股", "symbol": "0700.HK"},
    ],
    "jp_stock": [
        {"name": "日經225", "symbol": "^N225"},
        {"name": "東京威力科創", "symbol": "8035.T"},
        {"name": "愛德萬測試", "symbol": "6857.T"},
    ],
    "macro": [
        {"name": "美債10Y殖利率", "symbol": "^TNX"},
        {"name": "美元/台幣", "symbol": "TWD=X"},
        {"name": "美元/日圓", "symbol": "JPY=X"},
        {"name": "黃金期貨", "symbol": "GC=F"},
        {"name": "比特幣", "symbol": "BTC-USD"},
    ],
}

MARKET_LABELS: Dict[str, str] = {
    "tw_stock": "🇹🇼 台股市場",
    "us_stock": "🇺🇸 美股市場",
    "hk_stock": "🇭🇰 港股市場",
    "jp_stock": "🇯🇵 日股市場",
    "macro": "🌐 總經與匯率",
}


def parse_yahoo_chart_payload(payload: Dict[str, Any], name: str, symbol: str) -> Optional[Dict[str, Any]]:
    """Parse Yahoo Finance v8 chart JSON payload into a normalized quote dict."""
    try:
        results = payload.get("chart", {}).get("result")
        if not results:
            return None
        meta = results[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        if price is None:
            return None
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        change = float(price) - float(prev_close)
        change_pct = (change / float(prev_close) * 100.0) if float(prev_close) != 0 else 0.0
        return {
            "name": name,
            "symbol": symbol,
            "price": round(float(price), 2),
            "prev_close": round(float(prev_close), 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "currency": meta.get("currency", ""),
        }
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def fetch_single_quote(name: str, symbol: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """Fetch a single symbol quote from Yahoo Finance v8 Chart endpoint with host fallback."""
    encoded_sym = urllib.parse.quote(symbol)
    for host in YAHOO_HOSTS:
        url = f"https://{host}/v8/finance/chart/{encoded_sym}?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw = json.loads(resp.read().decode("utf-8", errors="replace"))
                    parsed = parse_yahoo_chart_payload(raw, name=name, symbol=symbol)
                    if parsed is not None:
                        return parsed
        except Exception:
            continue
    return None


def fetch_all_market_quotes(max_workers: int = 4) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch all 5 market/macro sector quotes concurrently."""
    results: Dict[str, List[Dict[str, Any]]] = {k: [] for k in MARKET_INDICATORS}
    tasks: List[tuple[str, int, str, str]] = []

    for group_key, items in MARKET_INDICATORS.items():
        for idx, item in enumerate(items):
            tasks.append((group_key, idx, item["name"], item["symbol"]))

    fetched_map: Dict[tuple[str, int], Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {
            executor.submit(fetch_single_quote, name, sym): (group_key, idx)
            for group_key, idx, name, sym in tasks
        }
        for future in as_completed(future_to_key):
            g_key, idx = future_to_key[future]
            quote = future.result()
            if quote is not None:
                fetched_map[(g_key, idx)] = quote

    for group_key, items in MARKET_INDICATORS.items():
        for idx in range(len(items)):
            if (group_key, idx) in fetched_map:
                results[group_key].append(fetched_map[(group_key, idx)])

    return results


def format_quote_badge(quote: Dict[str, Any]) -> str:
    """Format a single quote into a compact Slack markdown string."""
    name = quote.get("name", "")
    price = quote.get("price", 0.0)
    pct = quote.get("change_pct", 0.0)
    arrow = "🔺" if pct > 0 else ("🔻" if pct < 0 else "➖")
    price_str = f"{price:,.2f}".rstrip("0").rstrip(".") if price < 1000 else f"{price:,.2f}"
    return f"*{name}* `{price_str}` ({arrow}{pct:+.2f}%)"

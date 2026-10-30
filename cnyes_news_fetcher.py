"""Anue (cnyes.com) Multi-Market Financial News Fetcher (TW / US / HK / JP / Macro).

Extracts structured news items (including editorial 3-point summaries, keywords,
related stock tickers, and timestamps) directly from Anue's Next.js SSR stream,
supplemented by Google News RSS for Japan stock coverage.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Set
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

NEXT_STREAM_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)')

JP_KEYWORDS = (
    "日股",
    "日經",
    "東證",
    "日本",
    "日銀",
    "日圓",
    "日元",
    "植田",
    "東京威力",
    "愛德萬",
    "軟銀",
    "豐田",
    "索尼",
    "任天堂",
    "BOJ",
    "Nikkei",
)

SECTOR_LABELS: Dict[str, str] = {
    "tw_stock": "🇹🇼 台股焦點",
    "us_stock": "🇺🇸 美股雷達",
    "hk_stock": "🇭🇰 港股動態",
    "jp_stock": "🇯🇵 日股觀察",
    "macro": "🌐 總經與匯債",
}


def clean_text(raw: str | None) -> str:
    """Unescape HTML entities and normalize whitespace."""
    if not raw:
        return ""
    unescaped = html.unescape(raw)
    lines = [ln.strip() for ln in unescaped.splitlines() if ln.strip()]
    return " / ".join(lines)


def parse_cnyes_ssr_html(html_text: str) -> List[Dict[str, Any]]:
    """Extract news objects from Anue Next.js SSR hydration scripts."""
    scripts = NEXT_STREAM_RE.findall(html_text)
    stream_parts: List[str] = []
    for chunk in scripts:
        try:
            decoded = json.loads(f'"{chunk}"')
            stream_parts.append(decoded)
        except Exception:
            continue

    stream = "".join(stream_parts)
    if not stream:
        return []

    decoder = json.JSONDecoder()
    extracted: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for match in re.finditer(r'"data"\s*:\s*\[', stream):
        arr_start = match.end() - 1
        try:
            arr, _ = decoder.raw_decode(stream, arr_start)
            if isinstance(arr, list):
                for obj in arr:
                    if not isinstance(obj, dict):
                        continue
                    news_id = obj.get("newsId")
                    title = clean_text(obj.get("title"))
                    if not news_id or not title:
                        continue
                    nid_str = str(news_id)
                    if nid_str in seen_ids:
                        continue
                    seen_ids.add(nid_str)

                    keywords = obj.get("keyword") or []
                    if not isinstance(keywords, list):
                        keywords = []

                    stocks = obj.get("stock") or []
                    if not isinstance(stocks, list):
                        stocks = []

                    extracted.append(
                        {
                            "id": nid_str,
                            "title": title,
                            "summary": clean_text(obj.get("summary")),
                            "keywords": [str(k) for k in keywords if k],
                            "stocks": [str(s) for s in stocks if s],
                            "publish_at": int(obj.get("publishAt") or 0),
                            "category_name": clean_text(obj.get("categoryName")),
                            "url": f"https://news.cnyes.com/news/id/{nid_str}",
                        }
                    )
        except Exception:
            continue

    return extracted


def fetch_cnyes_category(category: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch and parse a single Anue category page."""
    url = f"https://news.cnyes.com/news/cat/{category}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return []
            html_text = resp.read().decode("utf-8", errors="replace")
            return parse_cnyes_ssr_html(html_text)
    except Exception:
        return []


def is_japan_related(article: Dict[str, Any]) -> bool:
    """Determine if a news item is related to Japan stock market or BOJ/JPY."""
    haystack = " ".join(
        [
            article.get("title", ""),
            article.get("summary", ""),
            " ".join(article.get("keywords", [])),
        ]
    )
    return any(kw in haystack for kw in JP_KEYWORDS)


def parse_google_rss_xml(xml_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse Google News RSS XML into normalized news dicts."""
    articles: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.findall(".//item"):
            raw_title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            guid = (item.findtext("guid") or link).strip()
            if not raw_title or raw_title.startswith("頭條新聞"):
                continue
            title = re.sub(r"\s*-\s*鉅亨網.*$", "", raw_title).strip()
            articles.append(
                {
                    "id": f"rss_{abs(hash(guid)) % 10**10}",
                    "title": clean_text(title),
                    "summary": "",
                    "keywords": ["日股", "鉅亨網"],
                    "stocks": [],
                    "publish_at": 0,
                    "category_name": "日股觀察",
                    "url": link,
                }
            )
    except Exception:
        return []
    return articles


def fetch_jp_rss_supplement(timeout: int = 8) -> List[Dict[str, Any]]:
    """Fetch Japan market news from Anue via Google News RSS as a supplement."""
    query = urllib.parse.quote("日股 OR 日經 OR 日本央行 OR 日圓 site:cnyes.com when:2d")
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return []
            return parse_google_rss_xml(resp.read())
    except Exception:
        return []


def load_seen_ids(seen_file: Path) -> Set[str]:
    """Load previously pushed article IDs from JSON state file."""
    if not seen_file.exists():
        return set()
    try:
        data = json.loads(seen_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return set(str(x) for x in data.get("seen_ids", []))
        if isinstance(data, list):
            return set(str(x) for x in data)
    except Exception:
        pass
    return set()


def save_seen_ids(seen_file: Path, seen_ids: Set[str], max_keep: int = 500) -> None:
    """Persist seen article IDs to JSON state file (bounded to max_keep)."""
    sorted_ids = sorted(seen_ids)[-max_keep:]
    payload = {"seen_ids": sorted_ids}
    seen_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def rank_and_deduplicate(
    articles: List[Dict[str, Any]],
    seen_ids: Set[str],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Deduplicate by title/id, mark new items, prioritize articles with editorial summaries."""
    unique: List[Dict[str, Any]] = []
    seen_titles: Set[str] = set()

    for art in articles:
        title = art.get("title", "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        art_copy = dict(art)
        art_copy["is_new"] = str(art.get("id")) not in seen_ids
        unique.append(art_copy)

    # Sort: unseen first, then articles with editorial summary, then most recent timestamp
    unique.sort(
        key=lambda x: (
            1 if x.get("is_new") else 0,
            1 if x.get("summary") else 0,
            x.get("publish_at", 0),
        ),
        reverse=True,
    )
    return unique[:limit]


def fetch_all_market_news(
    seen_file: Path | None = None,
    per_sector_limit: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch news across all 5 target sectors concurrently and update seen state."""
    seen_ids = load_seen_ids(seen_file) if seen_file else set()

    cnyes_cats = ["tw_stock", "us_stock", "hk_stock", "wd_stock", "wd_macro", "forex"]
    raw_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in cnyes_cats}
    jp_rss_items: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=7) as executor:
        future_map = {executor.submit(fetch_cnyes_category, c): c for c in cnyes_cats}
        rss_future = executor.submit(fetch_jp_rss_supplement)

        for future in as_completed(future_map):
            cat = future_map[future]
            raw_by_cat[cat] = future.result()
        jp_rss_items = rss_future.result()

    # Assemble 5 target sectors
    jp_candidates = [
        art
        for art in (raw_by_cat["wd_stock"] + raw_by_cat["forex"] + raw_by_cat["wd_macro"])
        if is_japan_related(art)
    ] + jp_rss_items

    macro_candidates = raw_by_cat["wd_macro"] + raw_by_cat["forex"]

    sector_pools: Dict[str, List[Dict[str, Any]]] = {
        "tw_stock": raw_by_cat["tw_stock"],
        "us_stock": raw_by_cat["us_stock"],
        "hk_stock": raw_by_cat["hk_stock"],
        "jp_stock": jp_candidates,
        "macro": macro_candidates,
    }

    final_news: Dict[str, List[Dict[str, Any]]] = {}
    new_seen_ids = set(seen_ids)

    for sector, pool in sector_pools.items():
        selected = rank_and_deduplicate(pool, seen_ids=seen_ids, limit=per_sector_limit)
        final_news[sector] = selected
        for item in selected:
            new_seen_ids.add(str(item["id"]))

    if seen_file is not None:
        save_seen_ids(seen_file, new_seen_ids)

    return final_news

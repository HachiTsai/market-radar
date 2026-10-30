"""Unit tests for cnyes_news_fetcher.py."""
from __future__ import annotations

import json
from pathlib import Path

from cnyes_news_fetcher import (
    clean_text,
    is_japan_related,
    load_seen_ids,
    parse_cnyes_ssr_html,
    parse_google_rss_xml,
    rank_and_deduplicate,
    save_seen_ids,
)


def test_clean_text():
    raw = "第一行重點&#10;第二行 &amp; 關鍵數據\n\n第三行"
    assert clean_text(raw) == "第一行重點 / 第二行 & 關鍵數據 / 第三行"
    assert clean_text(None) == ""


def test_parse_cnyes_ssr_html():
    inner_json = json.dumps(
        {
            "state": {
                "data": {
                    "pages": [
                        {
                            "data": [
                                {
                                    "newsId": 6641677,
                                    "title": "台積電CoWoS產能翻倍&#10;外資調升目標價",
                                    "summary": "重點一&#10;重點二",
                                    "keyword": ["台積電", "CoWoS"],
                                    "stock": ["2330"],
                                    "publishAt": 1793335856,
                                    "categoryName": "台股新聞",
                                }
                            ]
                        }
                    ]
                }
            }
        },
        ensure_ascii=False,
    )
    escaped_chunk = json.dumps(inner_json, ensure_ascii=False)[1:-1]
    fake_html = f'<script>self.__next_f.push([1,"16:{escaped_chunk}"])</script>'

    items = parse_cnyes_ssr_html(fake_html)
    assert len(items) == 1
    assert items[0]["id"] == "6641677"
    assert items[0]["title"] == "台積電CoWoS產能翻倍 / 外資調升目標價"
    assert items[0]["summary"] == "重點一 / 重點二"
    assert items[0]["keywords"] == ["台積電", "CoWoS"]
    assert items[0]["stocks"] == ["2330"]
    assert items[0]["url"] == "https://news.cnyes.com/news/id/6641677"


def test_is_japan_related():
    jp_art = {"title": "日銀總裁植田和男暗示升息 日圓急升", "summary": "", "keywords": []}
    us_art = {"title": "蘋果發表新款 Mac", "summary": "", "keywords": ["Apple"]}
    assert is_japan_related(jp_art) is True
    assert is_japan_related(us_art) is False


def test_parse_google_rss_xml():
    xml_sample = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
      <item>
        <title>日經225指數大漲逾700點 半導體設備股領軍 - 鉅亨網</title>
        <link>https://news.cnyes.com/news/id/12345</link>
        <guid>guid-12345</guid>
      </item>
    </channel></rss>""".encode("utf-8")
    items = parse_google_rss_xml(xml_sample)
    assert len(items) == 1
    assert items[0]["title"] == "日經225指數大漲逾700點 半導體設備股領軍"
    assert items[0]["url"] == "https://news.cnyes.com/news/id/12345"


def test_rank_and_deduplicate_and_seen_persistence(tmp_path: Path):
    seen_file = tmp_path / "seen.json"
    save_seen_ids(seen_file, {"100", "101"})
    loaded = load_seen_ids(seen_file)
    assert loaded == {"100", "101"}

    pool = [
        {"id": "100", "title": "舊新聞有摘要", "summary": "摘要A", "publish_at": 200},
        {"id": "102", "title": "新新聞無摘要", "summary": "", "publish_at": 150},
        {"id": "103", "title": "新新聞有摘要", "summary": "摘要B", "publish_at": 180},
        {"id": "104", "title": "新新聞有摘要", "summary": "重複標題應被過濾", "publish_at": 190},
    ]
    ranked = rank_and_deduplicate(pool, seen_ids=loaded, limit=3)
    assert len(ranked) == 3
    # New + has summary comes first
    assert ranked[0]["id"] == "103"
    assert ranked[0]["is_new"] is True
    # New without summary comes second
    assert ranked[1]["id"] == "102"
    assert ranked[1]["is_new"] is True
    # Seen item comes last
    assert ranked[2]["id"] == "100"
    assert ranked[2]["is_new"] is False

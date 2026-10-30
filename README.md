# 🌏 Market Radar — 全球五大市場財經新聞與行情數據監控雷達

本專案基於 **`HachiTsai/agent-repo-template`** 標準雙 Agent 協作架構建立，定時從**鉅亨網（Anue）**與 **Yahoo Finance** 採集**台股、美股、港股、日股、總經**五大維度的即時行情與結構化新聞摘要，並結合 **Google Gemini AI** 產出跨市場資金與產業鏈深度洞察，自動推播至 Slack。

---

## ✨ 核心功能與架構

1. **📊 全球五大市場即時行情儀表板 (`market_data_fetcher.py`)**
   - **🇹🇼 台股**：台股加權指數 (`^TWII`)、台積電 (`2330.TW`)、鴻海 (`2317.TW`)、聯發科 (`2454.TW`)
   - **🇺🇸 美股**：S&P 500 (`^GSPC`)、那斯達克 (`^IXIC`)、費城半導體 (`^SOX`)、輝達 (`NVDA`)、台積電 ADR (`TSM`)
   - **🇭🇰 港股**：恆生指數 (`^HSI`)、恆生科技 ETF (`3032.HK`)、騰訊控股 (`0700.HK`)
   - **🇯🇵 日股**：日經 225 (`^N225`)、東京威力科創 (`8035.T`)、愛德萬測試 (`6857.T`)
   - **🌐 總經與匯率**：美債 10 年期殖利率 (`^TNX`)、美元/台幣 (`TWD=X`)、美元/日圓 (`JPY=X`)、黃金 (`GC=F`)、比特幣 (`BTC-USD`)

2. **📰 鉅亨網五大板塊結構化新聞與三點摘要 (`cnyes_news_fetcher.py`)**
   - 直接解析鉅亨網（`news.cnyes.com`）SSR 資料流，擷取新聞標題、**編輯撰寫的三點精華摘要**、關鍵字標籤、關聯股票代碼與原文連結。
   - 針對「日股」結合鉅亨網國際股/外匯關鍵字過濾與 Google News `site:cnyes.com` 日股專項 RSS 雙軌補強。
   - 內建 `seen_news.json` 滾動去重機制，自動標記 `🆕` 最新爆發新聞。

3. **🧠 Gemini AI 跨市場首席策略綜述 (`market_summarizer.py`)**
   - 融合即時行情數據與五大板塊新聞摘要，提煉「全球宏觀與資金風向」、「台美日港跨市場連動」與「焦點標的與風險雷達」。
   - 具備無 API Key 或網路異常時的量化規則引擎優雅降級（Graceful Degradation）。

4. **🚀 機構級 Slack Block Kit 推播與 Gatekeeper 防呆 (`slack_notifier.py` & `radar_runner.py`)**
   - 內建 Gatekeeper 品質門檻檢驗，確保至少 3 個市場與板塊資料完整才發送推播。

---

## ⏰ 自動化排程時段 (`.github/workflows/market_radar.yml`)

配合亞洲盤與歐美盤開收盤節奏，於週一至週五自動執行（亦支援 GitHub Actions 手動 `workflow_dispatch`）：
- **台灣時間 `08:30`**：美股昨夜收盤總結 + 日股開盤 + 台股盤前晨報
- **台灣時間 `13:45`**：台股收盤總結 + 日股尾盤動態
- **台灣時間 `16:30`**：港股收盤總結 + 總經與歐盤開盤動態
- **台灣時間 `21:30`**：美股開盤焦點 + 美國總經數據快訊

---

## 🛠️ 本地開發與測試速查

```bash
# 1. 安裝/同步環境
uv sync

# 2. 本地 Dry-Run 測試（抓取真實行情與新聞並通過 Gatekeeper，不發送 Slack）
uv run python radar_runner.py --dry-run

# 3. 執行單元測試与代碼風格檢查
uv run pytest -q
uv run ruff check .
```

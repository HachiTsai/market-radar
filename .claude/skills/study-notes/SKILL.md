---
name: study-notes
description: 跨專案通用學習筆記技能，支援本機與雲端環境自動同步至 Google Drive 的 Agent_Study_Notes 目錄，且一律採用 Google 原生文件格式 (Google Docs 📄、Sheets 📊、Slides 📽️)。
type: prompt
whenToUse: 當使用者要求記錄學習心得、技術踩坑、架構決策、除錯排錯筆記，或要求查詢/回顧歷史筆記時調用。
disableModelInvocation: false
metadata:
  version: "1.1.0"
  folder_id: "1Xlj49hpabV47WMzctSNS29_Vuuh6ddHn"
---

# Study Notes Skill (跨專案通用學習筆記 - Google Workspace 原生格式版)

本技能提供標準化的學習筆記沉澱與檢索工作流，直接連接至 Google Drive 的 `00_Claude/Agent_Study_Notes/` 目錄，**所有儲存至 Google Drive 的檔案一律採用 Google 原生文件格式（Google Docs 📄, Sheets 📊, Slides 📽️）**。

## 📋 存放路徑與架構規範

- **本機 Google Drive 同步路徑**：
  `/Users/hachi/Library/CloudStorage/GoogleDrive-hachi.tsai@gmail.com/我的雲端硬碟/00_Claude/Agent_Study_Notes/`
- **雲端 Google Drive Folder ID**：
  `1Xlj49hpabV47WMzctSNS29_Vuuh6ddHn`
- **檔案格式鐵律**：
  - **預設一律採用 Google Docs (Google 文件 📄)**，禁止直接在雲端留存未轉換的裸 `.md` 文字檔。
  - 支援 Google Sheets (Google 試算表 📊，適用結構化數據與統計)。
  - 支援 Google Slides (Google 簡報 📽️，適用投影片大綱)。
- **目錄結構**：
  `Agent_Study_Notes/<repo名>/<類別>_<標題>` (Google 文件)

---

## 🛠️ 常用指令

腳本位置：`.claude/skills/study-notes/scripts/note.py`

### 1. 新增筆記 (預設自動建立 Google 文件 📄)
```bash
python3 .claude/skills/study-notes/scripts/note.py add \
  --category "Firmware" \
  --title "ESP32_Flashing_Guide" \
  --tags "esp32,flashing,pio" \
  --content "## 📌 核心摘要\n...\n## 🛠️ 排錯步驟\n..."
```

- 從檔案讀取長篇 Markdown 內容並轉為 Google 文件：
```bash
python3 .claude/skills/study-notes/scripts/note.py add \
  --category "Architecture" \
  --title "SSOT_Pattern" \
  --content-file <path_to_markdown>
```

- 建立 Google 試算表 📊（以 CSV 內容建立）：
```bash
python3 .claude/skills/study-notes/scripts/note.py add \
  --category "Metrics" \
  --title "Latency_Benchmark" \
  --format sheet \
  --content "Time,Ping_ms,RSSI\n10:00,4.2,-65\n10:01,3.8,-64"
```

### 2. 檢索筆記 (Search)
```bash
python3 .claude/skills/study-notes/scripts/note.py search "Flashing"
```

### 3. 讀取筆記 (Read - 自動從 Google Doc 匯出為 Markdown 輸出)
```bash
python3 .claude/skills/study-notes/scripts/note.py read "ESP32_Flashing_Guide"
```

### 4. 列出目錄現有筆記 (List)
```bash
python3 .claude/skills/study-notes/scripts/note.py list
```

---

## 📝 筆記格式標準 (Frontmatter + Markdown)

每份筆記自動產生標準 YAML Frontmatter，上傳時 Google Drive 會自動將 Markdown 標題、清單、表格解析為原生 Google 文件版面：

```markdown
---
title: "筆記標題"
repo: "當前專案名稱"
category: "技術分類"
date: YYYY-MM-DD
tags: ["tag1", "tag2"]
---

# 標題

## 📌 核心摘要 (TL;DR)
- 簡要說明問題、決策或學習核心。

## 🔍 問題背景與原理探討
- 詳細記錄當時的情境、錯誤現象與根因分析。

## 🛠️ 最佳實踐與排錯手冊
- 具體指令、設定檔範例、架構圖或程式碼片段。
```

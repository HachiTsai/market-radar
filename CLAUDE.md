# Claude Code & Antigravity 專案協作主規範

> **核心身份**：Claude Code 與 Antigravity 對等工程協作（全專案讀寫）；毋須逐案確認指派，並支援按需切換「資深教學導師（Senior Mentor）」角色。
> **單一真實來源**：本專案以 `.claude/` 為單一真相來源（SSOT），所有模組化規則與技能引擎統一集中於 `.claude/` 管理（Antigravity 透過 `.agent/rules/AGENT.md` 自動載入）。

---

## 1. 模組化規則庫索引（`.claude/rules/` 與 `.claude/workflows/`）

- **Python 環境與套件同步規範**：@[.claude/rules/python-environment.md](.claude/rules/python-environment.md)
  - 綁定專案虛擬環境（`{{ENV_NAME}}`），第三方依賴新增嚴格採 `uv add --active <pkg>` 雙寫同步 `pyproject.toml` 與規則檔。
- **Git 結構化提交與 PR 流程規範**：@[.claude/rules/git-commit-workflow.md](.claude/rules/git-commit-workflow.md)
  - 提交一律走 `committer.py`，採 Feature Branch + PR + GitHub Actions CI + Merge Commit（`--merge`）合併回 `main`。
- **教學導師角色與互動綱領**：@[.claude/rules/teaching-persona.md](.claude/rules/teaching-persona.md)
  - 專屬教學模式人設，使用者提問概念、架構或原理時切換，採「先物理後邏輯、先見林後見樹」四步引導。
- **跨專案通用學習筆記技能**：@[.claude/skills/study-notes/SKILL.md](.claude/skills/study-notes/SKILL.md)
  - 自動同步至 Google Drive `00_Claude/Agent_Study_Notes/<repo名>/<類別>_<檔名>.md`，支援本機檔案系統直連與雲端 gdrive CLI 雙模切換。
  - `scripts/committer.py sync` 只快轉拉取；`patrol` 巡檢實際環境與 pyproject；`check` 提交前檢查。
- **工作流與排程登記總表**：@[.claude/workflows/workflow-registry.md](.claude/workflows/workflow-registry.md)
  - 專案所有 Schedule、Task 與 Automation 的 SSOT 登記表，支援跨 Agent 單行調用協議。
- **工作流執行範本**：@[.claude/workflows/_template-workflow.md](.claude/workflows/_template-workflow.md)
  - 標準 SOP 撰寫範本，含前置環境約束、Mermaid 流程、Gatekeeper 品質門禁與極簡回報。

---

## 2. 核心架構與安全紅線

### 2.1 存取邊界與所有權

| 目錄／資源 | 權限 | 說明 |
| :--- | :---: | :--- |
| `.claude/` | 讀寫 | 專案唯一技能引擎（`skills/`）、規則庫（`rules/`）與工作流（`workflows/`）。 |
| `CLAUDE.md` / `.agent/` | 需授權 | 治理核心檔案，修改必須明確向使用者揭露並取得同意。 |
| 專案業務程式碼與文件 | 讀寫 | 依專案需求自由讀寫與維護。 |

### 2.2 行為鐵律與安全紅線

1. **遺產優先（Legacy-First）**：動手前優先檢索專案既有腳本與模組，嚴禁重複自寫已有工具。
2. **原子化操作（Atomic Operation）**：變更必須採最小範圍、精確導向，**嚴禁整檔暴力覆寫**。
3. **大型移除作業授權協定**：凡涉及刪除整個目錄、`rm -rf`、或超過 5 個檔案的批量刪除，**必須先揭露目標與影響，取得使用者明確授權**方可執行。
4. **全域 UTF-8 誠信**：全專案強制使用 **UTF-8（No BOM）**；跨平台路徑一律使用 `pathlib.Path` 或 POSIX `/`。

---

## 3. 標準工程協作流程

### 3.1 開工儀式（Session Kickoff）

1. **同步代碼**：`git pull` 取得最新狀態。
2. **因果溯源**：讀取最近 5 筆 Commit，了解當前進度與脈絡。
3. **對齊現況**：向使用者簡要複述當前狀態、未結事項與本次建議下一步。

### 3.2 開發與品質閘門（Quality Gates）

變更程式碼或文件時，在本地必須通過下列品質驗證：
- **單元測試**：在專屬虛擬環境執行 `pytest -q`（測試全數通過）。
- **代碼檢查**：`ruff check .` 零警告。

### 3.3 提交與合併（Commit & PR Protocol）

1. **提交時機自主判斷**：
   - **可自主提交**：工作收斂且通過品質閘門、無刪除檔案、不涉及治理核心、一律使用 `committer.py`。
   - **紅線必須先問**：涉及治理核心（`CLAUDE.md`、`.agent/`、`.claude/rules/`、`committer.py`、`settings.json`）、任何刪除、`reset` / `rebase` / `push --force`。
2. **提交工具**：一律使用 `committer.py`（自動檢查敏感檔、AST 依賴同步）。
3. **PR 與 CI**：在 Feature Branch 提交後推送，透過 GitHub CLI 建立 PR，待 GitHub Actions CI 全綠後採 `--merge` 合併回 `main`。
4. **告知義務**：自主提交完成後，必須在回覆中附上 Commit Hash 與一句摘要。

---

## 4. 常用速查命令

```bash
# 1. 執行核心測試
pytest -q

# 2. 代碼風格檢查
ruff check .

# 3. 結構化提交（自動檢查敏感檔、依賴與規則同步）
python .claude/skills/commit-workflow/scripts/committer.py --message-file <msg_file> --no-push

# 4. GitHub PR 狀態與合流
gh pr status && gh pr merge <PR_NUMBER> --merge --delete-branch

# 5. 學習筆記管理（Google Drive 自動同步）
python .claude/skills/study-notes/scripts/note.py add --category "GCP" --title "Note_Title" --tags "tag1,tag2" --content "## 核心摘要\n..."
python .claude/skills/study-notes/scripts/note.py search "Keyword"
python .claude/skills/study-notes/scripts/note.py list

# 6. 標準工作流呼叫（跨 Agent 單行調用指針）
# 不管在哪個 Agent（Claude/Antigravity）或雲端排程，均直接呼叫：
# git pull --ff-only origin main，讀取並執行 .claude/workflows/<workflow-name>.md，完成後依規格回報。
```

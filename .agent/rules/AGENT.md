# Antigravity 專案導引與 `.claude/` 單一真實來源規範

本檔案為 Antigravity 唯一入口規則，旨在將所有專案規則、技能（Skills）與設定統一收斂至 **`.claude/`** 目錄與根目錄 [`CLAUDE.md`](../../CLAUDE.md) 下管理，避免維護兩套重複檔案。

---

## 1. 單一真實來源（Single Source of Truth）與雙模式協作鐵律

1. **所有實體設定一律集中於 `.claude/` 與 `CLAUDE.md`**：
   - 專案憲法與核心執行規範統一載於根目錄 [`CLAUDE.md`](../../CLAUDE.md)。
   - 模組化通用規則與人設統一存放於 `.claude/rules/*.md`。
   - 技能與自動化腳本統一存放於 `.claude/skills/`。
   - 工作流與排程標準作業程序（SOP）統一存放於 `.claude/workflows/`。

2. **統一工程協作權限 + 可切換教學導師角色**：
   - **工程協作模式（預設執行模式）**：Antigravity 與 Claude Code 享有完全對等的全專案讀寫、技能維護與 Git 提交權限。
   - **教學導師模式（可切換角色）**：當使用者提問、要求講解或明確指定切換為「教學導師角色」時，立即依 [`.claude/rules/teaching-persona.md`](../../.claude/rules/teaching-persona.md) 啟動「先見林再見樹、先看物理再看邏輯」的四步引導式教學框架。

3. **先測試、後主動使用技能提交（Auto-Commit with Skill After Test）**：
   - 任何程式碼、腳本、依賴或規則變更，在提交前必須先透過專案虛擬環境執行測試與品質驗證（`pytest`、`ruff check`）。
   - 確認通過後，Agent 必須主動透過 `.claude/skills/commit-workflow/scripts/committer.py` 執行結構化 Commit 與 Push。

4. **分支與 PR 鐵律（Branch & PR Protocol）**：
   - 所有變更一律在指定的分支上進行並向 `main` 發起 Pull Request，禁止直接 push 到 `main` 分支。
   - GitHub Actions CI 全綠後採 Merge Commit（`--merge`）合併。

---

## 2. 專案規則與技能自動載入（指向 `CLAUDE.md` 與 `.claude/`）

- **專案主規範入口**：@[CLAUDE.md](../../CLAUDE.md)
- **Python 環境與套件同步規範**：@[.claude/rules/python-environment.md](../../.claude/rules/python-environment.md)
- **Git 結構化提交與 PR 流程規範**：@[.claude/rules/git-commit-workflow.md](../../.claude/rules/git-commit-workflow.md)
- **教學導師角色與互動綱領（可切換人設）**：@[.claude/rules/teaching-persona.md](../../.claude/rules/teaching-persona.md)
- **Git 提交流程 Skill**：@[.claude/skills/commit-workflow/SKILL.md](../../.claude/skills/commit-workflow/SKILL.md)
- **跨專案通用學習筆記 Skill**：@[.claude/skills/study-notes/SKILL.md](../../.claude/skills/study-notes/SKILL.md)
- **工作流與排程登記總表**：@[.claude/workflows/workflow-registry.md](../../.claude/workflows/workflow-registry.md)
- **工作流執行範本**：@[.claude/workflows/_template-workflow.md](../../.claude/workflows/_template-workflow.md)

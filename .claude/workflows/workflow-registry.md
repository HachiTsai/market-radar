# 工作流與排程登記總表 (Workflow & Schedule Registry)

本表為專案內所有自動排程（Schedule）、標準任務（Task）與事件自動化（Automation）的**唯一登記總表（Single Source of Truth, SSOT）**。

無論透過 **Claude Code**、**Antigravity**、**GitHub Actions** 或**雲端 Cron** 執行，所有流程均收斂於此。新增、修改、停用或調整排程時間時，必須同步更新本表。

---

## 1. 架構核心原則：單行呼叫協議 (One-Line Dispatch Protocol)

為杜絕跨 Agent（Claude Code vs Antigravity vs 雲端環境）提示詞與上下文漂移：
1. **外部觸發與提示詞一律維持極簡單行**：
   ```text
   git pull --ff-only origin main，讀取並執行 .claude/workflows/<name>.md，完成後依規格回報。
   ```
2. **SOP 邏輯 100% 收斂於 Git 版本庫**：
   - 所有的步驟調整、門禁門檻（Gatekeeper）、參數變更只需直接修改對應的 `.claude/workflows/*.md` 文件。
   - 外部排程平台無需反覆修改 Prompt，下次執行時自動拉取最新邏輯生效。

---

## 2. 流程總表 (Registry Table)

| ID | 流程名稱 | 類型 | 平台 | 觸發時機 | 規格文件（SSOT） | 產出與回報 | 健康檢查 / 門禁 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `S1` | 每日健康檢查巡檢 (範例) | Schedule | GitHub Actions / 雲端排程 | 平日 09:00 | [`.claude/workflows/_template-workflow.md`](_template-workflow.md) | 巡檢報告 / Slack 通知 | 失敗門檻判定 |
| `T1` | 依賴升級與環境驗證 (範例) | Task | 本地 CLI / Agent 對話 | 依需求手動觸發 | [`.claude/workflows/_template-workflow.md`](_template-workflow.md) | PR 變更摘要 | 測試全數通過 |
| `A1` | 新 PR 自動語法與安全審查 (範例) | Automation | Webhook / CI 事件 | PR 開立時觸發 | [`.claude/workflows/_template-workflow.md`](_template-workflow.md) | PR 內嵌審查評論 | CI Quality Gate |

> 💡 **類型說明**：
> - `Schedule`：週期性定時執行（例如 Cron 每天/每週觸發）。
> - `Task`：手動呼叫的標準作業（如發版、資料手動校準）。
> - `Automation`：事件驅動觸發（如 Webhook、GitHub Event）。

---

## 3. 跨平台單行 Prompt 範例

設定排程或呼叫 Agent 時，請逐字使用以下格式：

- **排程呼叫（標準）**：
  ```text
  git pull --ff-only origin main，讀取並執行 .claude/workflows/<workflow-name>.md，完成後依規格回報。
  ```
- **指定分支排程呼叫**：
  ```text
  git pull origin <branch-name>，讀取並執行 .claude/workflows/<workflow-name>.md，完成後依規格回報。
  ```

---

## 4. 流程生命週期管理規範

1. **新增流程**：
   - 複製 `_template-workflow.md` 為具體的工作流檔案（如 `daily-sync.md`）。
   - 撰寫標準執行步驟與 Gatekeeper。
   - 於本表登錄新的流程 ID 與詳細資訊。
   - 同步更新根目錄 `CLAUDE.md` 與 `.agent/rules/AGENT.md` 的索引清單。
2. **修改流程**：
   - 直接修改對應的 `.claude/workflows/*.md`，遵循 Feature Branch + PR 流程合併。
   - 外部排程器無需變更 Prompt，下次自動執行即拉取最新版本。
3. **停用流程**：
   - 停用外部排程觸發器。
   - 於本表標記為「已停用」，並在異動紀錄中留下原因與時間。

---

## 5. 異動紀錄

- `2026-10-30`：初始化工作流登記總表，導入雙 Agent 單行調用協議。

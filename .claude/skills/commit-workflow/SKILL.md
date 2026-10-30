---
name: commit-workflow
description: 結構化 Git 提交流程：分析 staged diff，依統一模板草擬 Commit Message，用 git commit -F 提交並推送。
whenToUse: 當用戶說「開始提交流程」、「幫我 commit」，或需要產出結構化 Commit Message 時
disableModelInvocation: false
metadata:
  version: "2026.10.14.1"
---

# Commit Workflow Skill

## 觸發指令

- `開始提交流程`
- `幫我 commit`
- `python .claude/skills/commit-workflow/scripts/committer.py`（暫存並印出 diff 與模板，供 Agent 草擬）
- `python .claude/skills/commit-workflow/scripts/committer.py --message-file .git/COMMIT_MSG_TEMP --no-stage`（提交已草擬的訊息並推送）
- `python .claude/skills/commit-workflow/scripts/committer.py --auto-quick`（自動產生精簡訊息並提交，限小型變更）

### 參數

| 參數 | 用途 |
| :--- | :--- |
| `--message-file PATH` | 讀取訊息檔，驗證標題後 `git commit -F`，並補上 Co-Authored-By |
| `--auto-quick` | 依 staged 檔案自動產生標題與 bullet；與 `--message-file` 互斥；超過 10 檔會警告 |
| `--no-push` | 提交後不推送 |
| `--dry-run` | 只預覽訊息，不提交 |
| `--no-stage` | 不執行 `git add`，使用既有暫存區 |
| `--stage-list PATH...` | 清空暫存區後只暫存指定路徑 |
| `--exclude PATH...` | `git add .` 後排除指定路徑（支援 glob 與目錄前綴） |
| `--allow-sensitive` | 略過敏感檔案檢查（`.env`、`*.pem`、`*.key`、`credentials/` 等） |
| `--allow-missing-deps` | 略過未記錄套件與依賴檔（`pyproject.toml`／`.claude/rules/python-environment.md`）同步檢查 |
| `--sync` | 安全拉取：`fetch --prune` 後只做 `--ff-only`；有未提交變更、與遠端分叉時不動並回報，分支已併入 `main` 或落後 `main` 時提醒；絕不 rebase／reset／force |
| `--fetch-only` | 搭配 `--sync`：只 fetch 並回報落後，不快轉 |
| `--patrol` | 巡檢系統工具（git、python3、uv、gh）、git 狀態、Python 版本，以及 `pyproject.toml` 直接依賴是否已安裝且版本符合；只回報，不安裝 |

腳本會：拒絕 type 不在封閉清單內的標題、發現敏感檔案或未記錄套件依賴時中止、要推送時若目前在 `main` 則中止（請先建工作分支）、變更 `.claude/` 卻沒動到 rules 或索引時提醒、推送失敗時以 2/4/8/16 秒退避重試，並推送到當前分支。

## 核心原則

讓每一次提交都成為日後可考古的紀錄：標題說明改了什麼，內文說明為什麼改、怎麼驗證。
遵循 Conventional Commits，並以統一模板取代分層（快速／正常／價值）判斷。

## 流程

1. **暫存**：`git add .`。使用者指定只提交某些檔案時，改為只暫存該些路徑。
2. **分析**：`git status --short` 與 `git diff --staged`。大型資料檔（`*.json`、`*.csv`、圖片）以
   `git diff --staged -- . ':(exclude)*.json'` 排除，只看 `--stat`。優先看 staged diff，
   不必遍歷 `git log`，需要對齊既有風格時再看最近 3～5 筆標題。
3. **安全與依賴檢查**：
   - staged 內若含 `.env`、`credentials/`、金鑰、token 等敏感內容，停止並告知使用者，不提交。
   - 若 `committer.py` 提示 staged `.py` 匯入了未記錄的第三方套件，或 `pyproject.toml` 與 `.claude/rules/python-environment.md` 不同步，先補齊依賴並重新暫存後再提交。
4. **草擬**：依下方模板直接寫出最終版本，不提供多個選項讓使用者挑。
5. **提交**：寫入 `.git/COMMIT_MSG_TEMP`，執行 `git commit -F .git/COMMIT_MSG_TEMP`，成功後刪除暫存檔。
6. **推送**：`git push -u origin <當前分支>`；網路失敗時依 2s、4s、8s、16s 退避重試最多 4 次。
7. **回報**：回覆 commit hash、分支、檔案數；有推送就說已推送，沒有就明說。

## Commit Message 格式

### 標題

`<type>(<scope>): <簡短描述>`

- 標題不超過 72 字元，描述用現在式，說明結果而不是過程。
- **scope 為開放清單**，寫變更落在哪個子系統或目錄即可；跨多處時可省略。

### Type（封閉清單，清單外不得自創）

| Type | 用於 |
| :--- | :--- |
| `feat` | 新增功能、能力 |
| `fix` | 修正缺陷 |
| `refactor` | 不改變外部行為的結構調整（含改名、搬移） |
| `docs` | 文件、規範、筆記 |
| `test` | 只補或只改測試（程式同時有改動時，用該程式的 type） |
| `style` | 純格式（空白、排版、lint 修正） |
| `chore` | 雜務：依賴、設定、清理；**找不到合適 type 時的預設** |
| `revert` | 撤銷先前提交 |
| `merge` | 合併分支 |

### 內文模板

```markdown
<type>(<scope>): <簡短描述>

## 核心變更

- 具體改了什麼（按主題分組，一行一件事）

## 變更理由

- 為什麼改、解決了什麼問題

## 驗證

- 跑過什麼檢查與結果（例：`pytest` → 12 passed）
- 純文件或純刪除可寫「無需測試—純文件變更」，必須明寫，不可省略區塊

## Pending Tasks

- 發現但未處理的事項；沒有就寫「無」

Co-Authored-By: Claude <noreply@anthropic.com>
```

小型變更（錯字、單檔刪除、格式）可只保留標題加 1～2 行 bullet 與「驗證」，其餘區塊省略。

### 選用區塊（有實際內容才加，不要硬湊）

- `## 關鍵決策`：有取捨時，表格列出「選項／為什麼沒選／為什麼選現在這個」。
- `## 影響範圍`：變更會影響其他模組、使用者或共用資產時。
- `## 試行錯誤`：真的踩過坑時，寫嘗試了什麼、為何失敗、最終方案。

### 署名

訊息尾端附 `Co-Authored-By` 行。以當前環境給定的署名為準，沒有指定就用上方模板的寫法。

## Pending Tasks 與 Issue 門檻

- **能當場修好且可驗證的缺陷直接修**，另開一筆 commit，回覆中告知。
- 涉及設計判斷、刪除、不可逆操作者，先問使用者。
- 修不了的事項寫在 Pending Tasks。只有「已確認可重現的缺陷」或「使用者明確要求追蹤」才開 GitHub Issue 並寫 `#N`；修好時寫 `Fixes #N`。
- 疑點、「之後可以做」不開 Issue。

## 禁止事項

1. 不憑記憶草擬訊息，一律依 staged diff 內容。
2. 不使用 `git commit -m` 傳多行訊息，一律 `git commit -F`。
3. 不硬湊選用區塊。
4. 不提交敏感憑證。
5. 不自行 `reset --hard`、`rebase`、`push --force`；需要時先問使用者。
6. 不對未被要求的分支推送；推送目標以使用者或環境指定的分支為準。

## 變更紀錄

- **2026.10.14.1**：新增 `scripts/committer.py` 與 `scripts/tests/`。
  - 暫存控制（`--stage-list`／`--exclude`／`--no-stage`）、`--auto-quick`、`--message-file`、`--dry-run`、`--no-push`、Co-Authored-By 注入、type／scope 推斷、各 git 呼叫皆設 timeout。
  - 標題格式驗證（封閉 type 清單）、敏感檔案檢查、推送退避重試。

- **2026.10.14**：建立 skill：staged diff 分析、封閉 Type 清單、統一詳細模板、必填「驗證」、`git commit -F`、Issue 門檻、Co-Authored-By 署名。

# Agent Repo Template (雙 Agent 工程協作標準範本)

本倉庫為 **Claude Code & Antigravity** 專用 GitHub Template Repository，旨在為新專案提供開箱即用的「單一真實來源（SSOT）」、「自動化提交防呆」與「PR + CI 自動化驗證」基建。

---

## 🚀 如何使用本範本建立新專案

### 方式一：終端一鍵建立（最快、最推薦）

若本機已安裝全域腳本 `git-new`（位於 `~/bin/git-new`），只需在終端輸入一行指令：

```bash
# 預設建立 Private Repo
git-new MyProject

# 指定自訂虛擬環境與 Python 版本
git-new MyProject --env my-custom-env --python 3.13

# 建立 Public Repo
git-new MyProject --public
```

**自動完成**：
1. 透過 GitHub CLI 建立獨立專屬的遠端 Repository（完全不與範本綁定）。
2. Clone 至本機 `/Users/hachi/Git/MyProject`。
3. 自動執行變數替換（將專案名與環境名寫入 `CLAUDE.md` 與 `pyproject.toml`）並清理初始化腳本。
4. 自動提交 Initial Commit 並推送到遠端 `main` 分支。

---

### 方式二：在 GitHub 網頁上建立

1. 在 GitHub 頁面上方點擊綠色的 **「Use this template」➔「Create a new repository」**。
2. 輸入您的專案名稱並完成建立。
3. 將新專案 Clone 到本機：
   ```bash
   cd ~/Git
   git clone https://github.com/HachiTsai/<新專案名稱>.git
   cd <新專案名稱>
   ```
4. 執行一次性的專案名稱初始化：
   ```bash
   ./setup.sh <新專案名稱> [虛擬環境名稱] [Python版本]
   ```
   *(該腳本替換完成後會自動自我銷毀，不留痕跡)*
5. 提交並推送變更：
   ```bash
   git add -A
   git commit -m "chore(init): configure project identity"
   git push origin main
   ```

---

## 💡 非 Python / 非 Conda 專案的適用性與調整

本範本預設提供 Python + `pyproject.toml` 的配置，**但核心架構是完全語言無關（Language-Agnostic）的**：

### 1. `committer.py` 的彈性設計（零報錯）
- `committer.py` 內建智慧判斷：**如果專案中沒有 `pyproject.toml`，或者暫存區沒有 `.py` 檔案，它會自動跳過 Python AST 依賴檢查**。
- 敏感檔案攔截（`.env*`、`*.key`、`*.pem`、`credentials.json` 等）與規範同步檢查仍然 100% 生效。

### 2. 若為前端／Node.js 專案（如 Next.js、React、TypeScript）
- **環境規範**：可將 `.claude/rules/python-environment.md` 替換或重命名為 `node-environment.md`（記錄 Node 版本、`pnpm` / `npm` 與 `package.json`）。
- **CI 調整**：將 `.github/workflows/ci.yml` 中的 `pip install` 改為 `npm install && npm test && npm run lint`。
- **清除 Python 檔**：直接刪除根目錄的 `pyproject.toml`，`committer.py` 不會報錯。

### 3. 若為純文件 / 知識庫 / Go / Rust 等專案
- 同理只需依專案語言調整 `.github/workflows/ci.yml` 中的測試指令即可，其餘所有的雙 Agent 協作（`.agent/`、`CLAUDE.md`、`teaching-persona.md`）都能完全通用！

### 4. 跨 Agent 工作流調用協議（One-Line Dispatch Protocol）
不論在 Claude Code、Antigravity 或是雲端定時排程，均以極簡單行指向 `.claude/workflows/` 執行：
```text
git pull --ff-only origin main，讀取並執行 .claude/workflows/<workflow-name>.md，完成後依規格回報。
```
所有前置檢查、執行步驟與 Gatekeeper 品質門禁完全收斂於 Git 版本庫中，杜絕多 Agent 資訊與提示詞漂移。

---

## 🧠 內建核心資產

- **`.claude/` SSOT 架構**：
  - `.claude/rules/git-commit-workflow.md`：Feature Branch + PR + CI + Merge Commit 規範。
  - `.claude/rules/python-environment.md`：`uv add --active` 依賴同步規範。
  - `.claude/rules/teaching-persona.md`：隨時可切換的「資深教學導師（Senior Mentor）」角色人設。
  - `.claude/skills/commit-workflow/`：安全攔截防呆與結構化提交工具。
  - `.claude/skills/study-notes/`：跨專案學習筆記與 Google Drive 雙模同步工具。
  - `.claude/workflows/`：跨 Agent 標準作業程序（SOP）與排程總表，支援單行調用指針（Schedule / Task / Automation）。
- **`.agent/rules/AGENT.md`**：Antigravity 入口指針。
- **`CLAUDE.md`**：精簡現代工程協作主規範。
- **`.github/workflows/ci.yml`**：自動化 CI 門禁。

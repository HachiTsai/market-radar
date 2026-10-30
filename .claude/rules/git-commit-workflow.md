# Git 結構化提交流程規範

所有 Git 提交與推送操作一律透過 `.claude/skills/commit-workflow/scripts/committer.py` 執行，並遵循 [`.claude/skills/commit-workflow/SKILL.md`](../../.claude/skills/commit-workflow/SKILL.md) 規範：

## 1. 分支與 PR 鐵律

1. **先開 PR 再合併 `main`**：
   - 所有變更（功能開發、重構、工具、文件與規範）都在指定的分支上 commit 並推送，向 `main` 發起 Pull Request。
   - PR 的 GitHub Actions CI（`lint-and-tests`：`ruff check` 與 `pytest`）全綠後才可合併。
   - **禁止直接 push 到 `main` 分支**。
2. **合併方式一律採用 Merge Commit**：
   - 不使用 squash、不使用 rebase，保留分支上每個 commit 的完整訊息與歷程。

## 2. 自動提交流程原則

- **任務完成主動提交（Auto-Commit on Completion）**：任何功能開發、重構、設定或規則變更完成，並在通過測試與品質驗證（`pytest` 與 `ruff`）後，**Agent 必須主動使用 `commit-workflow` 技能在分支上自動執行結構化提交與推送並發起 PR，無需等待使用者口令催促**。
- **禁止隨意手動提交**：嚴禁使用 raw `git commit -m`，所有提交一律使用技能腳本，確保 Commit Message 符合結構化模板規範。

## 3. 標準提交步驟

0. **開工先同步**（本機與雲端 Claude 協作時必做）：
   ```bash
   python .claude/skills/commit-workflow/scripts/committer.py --sync
   ```
   只做 fast-forward；有未提交變更、與遠端分叉時不動並回報。環境懷疑有問題時用 `--patrol` 巡檢。
1. **檢查**：
   ```bash
   python .claude/skills/commit-workflow/scripts/committer.py --check-only
   ```
   檢查 staged diff、敏感檔案（`.env`、`*.key`、`credentials/`）與未記錄的 Python 套件依賴。
2. **草擬與提交**：
   將符合模板的 Commit Message 寫入訊息檔，再執行：
   ```bash
   python .claude/skills/commit-workflow/scripts/committer.py --message-file <path_to_msg> --no-push
   ```

## 4. 安全防護與依賴防呆

- **受保護分支攔截**：要推送時若目前在 `main`，腳本中止（`--no-push` 本機提交不受限）。
- **敏感檔案攔截**：暫存區若包含 `.env*`、憑證私鑰、`credentials.json` 等檔案，腳本將自動中止並阻擋提交（可加 `--allow-sensitive` 解除）。
- **Python 依賴與規則同步攔截**：AST 自動分析暫存 Python 檔的 `import` 是否登記於 `pyproject.toml`，並驗證 `pyproject.toml` 與 `.claude/rules/python-environment.md` 是否 100% 同步（可加 `--allow-missing-deps` 略過）。

## 5. 禁止事項

- 嚴禁直接 push 到 `main` 分支，一律由 PR 經 CI 驗證全綠後以 Merge Commit 合併。
- 禁止使用 `git commit -m` 傳遞多行訊息，一律使用 `--message-file`。
- 禁止提交任何明文金鑰、OAuth 憑證或 `.env` 檔案。
- 未經使用者明確同意，禁止執行 `git reset --hard`、`git rebase` 或 `git push --force`。

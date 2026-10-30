# Python 虛擬環境與套件同步規範

本專案使用專屬虛擬環境管理所有依賴，並嚴格遵循 `pyproject.toml` 與本規範檔案的**雙寫同步機制**。

---

## 1. 執行環境標準

- **虛擬環境**：`{{ENV_NAME}}`
- **Python 版本**：`{{PYTHON_VERSION}}`
- **依賴管理工具**：`uv`（速度快、具備跨平台 lock 機制）

---

## 2. 套件安裝與雙寫同步鐵律（Dual-Sync Protocol）

為確保開發環境與版控的一致性，凡是安裝或更新第三方套件，**必須使用 `uv add --active` 嚴格同步以下兩處**：

1. **實體環境與 `pyproject.toml`**：
   ```bash
   uv add --active <package_name>==<version>
   ```
   *注意：使用 `--active` 會將套件安裝至當前啟動的虛擬環境中，並自動將依賴條目寫入 `pyproject.toml`。*

2. **本規範檔的依賴清單區塊**：
   將新增的套件同步記錄至下方 `## 3. 現行專案依賴宣告` 的 toml 程式碼區塊內。

> ⚠️ **提交前防呆檢驗**：本專案的 `committer.py` 設有 AST 攔截機制，若檢測到 Python 原始碼引用了未登記於 `pyproject.toml` 的套件，或 `pyproject.toml` 與本檔案內容不一致，提交將會被自動中止。

---

## 3. 現行專案依賴宣告

```toml
[project]
name = "{{PROJECT_NAME}}"
version = "0.1.0"
description = "Project initialized from HachiTsai/agent-repo-template"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pytest>=8.0.0",
    "ruff>=0.8.0",
]
```

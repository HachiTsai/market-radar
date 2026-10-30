#!/usr/bin/env bash
set -euo pipefail

# 取得當前目錄名作為預設專案名
CURRENT_DIR="$(basename "$PWD")"
PROJECT_NAME="${1:-$CURRENT_DIR}"
ENV_NAME="${2:-$PROJECT_NAME}"
PYTHON_VERSION="${3:-3.12}"

echo "============================================================"
echo "🚀 正在初始化專案: $PROJECT_NAME"
echo "   - 虛擬環境: $ENV_NAME"
echo "   - Python 版本: $PYTHON_VERSION"
echo "============================================================"

# 替換樣板變數
replace_vars() {
  local file="$1"
  if [ -f "$file" ]; then
    sed -i '' "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$file" 2>/dev/null || sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$file"
    sed -i '' "s/{{ENV_NAME}}/$ENV_NAME/g" "$file" 2>/dev/null || sed -i "s/{{ENV_NAME}}/$ENV_NAME/g" "$file"
    sed -i '' "s/{{PYTHON_VERSION}}/$PYTHON_VERSION/g" "$file" 2>/dev/null || sed -i "s/{{PYTHON_VERSION}}/$PYTHON_VERSION/g" "$file"
  fi
}

replace_vars "pyproject.toml"
replace_vars "CLAUDE.md"
replace_vars "README.md"
replace_vars ".claude/rules/python-environment.md"
replace_vars ".claude/workflows/_template-workflow.md"

echo "✅ 模板變數替換完成。"

# 自我清理
rm -f setup.sh
echo "🧹 清除 setup.sh 完成。"

echo "🎉 專案初始化完畢！您可以開始進行開發。"

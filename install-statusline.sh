#!/bin/bash
# Claude Code StatusLine 安装脚本
# 一键安装增强的状态栏配置

set -e

# 颜色定义
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
RED='\033[31m'
RESET='\033[0m'
BOLD='\033[1m'

echo -e "${BLUE}${BOLD}╔════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}${BOLD}║  Claude Code StatusLine 安装脚本     ║${RESET}"
echo -e "${BLUE}${BOLD}╚════════════════════════════════════════╝${RESET}"
echo ""

# 1. 检查依赖
echo -e "${YELLOW}[1/4] 检查依赖...${RESET}"

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}✗ 缺少依赖: $1${RESET}"
        return 1
    else
        echo -e "${GREEN}✓ 已安装: $1${RESET}"
        return 0
    fi
}

missing_deps=0
check_command fzf || missing_deps=1
check_command jq || missing_deps=1

if [ $missing_deps -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}缺少必要依赖，请先安装：${RESET}"
    echo ""
    echo -e "${BOLD}macOS:${RESET}"
    echo "  brew install fzf jq"
    echo "  $(brew --prefix)/opt/fzf/install  # 安装 shell integration"
    echo ""
    echo -e "${BOLD}Linux:${RESET}"
    echo "  # fzf: https://github.com/junegunn/fzf#installation"
    echo "  # jq: sudo apt install jq 或 sudo yum install jq"
    echo ""
    echo -e "${YELLOW}安装完成后重新运行此脚本${RESET}"
    exit 1
fi

echo ""

# 2. 复制 statusLine 脚本
echo -e "${YELLOW}[2/4] 安装 StatusLine 脚本...${RESET}"

CLAUDE_DIR="$HOME/.claude"
STATUSLINE_SCRIPT="$CLAUDE_DIR/statusline-command.sh"

if [ ! -d "$CLAUDE_DIR" ]; then
    mkdir -p "$CLAUDE_DIR"
    echo -e "${GREEN}✓ 创建目录: $CLAUDE_DIR${RESET}"
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 复制 statusline-command.sh
if [ -f "$SCRIPT_DIR/statusline-command.sh" ]; then
    cp "$SCRIPT_DIR/statusline-command.sh" "$STATUSLINE_SCRIPT"
    chmod +x "$STATUSLINE_SCRIPT"
    echo -e "${GREEN}✓ 已复制: $STATUSLINE_SCRIPT${RESET}"
else
    echo -e "${RED}✗ 未找到源文件: $SCRIPT_DIR/statusline-command.sh${RESET}"
    exit 1
fi

echo ""

# 3. 更新 settings.json
echo -e "${YELLOW}[3/4] 配置 Claude Code settings.json...${RESET}"

SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# 检查是否已配置 statusLine
if [ -f "$SETTINGS_FILE" ]; then
    if jq -e '.statusLine' "$SETTINGS_FILE" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ 已存在 statusLine 配置，将更新${RESET}"
    fi
else
    echo -e "${GREEN}✓ 创建新的配置文件${RESET}"
    echo '{}' > "$SETTINGS_FILE"
fi

# 使用 jq 更新 statusLine 配置
temp_file=$(mktemp)
jq '.statusLine = {
  "type": "command",
  "command": "bash ~/.claude/statusline-command.sh"
}' "$SETTINGS_FILE" > "$temp_file"
mv "$temp_file" "$SETTINGS_FILE"

echo -e "${GREEN}✓ 已配置 statusLine${RESET}"
echo ""

# 4. 验证安装
echo -e "${YELLOW}[4/4] 验证安装...${RESET}"

if [ -f "$STATUSLINE_SCRIPT" ] && [ -x "$STATUSLINE_SCRIPT" ]; then
    echo -e "${GREEN}✓ StatusLine 脚本已就绪${RESET}"
else
    echo -e "${RED}✗ 验证失败${RESET}"
    exit 1
fi

if jq -e '.statusLine.command == "bash ~/.claude/statusline-command.sh"' "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 配置文件正确${RESET}"
else
    echo -e "${RED}✗ 配置验证失败${RESET}"
    exit 1
fi

echo ""
echo -e "${GREEN}${BOLD}╔════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║         安装成功！                   ║${RESET}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${BLUE}StatusLine 功能：${RESET}"
echo "  Model: 当前使用的 Claude 模型"
echo "  Context: 上下文窗口剩余容量"
echo "  Skills: 可用的 skill 数量"
echo "  Git: 当前 Git 分支"
echo "  Tokens: Token 使用量和费用（人民币）"
echo ""
echo -e "${YELLOW}提示：${RESET}"
echo "  1. 重启 Claude Code CLI 使配置生效"
echo "  2. 或在当前会话输入 /reload-config 刷新配置"
echo "  3. 分隔符使用全角字符 '｜' 更美观"
echo ""
echo -e "${BLUE}卸载方法：${RESET}"
echo "  删除配置：jq 'del(.statusLine)' ~/.claude/settings.json > tmp && mv tmp ~/.claude/settings.json"
echo "  删除脚本：rm ~/.claude/statusline-command.sh"
echo ""
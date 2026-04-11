# Claude Code StatusLine 配置分享

增强的 Claude Code 状态栏配置，显示更多实用信息。

## 功能特性

状态栏显示以下信息（使用全角分隔符 `｜`）：

- **Model**: 当前使用的 Claude 模型（Sonnet/Opus/Haiku）
- **Context**: 上下文窗口剩余容量（颜色提示：绿色>50%、黄色>20%、红色≤20%）
- **Skills**: 当前可用的 skill 数量
- **Git**: 当前 Git 分支名称
- **Tokens**: Token 使用量和费用（人民币）

示例显示：
```
Model: Sonnet 4.6｜Context: 99% left｜Skills: 2｜Git: v1｜Tokens: 654K in / 21K out (¥16.39)
```

## 一键安装

### 方法 1: 克隆仓库后安装

```bash
# 克隆仓库
git clone https://github.com/yangweitech/coding-skills.git
cd coding-skills

# 运行安装脚本
chmod +x install-statusline.sh
./install-statusline.sh
```

### 方法 2: 直接下载安装脚本

```bash
# 下载安装脚本和配置文件
curl -O https://raw.githubusercontent.com/yangweitech/coding-skills/main/install-statusline.sh
curl -O https://raw.githubusercontent.com/yangweitech/coding-skills/main/statusline-command.sh

# 运行安装
chmod +x install-statusline.sh
./install-statusline.sh
```

## 前置依赖

安装前需要确保已安装以下工具：

### macOS
```bash
brew install fzf jq
$(brew --prefix)/opt/fzf/install  # 安装 shell integration
```

### Linux
```bash
# fzf: https://github.com/junegunn/fzf#installation
# jq: sudo apt install jq 或 sudo yum install jq
```

## 安装后操作

1. **重启 Claude Code CLI** 使配置生效
2. 或在当前会话输入 `/reload-config` 刷新配置

## 卸载方法

```bash
# 删除配置
jq 'del(.statusLine)' ~/.claude/settings.json > tmp && mv tmp ~/.claude/settings.json

# 删除脚本
rm ~/.claude/statusline-command.sh
```

## 配置说明

安装脚本会修改 `~/.claude/settings.json`，添加以下配置：

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
  }
}
```

状态栏脚本位于：`~/.claude/statusline-command.sh`

## 自定义修改

如需修改显示内容或顺序，编辑 `~/.claude/statusline-command.sh`：

- **颜色定义**: 修改 ANSI 颜色代码
- **显示顺序**: 调整 `parts+=()` 的顺序
- **分隔符**: 修改 `IFS='｜'` 部分
- **字段名称**: 如将 "Git" 改为 "Branch"

## 效果对比

### 默认状态栏
```
Skills: 2 | Model: Sonnet 4.6 | Branch: v1 | Context: 99% left | Tokens: 654K in / 21K out (¥16.39)
```

### 增强状态栏
```
Model: Sonnet 4.6｜Context: 99% left｜Skills: 2｜Git: v1｜Tokens: 654K in / 21K out (¥16.39)
```

改进点：
- 优化显示顺序（Model → Context → Skills → Git → Tokens）
- Skills 只显示数量（避免 skill 很多时撑爆状态栏）
- 使用全角分隔符更美观
- Context 根据剩余容量动态变色

## 兼容性

- Claude Code CLI 所有版本
- macOS / Linux
- 需要 fzf 和 jq 支持

## 贡献

欢迎提交 Issue 和 PR 改进状态栏功能！

## 作者

杨卫 - yangweitech@gmail.com

## 许可

MIT License
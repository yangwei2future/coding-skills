# coding-skills

研发全生命周期 Skill 集合，覆盖需求管理、开发流水线、测试用例、技术文档等场景。

基于 Claude Code Plugin Marketplace 机制，支持一键安装。

## 快速导航

- [安装 Marketplace](#安装-marketplace)
- [Skills 列表](#skills-列表)
- [StatusLine 增强配置](#statusline-增强配置) ⭐ 推荐

---

## 安装 Marketplace

先将本仓库添加为 Claude Code 的 marketplace 来源：

```bash
claude plugin marketplace add yangwei2future/coding-skills
```

然后即可按需安装各个 skill：

```bash
claude plugin install <skill-name>

# 查看所有可用 skill
claude plugin list
```

---

## Skills 列表

### ai-friendly-prd — AI 友好 PRD 生成器

生成结构化产品需求文档（PRD），下游 Agent 可直接解析并生成系统设计、API 规范和测试用例。

**触发场景**：写 PRD、产品需求、需求文档、功能设计、feature spec

```bash
claude plugin install ai-friendly-prd
```

---

### code-to-tech-manual — 代码转技术手册

将项目实现代码转化为结构化技术手册，以方法级粒度记录业务流程的完整调用链、关键判断点和外部依赖。

支持前端（React/Vue）和后端（Java/Spring Boot）两种模式，以及 `init` / `add` / `update` 三个子命令。

**触发场景**：生成技术手册、记录代码实现、沉淀代码逻辑

```bash
claude plugin install code-to-tech-manual
```

---

### dev-pipeline — 端到端开发流水线

将需求澄清、架构设计、任务拆解、并行编码、QA 验证串联为自动化工作流，适用于任何技术栈。

```
需求文档 → [PM] → [架构师] → [人工审核] → [并行编码] → [QA验证] → 交付
```

**触发场景**：dev pipeline、全流程开发、需求到代码、帮我开发这个功能

```bash
claude plugin install dev-pipeline
```

---

### dip-openapi-token — DIP OpenAPI Token 获取

通过浏览器登录自动获取 IDaaS Access Token，供 DIP 数智平台 OpenAPI 接口调用使用。支持 test / ontest / prod 三套环境。

**触发场景**：获取 token、IDaaS 登录、DIP OpenAPI 认证、刷新 token

```bash
claude plugin install dip-openapi-token
```

---

### feishu-requirement — 飞书需求文档提取器

从飞书文档（docx/wiki）提取需求内容并保存为本地 Markdown 文件到 `docs` 目录。

**前提条件**：需设置环境变量 `FEISHU_TOKEN`

**触发场景**：从飞书导入需求文档

```bash
claude plugin install feishu-requirement
```

---

### llm-gateway — 公司内部 LLM Gateway 接入

帮助接入公司内部 LLM Gateway（AgentOps/融合云模型），完成模型接入、订阅管理、API Key 获取等操作。

**触发场景**：接入公司模型、使用内部模型、融合云模型、切换模型

```bash
claude plugin install llm-gateway
```

---

### test-case — 测试用例生成器

基于需求文档或技术方案生成全面的功能测试用例，支持为整个方案或指定模块生成。

**触发场景**：编写测试用例、生成测试用例

```bash
claude plugin install test-case
```

---

## StatusLine 增强配置 ⭐

增强的 Claude Code 状态栏配置，显示更多实用信息。

### 功能特性

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

### 一键安装

#### 方法 1: 克隆仓库后安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yangwei2future/coding-skills.git
cd coding-skills

# 运行安装脚本
chmod +x install-statusline.sh
./install-statusline.sh
```

#### 方法 2: 直接下载安装

```bash
# 下载安装脚本和配置文件
curl -O https://raw.githubusercontent.com/yangwei2future/coding-skills/main/install-statusline.sh
curl -O https://raw.githubusercontent.com/yangwei2future/coding-skills/main/statusline-command.sh

# 运行安装
chmod +x install-statusline.sh
./install-statusline.sh
```

### 前置依赖

安装前需要确保已安装以下工具：

#### macOS
```bash
brew install fzf jq
$(brew --prefix)/opt/fzf/install  # 安装 shell integration
```

#### Linux
```bash
# fzf: https://github.com/junegunn/fzf#installation
# jq: sudo apt install jq 或 sudo yum install jq
```

### 安装后操作

1. **重启 Claude Code CLI** 使配置生效
2. 或在当前会话输入 `/reload-config` 刷新配置

### 自定义修改

如需修改显示内容或顺序，编辑 `~/.claude/statusline-command.sh`：

- **颜色定义**: 修改 ANSI 颜色代码（BLUE、GREEN、YELLOW、RED 等）
- **显示顺序**: 调整 `parts+=()` 的顺序
- **分隔符**: 修改 `IFS='｜'` 部分
- **字段名称**: 如将 "Git" 改为 "Branch"

### 效果对比

#### 默认状态栏
```
Skills: 2 | Model: Sonnet 4.6 | Branch: v1 | Context: 99% left | Tokens: 654K in / 21K out (¥16.39)
```

#### 增强状态栏
```
Model: Sonnet 4.6｜Context: 99% left｜Skills: 2｜Git: v1｜Tokens: 654K in / 21K out (¥16.39)
```

改进点：
- 优化显示顺序（Model → Context → Skills → Git → Tokens）
- Skills 只显示数量（避免 skill 很多时撑爆状态栏）
- 使用全角分隔符更美观
- Context 根据剩余容量动态变色（绿色/黄色/红色）

### 卸载方法

```bash
# 删除配置
jq 'del(.statusLine)' ~/.claude/settings.json > tmp && mv tmp ~/.claude/settings.json

# 删除脚本
rm ~/.claude/statusline-command.sh
```

### 配置说明

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

---

## 目录结构

```
coding-skills/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace 入口 manifest
├── plugins/                 # 各 plugin 目录
│   ├── ai-friendly-prd/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/ai-friendly-prd/
│   ├── code-to-tech-manual/
│   ├── dev-pipeline/
│   ├── dip-openapi-token/
│   ├── feishu-requirement/
│   ├── llm-gateway/
│   └── test-case/
└── skills/                  # 原始 skill 源文件
```

# coding-skills

研发全生命周期 Skill 集合，覆盖需求管理、开发流水线、测试用例、技术文档等场景。

基于 Claude Code Plugin Marketplace 机制，支持一键安装。

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

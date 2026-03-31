# coding-skills

一套为 Claude Code 设计的自定义 Skill 集合，覆盖需求管理、开发流水线、测试用例、技术文档等研发全生命周期场景。

## 安装

使用 `npx` 将某个 skill 安装到 Claude Code：

```bash
# 安装单个 skill
npx @anthropic-ai/claude-code install-skill <skill-name>

# 或者直接 clone 本仓库，手动复制 skill 到 ~/.claude/skills/
git clone <repo-url>
cp -r skills/<skill-name> ~/.claude/skills/
```

---

## Skills 列表

### ai-friendly-prd — AI 友好 PRD 生成器

生成结构化产品需求文档（PRD），下游 Agent 可直接解析并生成系统设计、API 规范和测试用例。

**触发场景**：写 PRD、产品需求、需求文档、功能设计、feature spec

```bash
npx @anthropic-ai/claude-code skills install ai-friendly-prd
```

---

### code-to-tech-manual — 代码转技术手册

将项目实现代码转化为结构化技术手册，以方法级粒度记录业务流程的完整调用链、关键判断点和外部依赖，沉淀为可检索的知识库。

支持前端（React/Vue）和后端（Java/Spring Boot）两种模式：
- `/code-to-tech-manual init` — 全量扫描，首次建立技术手册
- `/code-to-tech-manual add` — 新功能完成后追加文档
- `/code-to-tech-manual update` — 需求变更后修正已有章节

**触发场景**：生成技术手册、记录代码实现、沉淀代码逻辑

```bash
npx @anthropic-ai/claude-code skills install code-to-tech-manual
```

---

### dev-pipeline — 端到端开发流水线

将需求澄清、架构设计、任务拆解、并行编码、QA 验证串联为自动化工作流，适用于任何技术栈的项目开发。

```
需求文档 → [PM] → [架构师] → [人工审核] → [并行编码] → [QA验证] → 交付
```

**触发场景**：dev pipeline、全流程开发、需求到代码、帮我开发这个功能

```bash
npx @anthropic-ai/claude-code skills install dev-pipeline
```

---

### dip-openapi-token — DIP OpenAPI Token 获取

通过浏览器登录自动获取 IDaaS Access Token，供 DIP 数智平台 OpenAPI 接口调用使用。支持 test / ontest / prod 三套环境。

**触发场景**：获取 token、IDaaS 登录、DIP OpenAPI 认证、刷新 token

```bash
npx @anthropic-ai/claude-code skills install dip-openapi-token
```

---

### feishu-requirement — 飞书需求文档提取器

从飞书文档（docx/wiki）提取需求内容并保存为本地 Markdown 文件到 `docs` 目录。

**前提条件**：需设置环境变量 `FEISHU_TOKEN`（飞书 API 认证 token）

**触发场景**：从飞书导入需求文档

```bash
npx @anthropic-ai/claude-code skills install feishu-requirement
```

**使用示例**：
```bash
/feishu-requirement https://li.feishu.cn/docx/abc123
```

---

### llm-gateway — 公司内部 LLM Gateway 接入

帮助接入公司内部 LLM Gateway（AgentOps/融合云模型），完成模型接入、订阅管理、API Key 获取等操作。

**触发场景**：接入公司模型、使用内部模型、融合云模型、切换模型

```bash
npx @anthropic-ai/claude-code skills install llm-gateway
```

---

### test-case — 测试用例生成器

基于需求文档或技术方案生成全面的功能测试用例，支持为整个方案或指定模块生成。

**触发场景**：编写测试用例、生成测试用例

```bash
npx @anthropic-ai/claude-code skills install test-case
```

**使用示例**：
```bash
/test-case 需求文档       # 为整个需求文档生成测试用例
/test-case 需求文档 登录模块  # 只为登录模块生成
/test-case               # 列出所有可用文档供选择
```

---

## 手动安装

如果不使用 npx，可以手动将 skill 目录复制到 Claude Code 的 skills 目录：

```bash
# 复制单个 skill
cp -r skills/test-case ~/.claude/skills/

# 复制所有 skills
cp -r skills/* ~/.claude/skills/
```

## 目录结构

```
coding-skills/
└── skills/
    ├── ai-friendly-prd/       # PRD 生成器
    ├── code-to-tech-manual/   # 代码转技术手册
    ├── dev-pipeline/          # 开发流水线
    ├── dip-openapi-token/     # DIP Token 获取
    ├── feishu-requirement/    # 飞书需求提取
    ├── llm-gateway/           # LLM Gateway 接入
    └── test-case/             # 测试用例生成
```

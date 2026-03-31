---
name: dev-pipeline
description: 端到端开发流水线编排器，将需求澄清、架构设计、任务拆解、并行编码、QA验证串联为自动化工作流。适用于任何技术栈的项目开发。当用户想从需求文档到可运行代码、或需要系统化地开发一个新功能时触发。触发场景包括但不限于：用户说"dev pipeline"、"开发流水线"、"全流程开发"、"需求到代码"、"端到端开发"、"pipeline"、"从需求开始开发"、"编排开发流程"、"帮我开发这个功能"、"从这个PRD开始实现"、"我有个需求文档，帮我实现"、"帮我把这个需求做出来"、"开始做这个功能"。即使用户没有说"pipeline"，只要意图是系统化地从需求走到可运行代码，都应触发此 skill。
---

# 开发流水线 - 多智能体编排器

```
需求文档 → [PM] → [架构师] → [人工审核] → [并行编码] → [QA验证] → 交付
```

## 流水线总览

| 阶段 | 角色 | 输入 | 输出 | 人工卡点 |
|:-----|:-----|:-----|:-----|:---------|
| 1. 需求澄清 | 产品经理 | 原始需求 | AI友好PRD | 确认PRD |
| 2. 架构设计 | 架构师 | PRD + 代码库 | 技术方案+项目上下文 | 审核方案 |
| 3. 任务拆解 | 技术负责人 | 已批准方案 | 原子编码任务（按波次） | 确认拆解 |
| 4. 并行编码 | 开发者 | 任务列表+项目上下文 | 实现代码 | - |
| 5. QA验证 | 测试工程师 | 代码+PRD+方案 | 测试报告 | 验收交付 |

---

## 启动流程

### 第一步：确定功能名称

询问用户为本次开发起一个简短的英文标识名（用于文件命名），例如 `user-favorites`、`points-system`。

所有产出文件统一使用此名称：`docs/<功能名>-prd.md`、`docs/<功能名>-architecture.md` 等。

### 第二步：确定起始阶段

用 AskUserQuestion 询问：
- "从哪个阶段开始？"
  - 选项：
    - "从需求澄清开始 (Phase 1)" — 完整流水线
    - "已有 PRD，从架构设计开始 (Phase 2)"
    - "已有技术方案，从任务拆解开始 (Phase 3)"
    - "已有任务列表，从编码开始 (Phase 4)"

### 第三步：加载对应阶段指引

根据用户选择，用 Read 工具加载对应阶段的详细指引文件（相对于本 skill 目录）：

- **阶段1** → 读取 `phase-1-pm.md`
- **阶段2** → 读取 `phase-2-architect.md`
- **阶段3** → 读取 `phase-3-tasks.md`
- **阶段4** → 读取 `phase-4-coding.md`
- **阶段5** → 读取 `phase-5-qa.md`

严格按照加载的阶段指引执行。每个阶段完成后，再加载下一阶段的指引继续。

### 第四步：需求文档来源（仅从阶段1开始时）

用 AskUserQuestion 询问：
- "请提供需求文档的来源"
  - 选项：
    - "本地文件路径"
    - "飞书文档链接" → 使用 `feishu-requirement` skill 提取
    - "直接粘贴内容"

---

## 流水线控制

### 状态持久化

**每个阶段开始和结束时**都要更新 `docs/<功能名>-pipeline-state.json`，确保状态始终最新。

```json
{
  "feature_name": "user-favorites",
  "current_phase": 4,
  "phase_status": "in_progress",
  "completed_phases": [1, 2, 3],
  "artifacts": {
    "prd": "docs/user-favorites-prd.md",
    "architecture": "docs/user-favorites-architecture.md",
    "tasks": "docs/user-favorites-tasks.md"
  },
  "project_context": {
    "tech_stack": "Java + Spring Boot + MyBatis + Vue 3",
    "test_command": "mvn test",
    "build_command": "mvn compile"
  },
  "coding_progress": {
    "current_wave": 2,
    "total_waves": 4,
    "completed_waves": [1]
  },
  "updated_at": "2024-01-15T11:00:00",
  "notes": "Wave 1 已完成并提交，正在执行 Wave 2"
}
```

**写入时机**：
- 阶段开始时：`phase_status: "in_progress"`
- 人工卡点等待时：`phase_status: "awaiting_review"`
- 阶段完成时：`phase_status: "completed"`，并将阶段号加入 `completed_phases`
- 编码阶段每个波次开始前：更新 `coding_progress.current_wave`

### 暂停与恢复

任何人工卡点都可选择"暂停流水线"，流水线会自动将最新状态写入状态文件。

**中途退出后的恢复流程**：

1. 用户重新触发 dev-pipeline skill
2. 询问用户"是否从上次中断处继续？"
3. 如果是，读取 `docs/<功能名>-pipeline-state.json`
4. 根据 `current_phase` + `phase_status` 判断恢复点：
   - `phase_status: "awaiting_review"` → 展示已有产出，重新走人工确认流程
   - `phase_status: "in_progress"` + 编码阶段 → 检查 TaskList，从未完成的任务恢复执行
   - `phase_status: "completed"` → 直接进入下一阶段
5. 恢复后继续正常执行，不重复已完成的工作

### 阶段切换质量检查

每次阶段切换前确认：
- [ ] 当前阶段产出完整（无占位文本）
- [ ] 用户已明确批准
- [ ] 所有已识别的缺口已解决或明确延期
- [ ] 文档已保存到 `docs/` 目录

### 每阶段完成后的检查点摘要

每个阶段完成后，向用户输出标准检查点摘要，格式如下：

```
---
阶段 [N] 完成检查点
---
产出文件：[列出本阶段生成/修改的文件路径]
主要决策：[1-3 条本阶段做出的关键决定或结论]
待下一阶段关注：[传递给下一阶段的注意事项，无则省略]
状态文件：已更新 docs/<功能名>-pipeline-state.json（phase [N] → completed）
---
下一步：[N+1]. [下一阶段名称]
```

此摘要的作用是让用户快速确认阶段成果，并在对话历史较长时提供清晰的进度锚点。

### 全局上下文传递

阶段2（架构设计）会产出一份「项目上下文摘要」，包含技术栈、框架约定、构建命令、测试命令等关键信息。此摘要会嵌入到技术方案文档的开头，供 Phase 3/4/5 直接引用，确保各阶段对项目环境的理解一致。

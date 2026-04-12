---
name: dev-pipeline
description: 端到端开发流水线编排器，将需求澄清、架构设计、任务拆解、并行编码、QA验证串联为自动化工作流。每个阶段通过独立的子 Agent 执行，支持不同阶段使用不同模型。适用于任何技术栈的项目开发。当用户想从需求文档到可运行代码、或需要系统化地开发一个新功能时触发。触发场景包括但不限于：用户说"dev pipeline"、"开发流水线"、"全流程开发"、"需求到代码"、"端到端开发"、"pipeline"、"从需求开始开发"、"编排开发流程"、"帮我开发这个功能"、"从这个PRD开始实现"、"我有个需求文档，帮我实现"、"帮我把这个需求做出来"、"开始做这个功能"。即使用户没有说"pipeline"，只要意图是系统化地从需求走到可运行代码，都应触发此 skill。
---

# 开发流水线 - 多智能体编排器

```
需求文档 → [PM Agent] → [架构师 Agent] → [人工审核] → [并行编码 Agent] → [QA Agent] → 交付
```

## 架构说明

本 Skill 采用 **主流程编排 + 子 Agent 执行** 架构：
- **主流程 (SKILL.md)**: 负责阶段编排、状态管理、人工卡点
- **子 Agent (agents/phase-*.md)**: 每个阶段由独立的子 Agent 执行，可使用不同模型
- **模型配置**: PM/架构师 → sonnet（规划分析），任务拆解 → sonnet（结构化），编码 → opus（高质量实现），QA → sonnet（验证审查）

---

## 流水线总览

| 阶段 | 角色 | 子 Agent 文件 | 推荐模型 | 输入 | 输出 | 人工卡点 |
|:-----|:-----|:--------------|:---------|:-----|:-----|:---------|
| 1. 需求澄清 | 产品经理 | `agents/phase-1-pm-agent.md` | sonnet | 原始需求 | PRD 文档 | 确认 PRD |
| 2. 架构设计 | 架构师 | `agents/phase-2-architect-agent.md` | sonnet | PRD + 代码库 | 技术方案+项目上下文 | 审核方案 |
| 3. 任务拆解 | 技术负责人 | `agents/phase-3-tasks-agent.md` | sonnet | 已批准方案 | 原子编码任务（按波次） | 确认拆解 |
| 4. 并行编码 | 开发者 | `agents/phase-4-coding-agent.md` | opus | 任务列表+项目上下文 | 实现代码 | - |
| 5. QA验证 | 测试工程师 | `agents/phase-5-qa-agent.md` | sonnet | 代码+PRD+方案 | 测试报告 | 验收交付 |

---

## 启动流程

### 第一步：确定功能名称

询问用户为本次开发起一个简短的英文标识名（用于文件命名），例如 `user-favorites`、`points-system`。

### 第二步：确定起始阶段

用 AskUserQuestion 询问：
- "从哪个阶段开始？"
  - 选项：
    - "从需求澄清开始 (Phase 1)" — 完整流水线
    - "已有 PRD，从架构设计开始 (Phase 2)"
    - "已有技术方案，从任务拆解开始 (Phase 3)"
    - "已有任务列表，从编码开始 (Phase 4)"

### 第三步：需求文档来源（仅从阶段1开始时）

用 AskUserQuestion 询问：
- "请提供需求文档的来源"
  - 选项：
    - "本地文件路径"
    - "飞书文档链接" → 使用 `feishu-requirement` skill 提取
    - "直接粘贴内容"

---

## 流水线控制

### 状态持久化

**每个阶段开始和结束时**都要更新 `docs/<功能名>-pipeline-state.json`：

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
  "updated_at": "2024-01-15T11:00:00"
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

---

## 阶段执行流程

### Phase 1: 需求澄清

**调用方式：**

```python
# 读取 Agent prompt
agent_prompt = Read("skills/dev-pipeline/agents/phase-1-pm-agent.md")

# 组装完整 prompt
full_prompt = f"""
{agent_prompt}

## 具体任务信息

- **功能名称**: {feature_name}
- **需求来源**: {requirement_source}
- **项目目录**: {project_dir}
"""

# 启动 PM Agent（使用 sonnet 模型）
Agent(
  prompt=full_prompt,
  model="sonnet",
  description=f"Phase 1: 需求澄清 - {feature_name}"
)
```

**阶段出口检查：**
- [ ] PRD 文件已保存到 `docs/` 目录
- [ ] 无占位文本或 TODO 标记
- [ ] 用户已明确批准

通过检查后，进入 Phase 2。

---

### Phase 2: 架构设计

**调用方式：**

```python
# 读取 Agent prompt
agent_prompt = Read("skills/dev-pipeline/agents/phase-2-architect-agent.md")

# 组装完整 prompt
full_prompt = f"""
{agent_prompt}

## 具体任务信息

- **功能名称**: {feature_name}
- **PRD 文件路径**: docs/{feature_name}-prd.md
- **项目目录**: {project_dir}
"""

# 启动架构师 Agent（使用 sonnet 模型）
Agent(
  prompt=full_prompt,
  model="sonnet",
  description=f"Phase 2: 架构设计 - {feature_name}"
)
```

**阶段出口检查：**
- [ ] 技术方案文件已保存到 `docs/` 目录
- [ ] 文档开头包含「项目上下文摘要」
- [ ] 方案完整覆盖 PRD 所有功能点
- [ ] 用户已明确批准

通过检查后，进入 Phase 3。

---

### Phase 3: 任务拆解

**调用方式：**

```python
# 读取 Agent prompt
agent_prompt = Read("skills/dev-pipeline/agents/phase-3-tasks-agent.md")

# 组装完整 prompt
full_prompt = f"""
{agent_prompt}

## 具体任务信息

- **功能名称**: {feature_name}
- **PRD 文件路径**: docs/{feature_name}-prd.md
- **技术方案文件路径**: docs/{feature_name}-architecture.md
- **项目目录**: {project_dir}
"""

# 启动技术负责人 Agent（使用 sonnet 模型）
Agent(
  prompt=full_prompt,
  model="sonnet",
  description=f"Phase 3: 任务拆解 - {feature_name}"
)
```

**阶段出口检查：**
- [ ] 任务清单已保存到 `docs/` 目录
- [ ] 任务清单开头包含项目上下文摘要
- [ ] 每个任务有明确的文件路径和验收标准
- [ ] 波次依赖关系合理
- [ ] 用户已明确批准

通过检查后，进入 Phase 4。

---

### Phase 4: 并行编码

**⚠️ 此阶段特殊：按波次执行，每个波次需要并行启动多个编码 Agent**

**调用方式：**

```python
# 读取 Agent prompt
agent_prompt = Read("skills/dev-pipeline/agents/phase-4-coding-agent.md")

# 读取任务清单，获取当前波次的任务列表
tasks_doc = Read(f"docs/{feature_name}-tasks.md")
current_wave_tasks = extract_tasks_for_wave(tasks_doc, current_wave)

# 组装完整 prompt
full_prompt = f"""
{agent_prompt}

## 具体任务信息

- **功能名称**: {feature_name}
- **任务清单文件路径**: docs/{feature_name}-tasks.md
- **技术方案文件路径**: docs/{feature_name}-architecture.md
- **项目目录**: {project_dir}
- **当前波次**: {current_wave}
- **本轮任务列表**: {', '.join(current_wave_tasks)}
"""

# 启动编码 Agent（使用 opus 模型）
Agent(
  prompt=full_prompt,
  model="opus",  # 编码阶段推荐用 Opus
  description=f"Phase 4 Wave {current_wave}: 并行编码 - {feature_name}"
)
```

**每个波次完成后：**
1. 检查 Agent 输出的文件修改列表
2. 验证编译通过
3. 更新状态文件的 `coding_progress`
4. 进入下一波次（如果还有）

**阶段出口检查：**
- [ ] 所有编码任务已完成
- [ ] 项目编译通过
- [ ] 现有测试无回归
- [ ] 代码已提交到版本控制

通过检查后，进入 Phase 5。

---

### Phase 5: QA 验证

**调用方式：**

```python
# 读取 Agent prompt
agent_prompt = Read("skills/dev-pipeline/agents/phase-5-qa-agent.md")

# 组装完整 prompt
full_prompt = f"""
{agent_prompt}

## 具体任务信息

- **功能名称**: {feature_name}
- **PRD 文件路径**: docs/{feature_name}-prd.md
- **技术方案文件路径**: docs/{feature_name}-architecture.md
- **任务清单文件路径**: docs/{feature_name}-tasks.md
- **项目目录**: {project_dir}
"""

# 启动 QA Agent（使用 sonnet 模型）
Agent(
  prompt=full_prompt,
  model="sonnet",
  description=f"Phase 5: QA 验证 - {feature_name}"
)
```

**阶段出口检查：**
- [ ] 测试报告已保存到 `docs/` 目录
- [ ] 所有 P0 用例通过
- [ ] 代码审查无高危问题
- [ ] 用户已验收

---

## 阶段切换质量检查

每次阶段切换前确认：
- [ ] 当前阶段产出完整（无占位文本）
- [ ] 用户已明确批准
- [ ] 所有已识别的缺口已解决或明确延期
- [ ] 文档已保存到 `docs/` 目录

### 每阶段完成后的检查点摘要

每个阶段完成后，向用户输出标准检查点摘要：

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

---

## 模型配置说明

每个阶段的推荐模型：

| 阶段 | 推荐模型 | 理由 |
|:-----|:---------|:-----|
| Phase 1: 需求澄清 | sonnet | 需求分析和文档生成，sonnet 足够 |
| Phase 2: 架构设计 | sonnet | 架构分析和方案设计，需要理解力 |
| Phase 3: 任务拆解 | sonnet | 结构化拆解，sonnet 足够 |
| Phase 4: 并行编码 | opus | 高质量代码实现，opus 效果最好 |
| Phase 5: QA 验证 | sonnet | 测试和审查，sonnet 足够 |

**配置方式：**

在 Agent 工具调用时通过 `model` 参数指定：
```python
Agent(
  prompt=...,
  model="opus",  # 或 "sonnet"
  description=...
)
```

用户也可以根据项目复杂度自定义模型配置。

---

## 异常处理

| 异常情况 | 处理方式 |
|:---------|:---------|
| Agent 执行失败 | 读取 Agent 输出的错误信息，分析原因后重新启动 Agent（补充缺失的上下文信息） |
| 用户拒绝批准 | 根据用户反馈修改，重新运行该阶段 Agent |
| 阶段产出不完整 | 补充必要信息后重新运行该阶段 Agent |
| 编译失败 | 定位失败原因，启动修复 Agent 或直接修复 |

---

## 恢复机制

如果流水线中断，重新启动时会：

1. 检测 `docs/<功能名>-pipeline-state.json` 是否存在
2. 如果存在，询问用户是否从中断处继续
3. 根据状态文件的 `current_phase` 和 `phase_status` 决定恢复点
4. 加载对应阶段的 Agent prompt 继续执行
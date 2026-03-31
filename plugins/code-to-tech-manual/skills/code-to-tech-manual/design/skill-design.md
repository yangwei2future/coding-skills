# code-to-tech-manual Skill 设计文档

## 背景与目标

将真实项目的实现代码导出为**技术手册**，以文本知识库的形式沉淀代码逻辑。
核心目标：在根据需求生成技术方案时，Claude 可以参考技术手册，了解项目已有实现的细节，避免重复设计或与现有实现冲突。

**主要消费场景**：方案生成参考（查阅"这类需求我们之前是怎么实现的"，重点记录设计决策和实现模式）

---

## Skill 基本信息

- **Skill 名称**：`code-to-tech-manual`
- **文档粒度**：方法级（流程步骤 + 关键方法签名 + 核心代码片段 ~20行 + 外部依赖）
- **组织维度**：按业务域，每域一个 markdown 文件

---

## 三种运行模式

```
/code-to-tech-manual init     # 全量扫描，首次建立手册
/code-to-tech-manual add      # 新功能实现后，追加知识
/code-to-tech-manual update   # 需求变更后，修正已有知识
```

---

## 手册存储结构

```
docs/tech-manual/
├── _index.md                  # 业务域总索引 + 元数据（last_documented_commit）
├── asset-catalog.md           # 资产目录域
├── asset-registration.md      # 资产注册域
├── permission.md              # 权限管理域
├── datasource.md              # 数据源域
└── ...（每个业务域一个文件）
```

`_index.md` 元数据区（追踪 diff 基准点）：

```markdown
---
last_documented_commit: 8c3dce3
last_updated: 2026-03-15
---
```

---

## init 模式：全量初始化（并行 Subagent）

### 三阶段流程

**阶段一：串行 — 域发现（Discovery）**

主 Claude 轻量扫描全局，识别业务域边界，生成域清单（不读代码内容，只扫类名/包名）：

```
域名: asset-catalog
相关文件:
  - AssetCatalogController.java
  - AssetCatalogServiceImpl.java
  - AssetCatalogRepository.java
  - AssetCatalogEntity.java
  - AssetCatalogDTO.java
  ...
```

**阶段二：并行 — 域文档生成（dispatching-parallel-agents）**

主 Claude 拿到域清单后，一次性启动所有域的 subagent，每个 subagent 只负责自己的域：

```
subagent-asset-catalog   → 读相关代码 → 生成 asset-catalog.md
subagent-permission      → 读相关代码 → 生成 permission.md
subagent-datasource      → 读相关代码 → 生成 datasource.md
...（并行执行，互不依赖）
```

每个 subagent 的输入：域名 + 文件列表 + 统一文档模板。

**阶段三：串行 — 汇总索引**

等所有 subagent 完成后，主 Claude 读取所有 md 文件，生成 `_index.md` 并写入 `last_documented_commit`。

---

## 单域文档结构（subagent 生成格式）

```markdown
# 资产目录（Asset Catalog）

## 业务概述
一句话描述该域解决什么问题，边界在哪里。

## 业务流程清单
- [创建资产目录](#创建资产目录)
- [删除资产目录](#删除资产目录)
- [编辑资产目录（含审批流）](#编辑资产目录)
- ...

---

## 创建资产目录

### 完整调用链
create(dto)
  ├── checkParentPermission(parentId)           # 私有方法
  │     └── permissionRepository.getUserCatalogPermission(userId, parentId)
  │           └── SQL: SELECT * FROM t_catalog_permission
  │                     WHERE user_id=? AND catalog_id=? AND del_flag=0
  │     └── 判断：permission 为空 或 type NOT IN ('EDIT','ADMIN') → 抛权限异常
  │
  ├── validateNameUnique(parentId, name)         # 私有方法
  │     └── catalogRepository.existsByParentAndName(parentId, name)
  │           └── LambdaQueryWrapper: parent_id=? AND name=? AND del_flag=0
  │     └── 判断：exists=true → 抛 CATALOG_NAME_DUPLICATE
  │
  ├── buildEntity(dto)                           # 私有方法
  │     └── 纯转换逻辑，无外部调用
  │     └── 关键赋值：status=DRAFT, level=父level+1, path=父path+"/"+id
  │
  └── catalogRepository.save(entity)
        └── catalogMapper.insert(entity)         # MyBatis，到底了

### 关键判断点汇总
| 判断点 | 条件 | 结果 |
|--------|------|------|
| 权限校验 | permission 为空或非 EDIT/ADMIN | 抛 NO_PERMISSION |
| 名称唯一 | 同父节点下存在同名 | 抛 NAME_DUPLICATE |
| level 计算 | 父节点 level + 1，超过最大层级 | 抛 MAX_LEVEL_EXCEEDED |

### 外部依赖
- Feign：无
- Kafka 发布：`dip-ia-asset-catalog-created`

### 变更历史
| 日期 | commit | 变更说明 |
|------|--------|---------|
| 2026-03-15 | abc1234 | 初始化文档 |
```

### 调用链下钻终止规则

| 情况 | 处理方式 |
|------|---------|
| 到达 `mapper.insert/select/update` 等 MyBatis 方法 | 记录 SQL 语义，停止下钻 |
| 到达纯数据转换（无条件判断、无外部调用） | 只记录"转换逻辑"，不继续展开 |
| 到达已在其他域文档化的公共方法 | 记录引用路径（如"见 permission.md #getUserPermission"），不重复展开 |

---

## add 模式：新增知识

**触发场景**：新功能开发完成，新增代码逻辑需要写入手册。

### 执行流程

```
第一步：定位变更范围
  git diff <last_documented_commit>...HEAD --name-only
  → 拿到新增/修改的文件列表

第二步：识别入口
  扫描变更文件中 Controller 的新增方法
  → 确定新业务流程的入口点

第三步：判断归属域
  根据入口类名、包名匹配已有域文件
  → 属于已有域：追加新流程块到对应 md 文件
  → 属于新域：新建 md 文件 + 更新 _index.md

第四步：调用链分析
  从入口方法出发，按下钻规则分析到 SQL 层
  → 生成新的流程块（格式同单域文档结构）

第五步：更新 _index.md 中的 last_documented_commit
```

---

## update 模式：修正知识

**触发场景**：已有需求变更，代码逻辑修改，需要修正手册中对应章节。

### 执行流程

```
第一步：定位变更范围
  git diff <last_documented_commit>...HEAD --name-only
  → 拿到修改的文件列表

第二步：定位受影响章节
  在所有域 md 文件中搜索涉及变更类/方法名的章节
  → 精确定位到具体的"流程块"标题

第三步：局部重新分析
  只对变更涉及的调用链做重新下钻
  不重新生成整个域文件

第四步：原地替换章节内容
  用新分析结果替换旧流程块
  在该流程块的"变更历史"表格中追加一条记录

第五步：更新 _index.md 中的 last_documented_commit
```

---

## add vs update 对比

| | add | update |
|--|-----|--------|
| 操作 | 追加新流程块 | 替换已有流程块 |
| 分析起点 | 新增的 Controller 方法 | 变更文件影响的章节 |
| _index.md | 新增域/流程条目 + 更新 commit | 只更新 commit |
| 变更历史 | 写入"初始化文档" | 写入具体变更说明 |

---

## 待实现事项

1. 编写 skill 文件：`~/.claude/skills/code-to-tech-manual.md`
2. 需要依赖的已有 skill：`dispatching-parallel-agents`
3. subagent 的 prompt 模板需要内嵌到 skill 文件中（包含下钻规则、文档格式模板）
4. 升级 `skill-creator` skill，使其能够指导编写"含并行 subagent 逻辑"的复杂 skill

---

## 前端扩展（2026-03-26）

### 背景

前端团队使用 React 18 + TypeScript + TanStack Router + Zustand 技术栈，需要与后端同等的代码知识库沉淀能力。

### 扩展要点

- **统一入口**：通过 `--type` 参数或自动检测区分前后端，`/code-to-tech-manual` 命令不变
- **组织维度**：前端按业务功能模块（对标后端按域），以 TanStack Router 路由路径为边界
- **调用链深度**：下钻至 HTTP 请求（`axios/fetch`），对标后端下钻至 MyBatis SQL
- **存储分区**：前端文件加 `fe-` 前缀，`_fe_index.md` 独立追踪前端 commit 基准

### 新增文件

| 文件 | 职责 |
|------|------|
| `references/be-call-chain-rules.md` | 后端调用链规则（从 SKILL.md 提取） |
| `references/be-subagent-prompt.md` | 后端 subagent 模板（从 SKILL.md 提取） |
| `references/fe-call-chain-rules.md` | 前端调用链规则 + 模块发现规则 |
| `references/fe-subagent-prompt.md` | 前端 subagent 任务模板 |
| `templates/domain-doc-template.md` | 后端域文档模板（从 references/ 迁移） |
| `templates/fe-module-doc-template.md` | 前端模块文档格式模板 |

### 设计文档

详见 `docs/superpowers/specs/2026-03-26-code-to-tech-manual-frontend-design.md`

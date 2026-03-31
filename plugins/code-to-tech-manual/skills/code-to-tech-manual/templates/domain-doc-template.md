# 域文档格式模板

这是生成每个业务域 md 文件时需要遵循的格式。

---

## 完整域文档格式

```markdown
# {域名中文名}（{DomainName}）

## 业务概述
一句话描述该域解决什么问题，边界在哪里。
（例：管理数据资产目录的树形层级结构，负责创建、编辑、删除目录节点，支持审批流程。）

## 业务流程清单
- [{流程名1}](#{流程名1锚点})
- [{流程名2}](#{流程名2锚点})
- ...

---

{每个流程块，见下方"单流程块格式"}
```

---

## 单流程块格式

```markdown
## {流程名}

### 完整调用链
{入口方法名}(params)
  ├── {子方法名}(params)                      # {方法说明}
  │     └── {更深层方法}(params)
  │           └── SQL: {SQL 语义描述}
  │                     WHERE {主要条件}
  │     └── 判断：{条件描述} → {结果/异常}
  │
  ├── {子方法名2}(params)                     # {方法说明}
  │     └── {Feign/外部调用描述}
  │
  └── {repository方法}(entity)
        └── {mapper方法}(entity)              # MyBatis，到底了

### 关键判断点汇总
| 判断点 | 条件 | 结果 |
|--------|------|------|
| {判断点名称} | {触发条件} | {处理结果/异常码} |
| ... | | |

### 外部依赖
- Feign：{FeignClientName}.{methodName}() — {调用目的}（无则填"无"）
- Kafka 发布：`{topic-name}` — {发布时机}（无则填"无"）
- Kafka 消费：`{topic-name}` — {消费场景}（无则填"无"）
- 事务边界：{@Transactional 覆盖范围说明}（无则填"无"）

### 变更历史
| 日期 | commit | 变更说明 |
|------|--------|---------|
| {日期} | {short hash} | 初始化文档 |
```

---

## 调用链写法示例

取自资产目录创建流程：

```markdown
### 完整调用链
create(dto)
  ├── checkParentPermission(parentId)           # 权限校验
  │     └── permissionRepository.getUserCatalogPermission(userId, parentId)
  │           └── SQL: SELECT * FROM t_catalog_permission
  │                     WHERE user_id=? AND catalog_id=? AND del_flag=0
  │     └── 判断：permission 为空 或 type NOT IN ('EDIT','ADMIN') → 抛 NO_PERMISSION
  │
  ├── validateNameUnique(parentId, name)        # 名称唯一性校验
  │     └── catalogRepository.existsByParentAndName(parentId, name)
  │           └── LambdaQueryWrapper: parent_id=? AND name=? AND del_flag=0
  │     └── 判断：exists=true → 抛 CATALOG_NAME_DUPLICATE
  │
  ├── buildEntity(dto)                          # 纯转换逻辑，无外部调用
  │     └── 关键赋值：status=DRAFT, level=父level+1, path=父path+"/"+id
  │
  └── catalogRepository.save(entity)
        └── catalogMapper.insert(entity)        # MyBatis，到底了
```

---

## 调用链下钻终止规则

| 情况 | 处理方式 |
|------|---------|
| 到达 `mapper.insert/select/update/delete` 等 MyBatis 方法 | 记录"SQL 语义：操作哪张表，主要 WHERE 条件"，标注"MyBatis，到底了" |
| 到达纯数据转换（无条件判断、无外部调用的 convert/build/assemble 方法） | 只记"纯转换逻辑，无外部调用"，列出关键赋值，不继续展开 |
| 到达其他域已文档化的公共方法 | 记录引用路径，如"见 permission.md #getUserPermission"，不重复展开 |
| 跨 Feign 调用 | 记录 Feign 接口名 + 方法名 + 调用目的，不下钻到远程服务内部 |
| 递归/循环调用 | 记录"递归调用自身，终止条件：{条件}"，不展开递归链 |

---

## 关键判断点识别指南

以下类型的判断必须在"关键判断点汇总"表格中体现：

- **权限校验**：用户是否有操作权限
- **唯一性约束**：名称/编码重复检查
- **状态机转换**：当前状态是否允许某操作（如"草稿才能发布"）
- **业务规则**：层级限制、数量上限等业务约束
- **审批流开关**：是否需要走审批流程
- **软删标记**：del_flag / is_deleted 的过滤逻辑

---

## _index.md 格式

```markdown
---
last_documented_commit: {7位 commit hash}
last_updated: {YYYY-MM-DD}
---

# 技术手册索引

## 业务域列表

| 域名 | 文件 | 业务概述 | 流程数量 |
|------|------|---------|---------|
| 资产目录 | [asset-catalog.md](asset-catalog.md) | 管理数据资产目录树形结构 | 5 个流程 |
| 权限管理 | [permission.md](permission.md) | 目录节点的权限分配与校验 | 3 个流程 |
| 数据源管理 | [datasource.md](datasource.md) | 数据源连接信息的增删改查 | 4 个流程 |

## 元数据
- 文档基准 commit：`{commit_hash}`（diff 基准点，add/update 时从此处开始 git diff）
- 最后更新：{YYYY-MM-DD}
```

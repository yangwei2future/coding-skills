# 前端模块文档格式模板

这是生成每个业务模块 md 文件时需要遵循的格式。

---

## 完整模块文档格式

```markdown
# {模块中文名}（{ModuleName}）

## 模块概述
一句话描述该模块解决什么问题，边界在哪里。
（例：管理数据资产目录的树形层级结构，支持创建、编辑、删除目录节点。）

## 功能流程清单
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

### 触发入口
`{组件名}` → {用户操作描述} → `{入口函数名}()`

> 触发类型：用户交互（onClick/onSubmit/onChange）/ 路由生命周期（loader/beforeEnter）/ 组件生命周期（useEffect）

### 完整调用链
{入口函数}()
  ├── {子步骤}()                              # {步骤说明}
  │     └── 判断：{条件描述} → {结果}
  │
  ├── {zustandStore}.{action}({params})       # Zustand Action
  │     └── {apiFunction}({params})
  │           └── {HTTP方法} {路径}
  │                 请求体：{ {关键字段} }
  │                 响应：{ {关键字段} }
  │                 网络请求，到底了
  │     └── 状态变更：{受影响的状态字段}
  │
  └── 成功后：{后续 UI 行为}

### 关键判断点汇总
| 判断点 | 条件 | 结果 |
|--------|------|------|
| 权限控制 | {权限标识符} 缺失 | {按钮禁用/页面重定向} |
| 表单校验 | {校验规则} | 阻断提交，展示错误提示 |
| 状态校验 | {业务状态条件} | {处理结果} |
| 异步状态 | 请求进行中 | 按钮 loading，防重复提交 |

### 外部依赖
- HTTP：`{方法} {路径}` — {调用目的}（无则填"无"）
- WebSocket/SSE：`{事件名}` — {订阅场景}（无则填"无"）
- 第三方 SDK：`{SDKName}.{method}()` — {调用目的}（无则填"无"）
- 依赖模块：`{module}.md #{hookName}` — {依赖说明}（无则填"无"）

### 变更历史
| 日期 | commit | 变更说明 |
|------|--------|---------|
| {日期} | {short hash} | 初始化文档 |
```

---

## 调用链写法示例

取自资产目录创建流程：

```markdown
### 触发入口
`AssetCatalogCreateModal` → 点击"确认"按钮 → `handleSubmit()`

> 触发类型：用户交互（onSubmit）

### 完整调用链
handleSubmit()
  ├── validateForm()                              # Ant Design Form 内置校验
  │     └── 判断：名称为空 → 阻断提交
  │     └── 判断：名称超过50字符 → 阻断提交
  │
  ├── usePermission('catalog:create')             # 权限 Hook，见 permission.md
  │     └── 判断：无权限 → 按钮禁用，不可触发
  │
  ├── assetCatalogStore.createCatalog(dto)        # Zustand Action
  │     └── createCatalogApi(dto)
  │           └── POST /api/asset/catalog
  │                 请求体：{ name, parentId, description }
  │                 响应：{ id, name, level, path }
  │                 网络请求，到底了
  │     └── 状态变更：catalogList 追加新节点，treeData 重新计算
  │
  └── 成功后：关闭 Modal，触发列表刷新
```

---

## `_fe_index.md` 格式

```markdown
---
last_documented_commit: {7位 commit hash}
last_updated: {YYYY-MM-DD}
---

# 前端技术手册索引

## 模块列表

| 模块名 | 文件 | 业务概述 | 流程数量 |
|--------|------|---------|---------|
| 资产目录 | [fe-asset-catalog.md](fe-asset-catalog.md) | 管理数据资产目录树形结构 | 5 个流程 |
| 权限配置 | [fe-permission.md](fe-permission.md) | 目录节点的权限分配与配置 | 3 个流程 |

## 元数据
- 文档基准 commit：`{commit_hash}`（diff 基准点，add/update 时从此处开始 git diff）
- 最后更新：{YYYY-MM-DD}
```

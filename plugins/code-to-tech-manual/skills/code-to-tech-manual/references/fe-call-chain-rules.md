# 前端调用链下钻规则

适用于 React 18 + TypeScript + TanStack Router + Zustand 技术栈。

---

## 模块发现规则（init 模式阶段一）

### 主要线索：TanStack Router 路由文件

扫描 `src/routes/` 目录（或 `routeTree.gen.ts`），以路由路径为模块边界：

```
/asset/catalog/**       →  模块：asset-catalog  →  fe-asset-catalog.md
/asset/registration/**  →  模块：asset-registration
/permission/**          →  模块：permission
```

### 模块文件聚合规则

```
模块名: asset-catalog
相关文件:
  - src/routes/asset/catalog/         # 路由页面组件
  - src/stores/assetCatalogStore.ts   # Zustand Store
  - src/hooks/useAssetCatalog.ts      # 业务 Hook
  - src/api/assetCatalogApi.ts        # API 请求函数
  - src/components/AssetCatalog*/     # 专属业务组件
```

### 过滤规则（跳过以下内容，不作为模块入口）

- 纯布局路由：`__root.tsx`、`_layout.tsx`
- 通用页面：`/login`、`/403`、`/404`
- 纯组件库封装：`src/components/common/`

---

## 调用链终止规则

分析 React 组件和 Hook 的调用链时，遇到以下情况停止下钻：

| 情况 | 处理方式 |
|------|---------|
| 到达 `axios.get/post` 或 `fetch` 调用 | 记录 HTTP 方法 + 路径 + 关键请求参数 + 响应结构，标注"网络请求，到底了" |
| 到达纯 UI 渲染逻辑（无数据请求、无状态变更） | 只记"纯渲染逻辑"，不展开 |
| 到达其他模块已文档化的公共 Hook | 记录引用路径（如"见 permission.md #usePermission"），不重复展开 |
| Zustand Store action | 记录 action 名 + 触发的状态字段变更，不展开 Store 内部实现 |
| 递归调用 | 记录"递归调用自身，终止条件：{条件}"，不展开 |

---

## 关键判断点识别指南

以下类型的判断必须在"关键判断点汇总"表格中体现：

- **权限控制**：路由守卫、按钮级权限（如 `usePermission('catalog:create')`）、组件显隐
- **表单校验规则**：必填、格式、业务规则（如名称唯一性前端预校验）
- **状态机/条件渲染**：根据数据状态显示不同 UI（如审批状态控制操作按钮）
- **异步流程控制**：loading/error/empty 状态处理、竞态处理（race condition）

---

## 触发入口类型说明

每个流程块的"触发入口"字段，需说明组件名 + 触发类型：

- **用户交互**：`onClick`、`onSubmit`、`onChange` 等事件处理器
- **路由生命周期**：路由 loader、beforeEnter 守卫
- **组件生命周期**：`useEffect`（首次挂载或依赖变更时触发）

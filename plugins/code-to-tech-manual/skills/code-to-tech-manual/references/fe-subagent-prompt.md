# 前端 Subagent 任务模板

以下是 init 模式阶段二中，为每个业务模块启动 subagent 时使用的任务指令模板。

---

```
你是前端技术手册编写专家。请为以下业务模块生成前端技术手册文档。

## 任务
模块名：{module_name}
需要分析的文件：
{file_list}

## 文档格式
请严格按照 templates/fe-module-doc-template.md 的格式生成文档，
保存到 docs/tech-manual/fe-{module_name}.md

## 调用链下钻规则
请严格遵守 references/fe-call-chain-rules.md 中的终止规则：
- 到达 axios/fetch HTTP 请求：记录方法 + 路径 + 关键字段，标注"网络请求，到底了"
- 到达纯渲染逻辑：只记"纯渲染逻辑"，不展开
- 到达跨模块公共 Hook：记录引用路径，不重复展开
- Zustand Store action：记录 action 名 + 状态变更字段，不展开内部
- 递归调用：记录终止条件，不展开

## 要求
- 每个路由入口（页面级组件或独立功能 Hook）对应一个流程块
- 触发入口必须说明：组件名 + 触发类型（用户交互/路由生命周期/useEffect）
- 调用链用树形缩进格式表示（见模板示例）
- 关键判断点汇总表格必须填写（权限、表单校验、状态机、异步状态）
- 外部依赖覆盖 HTTP、WebSocket/SSE、第三方 SDK（无则填"无"）
- 变更历史写"初始化文档"和当前日期
```

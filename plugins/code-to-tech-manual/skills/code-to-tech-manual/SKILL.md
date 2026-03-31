---
name: code-to-tech-manual
description: >
  将项目实现代码转化为结构化技术手册，以方法级粒度记录业务流程的完整调用链、关键判断点和外部依赖，沉淀为可检索的知识库，供后续技术方案设计时参考。

  支持前端（React/Vue）和后端（Java/Spring Boot）两种模式：
  - /code-to-tech-manual init：全量扫描项目，首次建立技术手册（使用并行 subagent 加速）
  - /code-to-tech-manual add：新功能开发完成后，追加新业务流程的文档
  - /code-to-tech-manual update：需求变更后，修正手册中已有章节

  支持 --type 参数：--type=frontend / --type=backend / --type=all（默认自动检测）

  当用户说"生成技术手册"、"记录代码实现"、"沉淀代码逻辑"、"更新技术文档"、"写技术手册"时触发。
  用户完成功能开发、代码合并主干后，也应主动建议使用此 skill。
---

# code-to-tech-manual

将代码逻辑以**方法级粒度**沉淀为技术手册，便于后续方案设计时查阅"这类需求我们之前是怎么实现的"。

手册存储位置：`docs/tech-manual/`

---

## 第一步：判断前后端类型

根据 `--type` 参数或自动检测：

| 检测条件 | 结果 |
|---------|------|
| `--type=frontend` | 前端模式 |
| `--type=backend` | 后端模式 |
| `--type=all` | 前后端均生成 |
| 未指定，仅有 `pom.xml` 或 `build.gradle` | 后端模式 |
| 未指定，仅有 `package.json` + `src/**/*.tsx` | 前端模式 |
| 未指定，两者都有 | 建议 `--type=all`，询问用户确认 |
| 未指定，都没有 | 报错提示，终止执行 |

---

## 第二步：判断运行模式

### 后端模式

| 情况 | 模式 |
|------|------|
| `docs/tech-manual/_index.md` 不存在 | `init` |
| 用户明确指定 `add` 或 `update` | 对应模式 |
| 用户未指定，但 `_index.md` 存在 | 询问用户是 add（新功能）还是 update（修改已有功能） |

### 前端模式

| 情况 | 模式 |
|------|------|
| `docs/tech-manual/_fe_index.md` 不存在 | `init` |
| 用户明确指定 `add` 或 `update` | 对应模式 |
| 用户未指定，但 `_fe_index.md` 存在 | 询问用户是 add（新功能）还是 update（修改已有功能） |

`--type=all` 时：前后端各自独立判断模式，`_index.md` 和 `_fe_index.md` 的 `last_documented_commit` 各自独立追踪。

---

## 后端 init 模式：全量初始化

### 阶段一：域发现（串行，主 Claude 执行）

扫描规则：
- 以 Controller 类名为主要线索（`XxxController` → 域名 `xxx`）
- 合并同域的 Service、Repository、Entity、DTO 文件
- 过滤通用类（`BaseController`、`CommonUtils` 等）

输出格式（内存中的工作清单，不写文件）：
```
域名: asset-catalog
相关文件:
  - dip-ia-asset-api/.../AssetCatalogController.java
  - dip-ia-asset-service/.../AssetCatalogServiceImpl.java
  - dip-ia-asset-dao/.../AssetCatalogRepository.java
  - dip-ia-asset-dao/.../AssetCatalogEntity.java
  - dip-ia-asset-model/.../AssetCatalogDTO.java
```

### 阶段二：并行域文档生成（dispatching-parallel-agents）

拿到域清单后，一次性为每个域启动一个 subagent，全部并行执行。

subagent 任务模板：见 `references/be-subagent-prompt.md`
调用链下钻规则：见 `references/be-call-chain-rules.md`
文档格式模板：见 `templates/domain-doc-template.md`

### 阶段三：汇总索引（串行，主 Claude 执行）

1. 读取所有已生成的域 md 文件
2. 获取当前 HEAD commit hash：`git rev-parse --short HEAD`
3. 生成 `docs/tech-manual/_index.md`（格式见 `templates/domain-doc-template.md` 末尾的 `_index.md 格式`）

---

## 后端 add 模式：追加新功能文档

**第一步：定位变更范围**
```bash
last_commit=$(从 docs/tech-manual/_index.md 的 YAML 中读取 last_documented_commit)
git diff ${last_commit}...HEAD --name-only
```

**第二步：识别新入口**

从变更文件中找 Controller 类，定位其中新增的方法：
- 新增方法：`git diff ${last_commit}...HEAD -- {controller_file}` 中出现 `+` 前缀的方法签名
- 这些方法即为新业务流程的入口点

**第三步：判断归属域**

根据入口类的包名/类名，匹配 `docs/tech-manual/` 中已有的域文件：
- 匹配已有域：追加新流程块到对应 md 文件末尾
- 未匹配到：新建域 md 文件，同时在 `_index.md` 的业务域列表中追加该域

**第四步：调用链分析**

从入口方法出发，按 `references/be-call-chain-rules.md` 下钻，生成新流程块（格式见 `templates/domain-doc-template.md`）。

**第五步：更新 `_index.md`**

将 `last_documented_commit` 更新为当前 HEAD commit hash。

---

## 后端 update 模式：修正已有文档

**第一步：定位变更范围**
```bash
last_commit=$(从 _index.md 读取 last_documented_commit)
git diff ${last_commit}...HEAD --name-only
```

**第二步：定位受影响章节**

在 `docs/tech-manual/` 所有 md 文件中，搜索包含变更类名或方法名的章节标题，精确定位到具体"流程块"（`## 流程名` 级别）。若多个域文件都引用了同一个变更方法，需要同时更新所有引用处。

**第三步：局部重新分析**

只对变更涉及的调用链重新下钻，不重新生成整个域文件。

**第四步：原地替换章节内容**

用新分析结果替换旧流程块，在变更历史表格末尾追加：
```markdown
| {今天日期} | {short commit hash} | {本次变更的一句话说明} |
```

**第五步：更新 `_index.md`**

将 `last_documented_commit` 更新为当前 HEAD commit hash。

---

## 后端质量检查清单

- [ ] 每个 Controller public 方法都有对应流程块
- [ ] 调用链树到达 SQL 层或终止条件才停止
- [ ] 关键判断点表格无遗漏（权限、唯一性、状态机等）
- [ ] Kafka 发布/消费在"外部依赖"中标注
- [ ] Feign 调用在"外部依赖"中标注（不下钻内部）
- [ ] 变更历史有记录（init 写"初始化文档"，update 写具体变更说明）

---

## 后端 add vs update 速查

| | add | update |
|--|-----|--------|
| 操作 | 追加新流程块 | 替换已有流程块 |
| 分析起点 | 变更文件中新增的 Controller 方法 | 变更文件影响到的已有章节 |
| `_index.md` 业务域列表 | 可能新增域条目 | 不变 |
| `_index.md` commit | 更新 | 更新 |
| 变更历史 | 写"初始化文档" | 写具体变更说明 |

---

## 前端 init 模式：全量初始化

### 阶段一：模块发现（串行，主 Claude 执行）

扫描规则：见 `references/fe-call-chain-rules.md` 的"模块发现规则"章节。

输出格式（内存中的工作清单，不写文件）：
```
模块名: asset-catalog
相关文件:
  - src/routes/asset/catalog/
  - src/stores/assetCatalogStore.ts
  - src/hooks/useAssetCatalog.ts
  - src/api/assetCatalogApi.ts
  - src/components/AssetCatalog*/
```

### 阶段二：并行模块文档生成（dispatching-parallel-agents）

拿到模块清单后，一次性为每个模块启动一个 subagent，全部并行执行。

subagent 任务模板：见 `references/fe-subagent-prompt.md`
调用链下钻规则：见 `references/fe-call-chain-rules.md`
文档格式模板：见 `templates/fe-module-doc-template.md`

### 阶段三：汇总索引（串行，主 Claude 执行）

1. 读取所有已生成的 `fe-*.md` 文件
2. 获取当前 HEAD commit hash：`git rev-parse --short HEAD`
3. 生成 `docs/tech-manual/_fe_index.md`（格式见 `templates/fe-module-doc-template.md` 末尾的 `_fe_index.md 格式`）

---

## 前端 add 模式：追加新功能文档

**第一步：定位变更范围**
```bash
last_commit=$(从 docs/tech-manual/_fe_index.md 的 YAML 中读取 last_documented_commit)
git diff ${last_commit}...HEAD --name-only
```

**第二步：识别新入口**

从变更文件中识别前端新增的业务入口：
- `src/routes/` 下新增的路由文件（主要线索，对应新增页面）
- `src/api/` 下新增的 API 函数（对应新增接口调用）
- `src/hooks/` 下新增的业务 Hook（辅助线索，对应新增交互逻辑）

**第三步：判断归属模块**

根据路由路径匹配 `_fe_index.md` 中已有的模块：
- 匹配已有模块：追加新流程块到对应 `fe-{module}.md` 文件末尾
- 未匹配到：新建 `fe-{module}.md` 文件，同时在 `_fe_index.md` 的模块列表中追加该模块

**第四步：调用链分析**

从入口函数出发，按 `references/fe-call-chain-rules.md` 下钻，生成新流程块（格式见 `templates/fe-module-doc-template.md`）。

**第五步：更新 `_fe_index.md`**

将 `last_documented_commit` 更新为当前 HEAD commit hash。

---

## 前端 update 模式：修正已有文档

**第一步：定位变更范围**
```bash
last_commit=$(从 docs/tech-manual/_fe_index.md 的 YAML 中读取 last_documented_commit)
git diff ${last_commit}...HEAD --name-only
```

**第二步：定位受影响章节**

在 `docs/tech-manual/` 所有 `fe-*.md` 文件中，搜索包含变更组件名/Hook 名/API 函数名的章节。若多个模块文件引用了同一个变更 Hook，需要同时更新所有引用处。

**第三步：局部重新分析**

只对变更涉及的调用链重新下钻，不重新生成整个模块文件。

**第四步：原地替换章节内容**

用新分析结果替换旧流程块，在变更历史表格末尾追加：
```markdown
| {今天日期} | {short commit hash} | {本次变更的一句话说明} |
```

**第五步：更新 `_fe_index.md`**

将 `last_documented_commit` 更新为当前 HEAD commit hash。

---

## 前端质量检查清单

- [ ] 每个路由入口（页面级组件）都有对应流程块
- [ ] 触发入口字段已填写（组件名 + 触发类型）
- [ ] 调用链到达 HTTP 请求层或终止条件才停止
- [ ] 关键判断点表格无遗漏（权限、表单校验、状态机、异步状态）
- [ ] WebSocket/SSE 订阅在"外部依赖"中标注（无则填"无"）
- [ ] 跨模块公共 Hook 引用路径已标注，不重复展开
- [ ] 变更历史有记录（init 写"初始化文档"，update 写具体变更说明）

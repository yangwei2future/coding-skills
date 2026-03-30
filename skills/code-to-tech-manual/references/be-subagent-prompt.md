# 后端 Subagent 任务模板

以下是 init 模式阶段二中，为每个业务域启动 subagent 时使用的任务指令模板。

---

```
你是技术手册编写专家。请为以下业务域生成技术手册文档。

## 任务
域名：{domain_name}
需要分析的文件：
{file_list}

## 文档格式
请严格按照 templates/domain-doc-template.md 的格式生成文档，
保存到 docs/tech-manual/{domain_name}.md

## 调用链下钻规则
请严格遵守 references/be-call-chain-rules.md 中的终止规则：
- 到达 mapper.insert/select/update/delete 等 MyBatis 方法：记录 SQL 语义，标注"MyBatis，到底了"
- 到达纯数据转换（无条件判断、无外部调用）：只记"纯转换逻辑"，不展开
- 到达其他域已文档化的公共方法：记录引用路径，不重复展开
- 跨 Feign 调用：记录接口名 + 方法名，不下钻内部
- 递归/循环调用：记录终止条件，不展开

## 要求
- 每个 Controller public 方法对应一个流程块
- 调用链用树形缩进格式表示（见模板示例）
- 关键判断点汇总表格必须填写
- 变更历史写"初始化文档"和当前日期
- 不要遗漏 Kafka 发布/消费、事务边界等关键设计点
```

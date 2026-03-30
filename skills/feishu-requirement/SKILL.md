---
name: feishu-requirement
description: 从飞书文档提取需求内容并保存为本地Markdown文件到docs目录。当用户需要从飞书导入需求文档时使用
allowed-tools: Bash(python3:*)
compatibility: 需要设置环境变量 FEISHU_TOKEN（飞书 API 认证 token）
---

# 飞书需求文档提取器

从飞书文档提取需求内容并保存为本地Markdown文件。

## 使用方法

```bash
/feishu-requirement <飞书文档URL>
```

**参数说明：**
- 飞书文档URL（必填）：格式必须是 `https://li.feishu.cn/docx/...` 或 `https://li.feishu.cn/wiki/...`
- 文档将自动保存到 `docs` 目录

**示例：**
```bash
# 提取飞书文档到 docs 目录
/feishu-requirement https://li.feishu.cn/docx/abc123
```

## 工作流程

### 第一步：验证输入参数

1. **检查URL参数**
   - 如果用户未提供URL参数（$0 为空），提示使用方法并退出
   - 验证URL格式必须是 `https://li.feishu.cn/docx/` 或 `https://li.feishu.cn/wiki/` 开头
   - 如果格式不正确，提示用户提供正确的URL并退出

2. **确定保存目录和文件名**
   - 固定使用 `docs` 目录保存文档
   - 文件名根据内容类型自动添加前缀：
     - 需求文档：`需求_`
     - 技术方案：`方案_`
   - 通过分析文档内容判断类型（标题/关键词）

### 第二步：执行Python脚本提取文档

调用独立的 Python 脚本 `extract_feishu.py` 来执行文档提取：

**执行步骤**：
1. 使用 Bash 工具执行脚本：`python3 extract_feishu.py <飞书URL> docs`
2. 脚本会自动处理：
   - 提交提取任务到飞书 API
   - 轮询任务状态（最多等待2分钟）
   - 下载文档内容
   - 保存到本地文件
3. 脚本内置 token，无需额外配置

### 第三步：报告结果

脚本执行成功后会自动输出：
- 文档名称
- 保存路径
- 文档大小（字符数）
- 后续操作建议（使用 `/test-case` 命令生成测试用例）

## 脚本文件说明

`extract_feishu.py` - 独立的飞书文档提取脚本
- 位置：skill 目录下
- 功能：完整的文档提取和保存逻辑
- 优势：代码独立、易于维护、支持大文档

## 输出示例

```
✓ 文档提取成功
文档名称：数据质量3.0-IAMAP产品方案-25H2
保存路径：docs/方案_数据质量3.0-IAMAP产品方案-25H2.md
文档大小：66234 字符

需求文档已保存，你可以使用 /test-case 命令基于此需求生成测试用例。
```

## 注意事项

1. **URL验证**：确保URL格式正确，必须是飞书文档链接
2. **网络连接**：需要能够访问飞书API服务
3. **Token配置**：使用前需设置环境变量 `FEISHU_TOKEN`，例如在 `~/.zshrc` 中添加 `export FEISHU_TOKEN=<your-token>`
4. **大文档支持**：优化了大文档的保存处理，支持 100KB+ 的文档
5. **错误处理**：脚本会输出详细的错误信息到标准错误流

## 后续操作建议

文档保存成功后，提示用户：
- 可以使用 `/test-case` 命令基于此需求生成测试用例
- 可以直接查看保存的需求文档
- 可以继续提取其他飞书文档

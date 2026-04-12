# PDF Reader Skill - 全能PDF处理工具

使用 PyMuPDF 进行 PDF 读取、编辑、生成全流程操作

## 功能概览

### 📖 读取能力
- 100%准确文本提取
- 完美中文支持
- 图片、表格提取

### ✏️ 编辑能力
- 文本、图片编辑
- 水印、注释添加
- 页面管理

### 🔀 合并拆分
- 多PDF合并
- 单PDF拆分

### 🔒 安全加密
- AES-256加密
- 权限控制

### 📝 PDF生成
- 从零创建
- 格式转换
- 批量生成

---

## 快速开始

### 安装依赖
```bash
pip3 install pymupdf
```

### 基础示例

#### 读取PDF
```python
import fitz
doc = fitz.open("file.pdf")
text = doc[0].get_text()
```

#### 编辑PDF
```python
doc = fitz.open("file.pdf")
page = doc[0]
page.insert_text(fitz.Point(100, 100), "Hello World")
doc.save("edited.pdf")
```

#### 创建PDF
```python
doc = fitz.open()
page = doc.new_page()
page.insert_text(fitz.Point(100, 100), "New PDF")
doc.save("created.pdf")
```

---

## 功能模块（渐进式学习）

### 📖 [读取功能详解](modules/reading.md)
文本提取、图片提取、表格提取、区域提取

### ✏️ [编辑功能详解](modules/editing.md)
添加文本/图片、水印、注释、页面管理

### 🔀 [合并拆分详解](modules/merging.md)
PDF合并、拆分、页面提取

### 🔒 [安全加密详解](modules/security.md)
加密、解密、权限设置

### 📝 [PDF生成详解](modules/generation.md)
创建PDF、格式转换、批量生成

### 💡 [完整示例](modules/examples.md)
工具类封装、批量处理脚本

---

## 使用场景

✅ **简历处理** - 提取信息、添加水印、合并作品集
✅ **文档管理** - 提取合同信息、批量添加页眉页脚
✅ **报告生成** - 从数据生成PDF、添加图表
✅ **电子书处理** - 章节提取、添加书签
✅ **自动化办公** - 批量处理、格式转换

---

## 对比传统方法

| 功能 | 传统方案 | PyMuPDF |
|------|---------|---------|
| 读取 | qlmanage + OCR | ✅ 100%准确 |
| 编辑 | Adobe Acrobat（付费） | ✅ 免费开源 |
| 合并 | 在线工具（隐私风险） | ✅ 本地安全 |
| 加密 | 商业软件 | ✅ AES-256 |
| 生成 | ReportLab（复杂） | ✅ 简单API |
| 中文 | 需额外配置 | ✅ 原生支持 |

---

## 使用方式

### 命令方式
```
/pdf file.pdf              # 读取PDF
/pdf file.pdf --edit       # 编辑PDF
/pdf file.pdf --watermark  # 添加水印
/pdf --merge a.pdf b.pdf   # 合并PDF
/pdf --split file.pdf      # 拆分PDF
```

### 对话方式
直接描述需求即可：
- "读取这个PDF的内容"
- "给这个PDF添加水印"
- "合并这些PDF文件"
- "从零创建一个PDF"

---

## 技术实现

基于 **PyMuPDF**（Python bindings for MuPDF）：
- 高性能C语言渲染引擎
- Python简洁API
- 跨平台支持（Windows/macOS/Linux）
- 开源免费（GNU Affero GPL）

---

## 重要提示

✅ **性能优化** - 大文件使用结构化数据提取
✅ **内存管理** - 处理完记得 `doc.close()`
✅ **异常处理** - 用 try-except 包裹文件操作
✅ **版权意识** - 遵守PDF相关法律法规
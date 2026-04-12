# PDF读取功能模块

精准提取PDF内容，支持文本、图片、表格等多种格式

---

## 核心能力

✅ **100%准确文本提取** - 直接解析PDF结构
✅ **完美中文支持** - 精准识别所有中文字符
✅ **结构完整保留** - 段落、表格、列表格式
✅ **图片提取** - 提取PDF中的所有图片
✅ **表格识别** - 智能识别表格并转为DataFrame

---

## 基础用法

### 1. 提取全部文本

```python
import fitz

doc = fitz.open("file.pdf")

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    print(f"第 {page_num + 1} 页:")
    print(text)

doc.close()
```

### 2. 提取特定区域文本

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 定义矩形区域 (x0, y0, x1, y1)
rect = fitz.Rect(100, 100, 500, 500)
text = page.get_text("text", clip=rect)

print("指定区域文本:")
print(text)

doc.close()
```

### 3. 提取结构化数据

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 获取结构化文本数据
blocks = page.get_text("dict")["blocks"]

for block in blocks:
    if "lines" in block:  # 文本块
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"文本: {span['text']}")
                print(f"字体: {span['font']}")
                print(f"大小: {span['size']}")
                print(f"位置: {span['bbox']}")

doc.close()
```

---

## 高级功能

### 提取图片

```python
import fitz

doc = fitz.open("file.pdf")

for page_num in range(len(doc)):
    page = doc[page_num]
    images = page.get_images()

    print(f"第 {page_num + 1} 页发现 {len(images)} 张图片")

    for img_index, img in enumerate(images):
        xref = img[0]  # 图片引用ID
        pix = fitz.Pixmap(doc, xref)

        # 保存图片
        if pix.n < 5:  # GRAY or RGB
            pix.save(f"page{page_num+1}_img{img_index+1}.png")
        else:  # CMYK: convert to RGB first
            pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(f"page{page_num+1}_img{img_index+1}.png")

        pix = None  # 释放内存

doc.close()
```

### 提取表格

```python
import fitz
import pandas as pd

doc = fitz.open("file.pdf")
page = doc[0]

# 查找表格
tabs = page.find_tables()

print(f"发现 {len(tabs.tables)} 个表格")

for i, tab in enumerate(tabs.tables):
    # 转为DataFrame
    df = tab.to_pandas()
    print(f"\n表格 {i+1}:")
    print(df)

    # 导出为CSV
    df.to_csv(f"table_{i+1}.csv", index=False)

doc.close()
```

### 提取带格式的文本

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 提取HTML格式
html_text = page.get_text("html")
with open("output.html", "w") as f:
    f.write(html_text)

# 提取XML格式
xml_text = page.get_text("xml")
with open("output.xml", "w") as f:
    f.write(xml_text)

# 提取Markdown格式
md_text = page.get_text("text")
# 可以进一步处理转换为Markdown

doc.close()
```

### 提取特定颜色的文本

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 获取所有文本块
blocks = page.get_text("dict")["blocks"]

for block in blocks:
    if "lines" in block:
        for line in block["lines"]:
            for span in line["spans"]:
                # 检查颜色（RGB值）
                color = span["color"]
                if color == 0xFF0000:  # 红色文本
                    print(f"红色文本: {span['text']}")
                elif color == 0x0000FF:  # 蓝色文本
                    print(f"蓝色文本: {span['text']}")

doc.close()
```

---

## 搜索功能

### 搜索文本位置

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 搜索文本
search_text = "重要"
areas = page.search_for(search_text)

print(f"找到 {len(areas)} 处 '{search_text}'")

for i, area in enumerate(areas):
    print(f"位置 {i+1}: {area}")
    # area 是一个 Rect 对象，包含坐标 (x0, y0, x1, y1)

doc.close()
```

### 高亮搜索结果

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 搜索并高亮
search_text = "重要"
areas = page.search_for(search_text)

for area in areas:
    # 添加黄色高亮
    highlight = page.add_highlight_annot(area)
    highlight.set_colors(stroke=(1, 1, 0))  # RGB: 黄色
    highlight.update()

doc.save("highlighted.pdf")
doc.close()
```

---

## 批量提取

### 提取多个PDF的文本

```python
import fitz
import os

def extract_all_pdfs(directory, output_file):
    """批量提取目录下所有PDF的文本"""
    with open(output_file, "w", encoding="utf-8") as f:
        for filename in os.listdir(directory):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(directory, filename)
                doc = fitz.open(pdf_path)

                f.write(f"\n{'='*80}\n")
                f.write(f"文件: {filename}\n")
                f.write(f"{'='*80}\n\n")

                for page in doc:
                    f.write(page.get_text())

                doc.close()

# 使用
extract_all_pdfs("./pdfs", "all_texts.txt")
```

---

## 性能优化

### 大文件处理

```python
import fitz

# 对于大文件，使用选择性加载
doc = fitz.open("large.pdf")

# 只加载特定页面（按需加载）
for page_num in [0, 5, 10]:  # 只读取第1、6、11页
    page = doc[page_num]
    text = page.get_text()
    print(text)

doc.close()
```

### 使用生成器节省内存

```python
import fitz

def extract_text_generator(pdf_path):
    """生成器方式提取文本，节省内存"""
    doc = fitz.open(pdf_path)
    for page in doc:
        yield page.get_text()
    doc.close()

# 使用
for text in extract_text_generator("large.pdf"):
    process(text)  # 逐页处理
```

---

## 实用场景

### 📄 简历信息提取
```python
def extract_resume_info(pdf_path):
    """提取简历关键信息"""
    doc = fitz.open(pdf_path)
    text = "".join([page.get_text() for page in doc])

    import re

    info = {
        "email": re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text),
        "phone": re.search(r'\b\d{11}\b', text),  # 手机号
        "name": re.search(r'姓名[：:]\s*(\S+)', text),
    }

    return info
```

### 📑 合同关键条款提取
```python
def extract_contract_terms(pdf_path):
    """提取合同关键条款"""
    doc = fitz.open(pdf_path)
    text = "".join([page.get_text() for page in doc])

    terms = []
    # 查找所有编号条款
    import re
    pattern = r'\d+\.[\s\S]*?(?=\n\d+\.|$)'
    matches = re.findall(pattern, text)

    return matches
```

---

## 错误处理

```python
import fitz

def safe_extract_text(pdf_path):
    """安全的文本提取"""
    try:
        doc = fitz.open(pdf_path)
        text_list = []

        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                text = page.get_text()
                text_list.append(text)
            except Exception as e:
                print(f"警告: 第 {page_num + 1} 页提取失败: {e}")
                continue

        doc.close()
        return "\n".join(text_list)

    except Exception as e:
        print(f"错误: 无法打开文件 {pdf_path}: {e}")
        return None
```

---

## 对比传统方法

| 功能 | qlmanage + OCR | PyMuPDF |
|------|----------------|---------|
| 文本准确度 | 低（依赖OCR） | ✅ 100%精准 |
| 中文识别 | 不稳定 | ✅ 完美支持 |
| 处理速度 | 慢（图片转换） | ✅ 秒级完成 |
| 结构保留 | 丢失 | ✅ 完整保留 |
| 批量处理 | 困难 | ✅ 简单 |

---

## 注意事项

⚠️ **扫描版PDF** - 需要配合OCR工具使用
⚠️ **加密PDF** - 需要先解密才能提取
⚠️ **图片文本** - 无法直接提取，需OCR
⚠️ **内存管理** - 处理完记得关闭文档

---

## 下一步

- [编辑功能](editing.md) - 学习如何编辑PDF
- [合并拆分](merging.md) - 学习PDF合并拆分
- [完整示例](examples.md) - 查看更多实用代码
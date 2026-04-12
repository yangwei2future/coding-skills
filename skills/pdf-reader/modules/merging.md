# PDF合并拆分模块

灵活处理PDF文档的合并、拆分、页面提取等操作

---

## 核心能力

✅ **多PDF合并** - 将多个PDF合并为一个文档
✅ **PDF拆分** - 将PDF拆分为单页或多页文档
✅ **页面提取** - 提取特定页面范围
✅ **页面重排** - 重新组织页面顺序
✅ **批量处理** - 自动化处理大量文件

---

## PDF合并

### 1. 基础合并

```python
import fitz

# 创建新文档
result = fitz.open()

# 合并多个PDF
pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]

for pdf_file in pdf_files:
    doc = fitz.open(pdf_file)
    result.insert_pdf(doc)  # 插入所有页面
    doc.close()

result.save("merged.pdf")
result.close()
```

### 2. 选择性合并

```python
import fitz

result = fitz.open()

# 合并特定页面
doc1 = fitz.open("file1.pdf")
result.insert_pdf(doc1, from_page=0, to_page=2)  # 只合并前3页
doc1.close()

doc2 = fitz.open("file2.pdf")
result.insert_pdf(doc2, from_page=5, to_page=9)  # 合并第6-10页
doc2.close()

result.save("partial_merged.pdf")
result.close()
```

### 3. 高级合并选项

```python
import fitz

result = fitz.open()

doc = fitz.open("source.pdf")

# 合并时设置链接、批注、表单字段
result.insert_pdf(
    doc,
    from_page=0,
    to_page=-1,  # -1表示到最后一页
    links=True,  # 保留链接
    annots=True,  # 保留批注
    widgets=True,  # 保留表单字段
    show_progress=True  # 显示进度（大文件）
)

doc.close()
result.save("advanced_merged.pdf")
result.close()
```

### 4. 合并并添加分隔页

```python
import fitz

result = fitz.open()

pdf_files = ["chapter1.pdf", "chapter2.pdf", "chapter3.pdf"]

for i, pdf_file in enumerate(pdf_files):
    # 添加分隔页
    if i > 0:
        sep_page = result.new_page()
        sep_page.insert_text(
            fitz.Point(200, 400),
            f"第 {i+1} 章",
            fontsize=24,
            fontname="helv-b"
        )

    # 合并PDF
    doc = fitz.open(pdf_file)
    result.insert_pdf(doc)
    doc.close()

result.save("book_with_separators.pdf")
result.close()
```

---

## PDF拆分

### 1. 拆分为单页

```python
import fitz

doc = fitz.open("original.pdf")

# 拆分为单页PDF
for i in range(len(doc)):
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(f"page_{i+1}.pdf")
    new_doc.close()

doc.close()
```

### 2. 按固定页数拆分

```python
import fitz

def split_by_pages(pdf_path, pages_per_file):
    """按固定页数拆分PDF"""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    for start in range(0, total_pages, pages_per_file):
        end = min(start + pages_per_file, total_pages)

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end-1)
        new_doc.save(f"part_{start//pages_per_file + 1}.pdf")
        new_doc.close()

    doc.close()

# 使用：每5页拆分一个文件
split_by_pages("large_file.pdf", 5)
```

### 3. 按章节拆分

```python
import fitz

def split_by_chapters(pdf_path, chapter_pages):
    """
    按章节拆分PDF
    chapter_pages: 章节起始页列表，如 [0, 10, 25, 40]
    """
    doc = fitz.open(pdf_path)

    for i in range(len(chapter_pages)):
        start = chapter_pages[i]
        end = chapter_pages[i+1] if i+1 < len(chapter_pages) else len(doc)

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end-1)
        new_doc.save(f"chapter_{i+1}.pdf")
        new_doc.close()

    doc.close()

# 使用
split_by_chapters("book.pdf", [0, 15, 30, 50])
```

---

## 页面提取

### 1. 提取特定页面范围

```python
import fitz

doc = fitz.open("original.pdf")

# 提取第6-10页
new_doc = fitz.open()
new_doc.insert_pdf(doc, from_page=5, to_page=9)

new_doc.save("pages_6_to_10.pdf")
new_doc.close()
doc.close()
```

### 2. 提取不连续页面

```python
import fitz

doc = fitz.open("original.pdf")

# 提取第1、3、5、7页
new_doc = fitz.open()
for page_num in [0, 2, 4, 6]:
    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

new_doc.save("selected_pages.pdf")
new_doc.close()
doc.close()
```

### 3. 按条件提取页面

```python
import fitz

def extract_pages_with_text(pdf_path, search_text):
    """提取包含特定文本的页面"""
    doc = fitz.open(pdf_path)
    new_doc = fitz.open()

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if search_text in text:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    new_doc.save(f"pages_with_{search_text}.pdf")
    new_doc.close()
    doc.close()

# 使用
extract_pages_with_text("report.pdf", "重要")
```

---

## 页面重排

### 1. 反转页面顺序

```python
import fitz

doc = fitz.open("original.pdf")

# 创建新文档
new_doc = fitz.open()

# 反向插入页面
for page_num in range(len(doc)-1, -1, -1):
    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

new_doc.save("reversed.pdf")
new_doc.close()
doc.close()
```

### 2. 自定义页面顺序

```python
import fitz

doc = fitz.open("original.pdf")
new_doc = fitz.open()

# 自定义顺序：第3页、第1页、第5页、第2页
custom_order = [2, 0, 4, 1]

for page_num in custom_order:
    if page_num < len(doc):
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

new_doc.save("reordered.pdf")
new_doc.close()
doc.close()
```

### 3. 交错合并页面

```python
import fitz

def interleave_pdfs(pdf1_path, pdf2_path):
    """交错合并两个PDF的页面"""
    doc1 = fitz.open(pdf1_path)
    doc2 = fitz.open(pdf2_path)

    result = fitz.open()
    max_pages = max(len(doc1), len(doc2))

    for i in range(max_pages):
        if i < len(doc1):
            result.insert_pdf(doc1, from_page=i, to_page=i)
        if i < len(doc2):
            result.insert_pdf(doc2, from_page=i, to_page=i)

    result.save("interleaved.pdf")
    result.close()
    doc1.close()
    doc2.close()

# 使用
interleave_pdfs("even_pages.pdf", "odd_pages.pdf")
```

---

## 批量处理

### 1. 批量合并文件夹中的PDF

```python
import fitz
import os

def batch_merge(directory, output_file):
    """批量合并文件夹中的所有PDF"""
    result = fitz.open()

    # 获取所有PDF文件
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    pdf_files.sort()  # 按文件名排序

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)
        doc = fitz.open(pdf_path)
        result.insert_pdf(doc)
        doc.close()

    result.save(output_file)
    result.close()

# 使用
batch_merge("./pdfs", "all_merged.pdf")
```

### 2. 批量拆分文件夹中的PDF

```python
import fitz
import os

def batch_split(directory, output_dir):
    """批量拆分文件夹中的所有PDF"""
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(directory, filename)
            doc = fitz.open(pdf_path)

            # 拆分为单页
            for i in range(len(doc)):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)

                output_path = os.path.join(
                    output_dir,
                    f"{filename}_page_{i+1}.pdf"
                )
                new_doc.save(output_path)
                new_doc.close()

            doc.close()

# 使用
batch_split("./input_pdfs", "./output_pages")
```

---

## 实用场景

### 📚 电子书章节拆分
```python
def split_ebook(pdf_path, chapters):
    """按章节拆分电子书"""
    doc = fitz.open(pdf_path)

    for chapter_name, (start, end) in chapters.items():
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        new_doc.save(f"{chapter_name}.pdf")
        new_doc.close()

    doc.close()

# 使用
chapters = {
    "第1章_基础": (0, 15),
    "第2章_进阶": (16, 30),
    "第3章_高级": (31, 50)
}
split_ebook("ebook.pdf", chapters)
```

### 📄 合同按日期归档
```python
import os
from datetime import datetime

def merge_by_date(pdf_dir, output_dir):
    """按日期归档合并PDF"""
    # 按修改日期分组
    files_by_date = {}

    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            filepath = os.path.join(pdf_dir, filename)
            mtime = os.path.getmtime(filepath)
            date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

            if date not in files_by_date:
                files_by_date[date] = []
            files_by_date[date].append(filepath)

    # 按日期合并
    for date, files in files_by_date.items():
        result = fitz.open()
        for filepath in files:
            doc = fitz.open(filepath)
            result.insert_pdf(doc)
            doc.close()

        output_path = os.path.join(output_dir, f"{date}.pdf")
        result.save(output_path)
        result.close()
```

---

## 注意事项

⚠️ **内存管理** - 合并大量PDF时注意内存使用
⚠️ **页码索引** - 页码从0开始（第1页是0）
⚠� **文件关闭** - 及时关闭不需要的文档
⚠️ **性能优化** - 大文件使用`show_progress`参数

---

## 下一步

- [安全加密功能](security.md) - 学习PDF加密解密
- [PDF生成功能](generation.md) - 学习创建PDF
- [完整示例](examples.md) - 查看更多实用代码
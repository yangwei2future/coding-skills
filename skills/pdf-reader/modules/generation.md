# PDF生成功能模块

从零创建PDF文档，支持多种内容格式

---

## 核心能力

✅ **空白PDF创建** - 创建新PDF并添加内容
✅ **图片转PDF** - 将图片转换为PDF文档
✅ **文本转PDF** - 将文本内容生成PDF
✅ **批量生成** - 自动化批量生成报告
✅ **格式化输出** - 支持标题、段落、表格等格式

---

## 从零创建PDF

### 1. 创建空白PDF

```python
import fitz

# 创建空白文档
doc = fitz.open()

# 添加新页面
page = doc.new_page()

# 保存
doc.save("blank.pdf")
doc.close()
```

### 2. 创建带内容的PDF

```python
import fitz

doc = fitz.open()
page = doc.new_page()

# 添加标题
page.insert_text(
    fitz.Point(100, 100),
    "Hello World",
    fontsize=24,
    fontname="helv-b"
)

# 添加正文
text_rect = fitz.Rect(100, 150, 500, 600)
page.insert_textbox(
    text_rect,
    "这是一段正文内容。",
    fontsize=12
)

doc.save("content.pdf")
doc.close()
```

### 3. 创建多页PDF

```python
import fitz

doc = fitz.open()

# 创建多个页面
for i in range(5):
    page = doc.new_page()

    # 添加页码
    page.insert_text(
        fitz.Point(250, 750),
        f"Page {i + 1}",
        fontsize=10
    )

    # 添加内容
    page.insert_text(
        fitz.Point(100, 100),
        f"这是第 {i + 1} 页的内容",
        fontsize=16
    )

doc.save("multi_page.pdf")
doc.close()
```

---

## 图片转PDF

### 1. 单张图片转PDF

```python
import fitz

doc = fitz.open()
page = doc.new_page()

# 插入图片（全页）
img_rect = fitz.Rect(0, 0, 612, 792)  # US Letter尺寸
page.insert_image(img_rect, filename="image.jpg")

doc.save("image.pdf")
doc.close()
```

### 2. 多张图片转PDF

```python
import fitz

doc = fitz.open()

images = ["img1.jpg", "img2.jpg", "img3.png"]

for img in images:
    page = doc.new_page()
    img_rect = fitz.Rect(0, 0, 612, 792)
    page.insert_image(img_rect, filename=img)

doc.save("images_to_pdf.pdf")
doc.close()
```

### 3. 从内存图片创建

```python
import fitz

doc = fitz.open()
page = doc.new_page()

# 从文件读取图片数据
with open("image.png", "rb") as f:
    img_data = f.read()

# 插入图片（从内存）
img_rect = fitz.Rect(100, 100, 500, 500)
page.insert_image(img_rect, stream=img_data)

doc.save("memory_image.pdf")
doc.close()
```

---

## 文本转PDF

### 1. 简单文本转PDF

```python
import fitz

doc = fitz.open()
page = doc.new_page()

# 添加文本
text = """Hello World
这是第二行
这是第三行"""

page.insert_text(
    fitz.Point(100, 100),
    text
)

doc.save("text.pdf")
doc.close()
```

### 2. 文本框转PDF

```python
import fitz

doc = fitz.open()
page = doc.new_page()

# 定义文本框区域
text_rect = fitz.Rect(50, 50, 550, 750)

# 添加多行文本
content = """
这是第一段文字。
这是第二段文字。
这是第三段文字。
"""

page.insert_textbox(
    text_rect,
    content,
    fontsize=12,
    fontname="helv",
    color=(0, 0, 0)
)

doc.save("textbox.pdf")
doc.close()
```

### 3. 格式化文本PDF

```python
import fitz

def create_formatted_pdf(title, paragraphs):
    """创建格式化PDF"""
    doc = fitz.open()
    page = doc.new_page()

    # 添加标题
    page.insert_text(
        fitz.Point(100, 100),
        title,
        fontsize=24,
        fontname="helv-b",
        color=(0, 0, 0.8)  # 蓝色标题
    )

    # 添加段落
    y = 150
    for paragraph in paragraphs:
        text_rect = fitz.Rect(100, y, 500, y + 100)
        page.insert_textbox(
            text_rect,
            paragraph,
            fontsize=11,
            align=fitz.TEXT_ALIGN_LEFT
        )
        y += 120

    doc.save("formatted.pdf")
    doc.close()

# 使用
create_formatted_pdf(
    "文档标题",
    ["第一段内容", "第二段内容", "第三段内容"]
)
```

---

## 表格生成

### 1. 简单表格

```python
import fitz

doc = fitz.open()
page = doc.new_page()

# 定义表格数据
table_data = [
    ["姓名", "年龄", "城市"],
    ["张三", "25", "北京"],
    ["李四", "30", "上海"],
    ["王五", "28", "广州"]
]

# 绘制表格
start_y = 100
row_height = 30
col_widths = [150, 100, 150]

for row_idx, row in enumerate(table_data):
    x = 100
    y = start_y + row_idx * row_height

    for col_idx, cell in enumerate(row):
        # 绘制单元格边框
        cell_rect = fitz.Rect(
            x, y,
            x + col_widths[col_idx], y + row_height
        )

        shape = page.new_shape()
        shape.draw_rect(cell_rect)
        shape.finish(color=(0, 0, 0), width=1)

        # 插入文本
        page.insert_text(
            fitz.Point(x + 10, y + 20),
            cell,
            fontsize=12
        )

        x += col_widths[col_idx]

doc.save("table.pdf")
doc.close()
```

---

## 批量生成

### 1. 批量生成报告

```python
import fitz
from datetime import datetime

def generate_report_batch(data_list, output_dir):
    """批量生成报告PDF"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    for i, data in enumerate(data_list):
        doc = fitz.open()
        page = doc.new_page()

        # 标题
        page.insert_text(
            fitz.Point(100, 100),
            data["title"],
            fontsize=24,
            fontname="helv-b"
        )

        # 日期
        date = datetime.now().strftime("%Y-%m-%d")
        page.insert_text(
            fitz.Point(100, 150),
            f"生成日期: {date}",
            fontsize=12
        )

        # 内容
        content_rect = fitz.Rect(100, 200, 500, 750)
        page.insert_textbox(content_rect, data["content"], fontsize=11)

        # 保存
        output_path = os.path.join(output_dir, f"report_{i+1}.pdf")
        doc.save(output_path)
        doc.close()

        print(f"✓ 生成: report_{i+1}.pdf")

# 使用
data_list = [
    {"title": "报告1", "content": "内容1"},
    {"title": "报告2", "content": "内容2"},
    {"title": "报告3", "content": "内容3"}
]
generate_report_batch(data_list, "./reports")
```

### 2. 自动化PDF生成工具

```python
import fitz

class PDFGenerator:
    """PDF生成工具类"""

    def __init__(self):
        self.doc = None

    def create_document(self):
        """创建新文档"""
        self.doc = fitz.open()

    def add_title_page(self, title, subtitle=None):
        """添加标题页"""
        page = self.doc.new_page()

        # 主标题
        page.insert_text(
            fitz.Point(200, 400),
            title,
            fontsize=36,
            fontname="helv-b",
            color=(0, 0, 0.8)
        )

        # 副标题
        if subtitle:
            page.insert_text(
                fitz.Point(200, 450),
                subtitle,
                fontsize=18
            )

    def add_content_page(self, content):
        """添加内容页"""
        page = self.doc.new_page()

        text_rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(text_rect, content, fontsize=12)

    def save(self, filename):
        """保存文档"""
        self.doc.save(filename)
        self.doc.close()

# 使用
generator = PDFGenerator()
generator.create_document()
generator.add_title_page("年度报告", "2024年度")
generator.add_content_page("这是报告内容...")
generator.save("annual_report.pdf")
```

---

## 实用场景

### 📄 生成简历PDF

```python
import fitz

def generate_resume(name, info):
    """生成简历PDF"""
    doc = fitz.open()
    page = doc.new_page()

    # 姓名
    page.insert_text(
        fitz.Point(250, 100),
        name,
        fontsize=28,
        fontname="helv-b"
    )

    # 个人信息
    y = 150
    for key, value in info.items():
        page.insert_text(
            fitz.Point(100, y),
            f"{key}: {value}",
            fontsize=12
        )
        y += 25

    doc.save("resume.pdf")
    doc.close()

# 使用
generate_resume(
    "杨卫",
    {
        "电话": "17695965214",
        "邮箱": "ywei_20@126.com",
        "微信": "yangw_0122"
    }
)
```

### 📋 生成合同PDF

```python
import fitz
from datetime import datetime

def generate_contract(contract_data):
    """生成合同PDF"""
    doc = fitz.open()
    page = doc.new_page()

    # 标题
    page.insert_text(
        fitz.Point(200, 100),
        "合同",
        fontsize=28,
        fontname="helv-b"
    )

    # 合同编号
    page.insert_text(
        fitz.Point(100, 150),
        f"合同编号: {contract_data['contract_id']}",
        fontsize=12
    )

    # 日期
    today = datetime.now().strftime("%Y年%m月%d日")
    page.insert_text(
        fitz.Point(100, 180),
        f"签订日期: {today}",
        fontsize=12
    )

    # 内容
    content_rect = fitz.Rect(100, 220, 500, 700)
    page.insert_textbox(
        content_rect,
        contract_data['content'],
        fontsize=11
    )

    # 签名位置
    page.insert_text(
        fitz.Point(100, 750),
        "甲方签字: ________________",
        fontsize=12
    )

    page.insert_text(
        fitz.Point(350, 750),
        "乙方签字: ________________",
        fontsize=12
    )

    doc.save("contract.pdf")
    doc.close()
```

---

## 注意事项

⚠️ **页面尺寸** - 默认使用A4尺寸，可自定义
⚠️ **字体支持** - PyMuPDF支持有限字体
⚠️ **坐标系** - PDF坐标从左下角开始，y轴向上
⚠️ **内存管理** - 生成完成后记得关闭文档

---

## 下一步

- [完整示例](examples.md) - 查看更多实用代码
- [编辑功能](editing.md) - 学习如何编辑PDF
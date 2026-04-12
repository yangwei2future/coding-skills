# PDF编辑功能模块

灵活编辑PDF内容，支持文本、图片、水印、注释等操作

---

## 核心能力

✅ **文本编辑** - 添加、修改、删除PDF文本
✅ **图片操作** - 插入、替换、删除图片
✅ **水印添加** - 文本水印、图片水印
✅ **注释标注** - 高亮、批注、下划线、删除线
✅ **页面管理** - 添加、删除、旋转、裁剪页面

---

## 文本编辑

### 1. 添加文本

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 插入文本（基础）
page.insert_text(
    fitz.Point(100, 100),  # 坐标位置
    "Hello World",
    fontsize=14,
    fontname="helv"
)

# 插入文本（高级）
page.insert_text(
    fitz.Point(100, 150),
    "高级文本",
    fontsize=16,
    fontname="helv-b",  # 粗体
    color=(0, 0, 1)  # RGB: 蓝色
)

doc.save("edited.pdf")
doc.close()
```

### 2. 插入多行文本

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

text = """
这是第一行文本
这是第二行文本
这是第三行文本
"""

# 定义文本框区域
text_rect = fitz.Rect(100, 100, 500, 500)

# 插入文本框
page.insert_textbox(
    text_rect,
    text,
    fontsize=12,
    fontname="helv",
    color=(0, 0, 0)  # 黑色
)

doc.save("textbox.pdf")
doc.close()
```

### 3. 修改现有文本

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 搜索要修改的文本
areas = page.search_for("旧文本")

for area in areas:
    # 创建红色矩形覆盖旧文本
    shape = page.new_shape()
    shape.draw_rect(area)
    shape.finish(color=(1, 0, 0), fill=(1, 0, 0))  # 红色填充

    # 在相同位置插入新文本
    page.insert_text(
        fitz.Point(area.x0, area.y0),
        "新文本",
        fontsize=12,
        color=(0, 0, 0)
    )

doc.save("modified.pdf")
doc.close()
```

---

## 图片操作

### 1. 插入图片

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 定义图片区域
img_rect = fitz.Rect(100, 100, 300, 300)

# 插入图片
page.insert_image(img_rect, filename="image.png")

doc.save("with_image.pdf")
doc.close()
```

### 2. 从内存插入图片

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 读取图片到内存
with open("image.png", "rb") as f:
    img_data = f.read()

# 插入图片（从内存）
img_rect = fitz.Rect(100, 100, 300, 300)
page.insert_image(img_rect, stream=img_data)

doc.save("image_from_memory.pdf")
doc.close()
```

### 3. 替换现有图片

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 获取页面中的图片列表
images = page.get_images()

if images:
    # 删除第一个图片
    xref = images[0][0]
    page.delete_image(xref)

    # 插入新图片到相同位置
    img_rect = fitz.Rect(100, 100, 300, 300)
    page.insert_image(img_rect, filename="new_image.png")

doc.save("replaced_image.pdf")
doc.close()
```

---

## 水印添加

### 1. 文本水印

```python
import fitz

doc = fitz.open("file.pdf")

for page in doc:
    # 添加斜向水印
    text = "CONFIDENTIAL"
    page.insert_text(
        fitz.Point(200, 400),
        text,
        fontsize=60,
        color=(0.8, 0.8, 0.8),  # 灰色
        rotate=45  # 旋转45度
    )

doc.save("watermarked.pdf")
doc.close()
```

### 2. 多层水印

```python
import fitz

doc = fitz.open("file.pdf")

for page in doc:
    # 添加多个水印（覆盖整个页面）
    for x in range(50, 550, 150):
        for y in range(50, 750, 150):
            page.insert_text(
                fitz.Point(x, y),
                "机密",
                fontsize=30,
                color=(0.9, 0.9, 0.9),  # 浅灰色
                rotate=45
            )

doc.save("multi_watermark.pdf")
doc.close()
```

### 3. 图片水印

```python
import fitz

doc = fitz.open("file.pdf")

for page in doc:
    # 添加图片水印
    img_rect = fitz.Rect(150, 300, 450, 500)
    page.insert_image(
        img_rect,
        filename="watermark_logo.png",
        overlay=True  # 覆盖模式
    )

doc.save("logo_watermark.pdf")
doc.close()
```

---

## 注释标注

### 1. 文本高亮

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 搜索要高亮的文本
areas = page.search_for("important")

for area in areas:
    # 添加黄色高亮
    highlight = page.add_highlight_annot(area)
    highlight.set_colors(stroke=(1, 1, 0))  # RGB: 黄色
    highlight.update()

doc.save("highlighted.pdf")
doc.close()
```

### 2. 添加批注

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 添加文本批注
point = fitz.Point(100, 100)
annot = page.add_text_annot(point, "这是一个批注")
annot.set_colors(stroke=(1, 0, 0))  # 红色
annot.update()

# 添加弹出式批注
popup_rect = fitz.Rect(200, 200, 400, 300)
popup = page.add_popup_annot(popup_rect, "弹出式批注内容")

doc.save("annotated.pdf")
doc.close()
```

### 3. 下划线和删除线

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

areas = page.search_for("text")

for area in areas:
    # 下划线
    underline = page.add_underline_annot(area)
    underline.set_colors(stroke=(0, 0, 1))  # 蓝色
    underline.update()

    # 删除线（在另一个位置演示）
    strike = page.add_strikeout_annot(area)
    strike.set_colors(stroke=(1, 0, 0))  # 红色
    strike.update()

doc.save("underline_strike.pdf")
doc.close()
```

### 4. 添加形状标注

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 添加矩形标注
rect = fitz.Rect(100, 100, 300, 300)
rect_annot = page.add_rect_annot(rect)

# 添加圆形标注
circle_rect = fitz.Rect(350, 100, 450, 200)
circle = page.add_circle_annot(circle_rect)

# 添加线条标注
line = page.add_line_annot(
    fitz.Point(100, 400),
    fitz.Point(300, 400)
)

doc.save("shape_annot.pdf")
doc.close()
```

---

## 页面管理

### 1. 删除页面

```python
import fitz

doc = fitz.open("file.pdf")

# 删除第一页
doc.delete_page(0)

# 删除多页
doc.delete_pages([1, 3, 5])  # 删除第2、4、6页

# 删除页面范围
doc.delete_pages(from_page=2, to_page=5)  # 删除第3到6页

doc.save("deleted_pages.pdf")
doc.close()
```

### 2. 旋转页面

```python
import fitz

doc = fitz.open("file.pdf")

# 旋转第一页90度
page = doc[0]
page.set_rotation(90)  # 可选: 0, 90, 180, 270

# 旋转所有页面
for page in doc:
    page.set_rotation(180)

doc.save("rotated.pdf")
doc.close()
```

### 3. 裁剪页面

```python
import fitz

doc = fitz.open("file.pdf")
page = doc[0]

# 设置裁剪框（CropBox）
crop_rect = fitz.Rect(50, 50, 500, 700)
page.set_cropbox(crop_rect)

doc.save("cropped.pdf")
doc.close()
```

### 4. 添加新页面

```python
import fitz

# 在现有PDF中添加新页面
doc = fitz.open("file.pdf")

# 在末尾添加空白页
new_page = doc.new_page(-1)  # -1表示最后一页之后

# 在第3页位置插入新页
inserted_page = doc.new_page(2)  # 在索引2位置插入

doc.save("added_pages.pdf")
doc.close()
```

---

## 批量编辑

### 批量添加页眉页脚

```python
import fitz

def add_header_footer(pdf_path, header_text, footer_text):
    """批量添加页眉页脚"""
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc):
        # 页眉（顶部）
        page.insert_text(
            fitz.Point(50, 30),
            header_text,
            fontsize=10,
            color=(0, 0, 0)
        )

        # 页脚（底部）
        page.insert_text(
            fitz.Point(50, 750),
            f"{footer_text} - 第 {page_num + 1} 页",
            fontsize=10,
            color=(0, 0, 0)
        )

    doc.save("header_footer_added.pdf")
    doc.close()

# 使用
add_header_footer("document.pdf", "公司文档", "内部资料")
```

### 批量替换文本

```python
import fitz

def batch_replace_text(pdf_path, old_text, new_text):
    """批量替换PDF中的文本"""
    doc = fitz.open(pdf_path)

    for page in doc:
        areas = page.search_for(old_text)

        for area in areas:
            # 覆盖旧文本
            shape = page.new_shape()
            shape.draw_rect(area)
            shape.finish(fill=(1, 1, 1))  # 白色填充

            # 插入新文本
            page.insert_text(
                fitz.Point(area.x0, area.y0),
                new_text,
                fontsize=12
            )

    doc.save("text_replaced.pdf")
    doc.close()

# 使用
batch_replace_text("contract.pdf", "2023年", "2024年")
```

---

## 实用场景

### 📄 简历处理
```python
def process_resume(original_pdf):
    """简历处理：添加水印和页码"""
    doc = fitz.open(original_pdf)

    for page_num, page in enumerate(doc):
        # 添加水印
        page.insert_text(
            fitz.Point(200, 400),
            "个人简历",
            fontsize=40,
            color=(0.9, 0.9, 0.9),
            rotate=45
        )

        # 添加页码
        page.insert_text(
            fitz.Point(250, 750),
            f"Page {page_num + 1}",
            fontsize=10
        )

    doc.save("processed_resume.pdf")
```

### 📑 合同标注
```python
def annotate_contract(pdf_path, key_terms):
    """标注合同关键条款"""
    doc = fitz.open(pdf_path)

    for page in doc:
        for term in key_terms:
            areas = page.search_for(term)

            for area in areas:
                # 高亮关键条款
                highlight = page.add_highlight_annot(area)
                highlight.set_colors(stroke=(1, 1, 0))
                highlight.update()

    doc.save("annotated_contract.pdf")
```

---

## 注意事项

⚠️ **字体支持** - PyMuPDF支持有限字体，中文推荐使用"china-s"
⚠️ **坐标系统** - PDF坐标从左下角开始，y轴向上
⚠️ **覆盖模式** - insert_text默认不覆盖，需要手动处理
⚠️ **内存管理** - 编辑完成后立即保存并关闭

---

## 下一步

- [合并拆分功能](merging.md) - 学习PDF合并拆分
- [安全加密功能](security.md) - 学习PDF加密解密
- [完整示例](examples.md) - 查看更多实用代码
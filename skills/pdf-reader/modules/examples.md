# PDF完整示例模块

封装的工具类和批量处理脚本

---

## 工具类封装

### 1. PDFTool - 全能PDF工具类

```python
#!/usr/bin/env python3
"""
PDF处理工具集 - 基于PyMuPDF
支持：读取、编辑、合并、拆分、加密、生成
"""
import fitz
import os
import re
from datetime import datetime

class PDFTool:
    """PDF全能工具类"""

    def __init__(self, pdf_path=None):
        """初始化"""
        self.doc = None
        if pdf_path:
            self.open(pdf_path)

    # ==================== 文档管理 ====================

    def open(self, pdf_path):
        """打开PDF文档"""
        try:
            self.doc = fitz.open(pdf_path)
            return True
        except Exception as e:
            print(f"错误: 无法打开文件 {pdf_path}: {e}")
            return False

    def close(self):
        """关闭文档"""
        if self.doc:
            self.doc.close()
            self.doc = None

    def get_info(self):
        """获取文档信息"""
        if not self.doc:
            return None

        return {
            "pages": len(self.doc),
            "metadata": self.doc.metadata,
            "is_encrypted": self.doc.is_encrypted
        }

    # ==================== 读取功能 ====================

    def extract_text(self, page_num=None):
        """提取文本"""
        if not self.doc:
            return None

        if page_num is not None:
            return self.doc[page_num].get_text()

        return [page.get_text() for page in self.doc]

    def extract_images(self, output_dir="images"):
        """提取所有图片"""
        if not self.doc:
            return

        os.makedirs(output_dir, exist_ok=True)

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            images = page.get_images()

            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(self.doc, xref)

                if pix.n < 5:
                    pix.save(f"{output_dir}/page{page_num+1}_img{img_index+1}.png")
                else:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    pix.save(f"{output_dir}/page{page_num+1}_img{img_index+1}.png")

                pix = None

    def search_text(self, text):
        """搜索文本位置"""
        if not self.doc:
            return []

        results = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            areas = page.search_for(text)

            for area in areas:
                results.append({
                    "page": page_num + 1,
                    "position": area
                })

        return results

    # ==================== 编辑功能 ====================

    def add_watermark(self, text, output_path, fontsize=60, color=(0.8, 0.8, 0.8)):
        """添加水印"""
        if not self.doc:
            return False

        for page in self.doc:
            page.insert_text(
                fitz.Point(200, 400),
                text,
                fontsize=fontsize,
                color=color,
                rotate=45
            )

        self.doc.save(output_path)
        return True

    def add_page_numbers(self, output_path, start=1):
        """添加页码"""
        if not self.doc:
            return False

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page.insert_text(
                fitz.Point(250, 750),
                f"Page {page_num + start}",
                fontsize=10
            )

        self.doc.save(output_path)
        return True

    def highlight_text(self, search_text, output_path, color=(1, 1, 0)):
        """高亮文本"""
        if not self.doc:
            return False

        for page in self.doc:
            areas = page.search_for(search_text)

            for area in areas:
                highlight = page.add_highlight_annot(area)
                highlight.set_colors(stroke=color)
                highlight.update()

        self.doc.save(output_path)
        return True

    # ==================== 合并拆分 ====================

    def split(self, output_dir):
        """拆分为单页PDF"""
        if not self.doc:
            return False

        os.makedirs(output_dir, exist_ok=True)

        for i in range(len(self.doc)):
            new_doc = fitz.open()
            new_doc.insert_pdf(self.doc, from_page=i, to_page=i)
            new_doc.save(f"{output_dir}/page_{i+1}.pdf")
            new_doc.close()

        return True

    def extract_pages(self, start, end, output_path):
        """提取特定页面范围"""
        if not self.doc:
            return False

        new_doc = fitz.open()
        new_doc.insert_pdf(self.doc, from_page=start, to_page=end)
        new_doc.save(output_path)
        new_doc.close()

        return True

    @staticmethod
    def merge(pdf_files, output_path):
        """合并多个PDF"""
        result = fitz.open()

        for pdf_file in pdf_files:
            doc = fitz.open(pdf_file)
            result.insert_pdf(doc)
            doc.close()

        result.save(output_path)
        result.close()

        return True

    # ==================== 加密解密 ====================

    def encrypt(self, output_path, owner_pw, user_pw, permissions=None):
        """加密PDF"""
        if not self.doc:
            return False

        if permissions is None:
            permissions = int(
                fitz.PDF_PERM_ACCESSIBILITY |
                fitz.PDF_PERM_PRINT
            )

        self.doc.save(
            output_path,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=owner_pw,
            user_pw=user_pw,
            permissions=permissions
        )

        return True

    def decrypt(self, password, output_path):
        """解密PDF"""
        if not self.doc:
            return False

        if self.doc.is_encrypted:
            if self.doc.authenticate(password):
                self.doc.save(output_path)
                return True
            else:
                print("密码错误")
                return False

        return True

    # ==================== 生成功能 ====================

    @staticmethod
    def create_blank(output_path, pages=1):
        """创建空白PDF"""
        doc = fitz.open()

        for i in range(pages):
            doc.new_page()

        doc.save(output_path)
        doc.close()

        return True

    @staticmethod
    def create_from_images(images, output_path):
        """从图片创建PDF"""
        doc = fitz.open()

        for img in images:
            page = doc.new_page()
            img_rect = fitz.Rect(0, 0, 612, 792)
            page.insert_image(img_rect, filename=img)

        doc.save(output_path)
        doc.close()

        return True

    @staticmethod
    def create_from_text(text, title, output_path):
        """从文本创建PDF"""
        doc = fitz.open()
        page = doc.new_page()

        # 标题
        page.insert_text(
            fitz.Point(100, 100),
            title,
            fontsize=24,
            fontname="helv-b"
        )

        # 内容
        text_rect = fitz.Rect(100, 150, 500, 750)
        page.insert_textbox(text_rect, text, fontsize=12)

        doc.save(output_path)
        doc.close()

        return True


# 使用示例
if __name__ == "__main__":
    # 打开PDF
    tool = PDFTool("example.pdf")

    # 提取文本
    text = tool.extract_text()
    print(text)

    # 添加水印
    tool.add_watermark("CONFIDENTIAL", "watermarked.pdf")

    # 拆分PDF
    tool.split("./pages")

    # 关闭
    tool.close()

    # 合并PDF
    PDFTool.merge(["a.pdf", "b.pdf"], "merged.pdf")
```

---

## 批量处理脚本

### 1. 批量添加水印

```python
#!/usr/bin/env python3
"""
批量PDF水印添加工具
"""
import fitz
import os

def add_watermark_batch(pdf_dir, watermark_text, output_dir, fontsize=60):
    """批量为PDF添加水印"""
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            doc = fitz.open(pdf_path)

            for page in doc:
                page.insert_text(
                    fitz.Point(200, 400),
                    watermark_text,
                    fontsize=fontsize,
                    color=(0.8, 0.8, 0.8),
                    rotate=45
                )

            output_path = os.path.join(output_dir, f"watermarked_{filename}")
            doc.save(output_path)
            doc.close()

            print(f"✓ 处理完成: {filename}")

if __name__ == "__main__":
    add_watermark_batch("./pdfs", "CONFIDENTIAL", "./output")
```

### 2. 批量提取文本

```python
#!/usr/bin/env python3
"""
批量PDF文本提取工具
"""
import fitz
import os

def extract_text_batch(pdf_dir, output_file):
    """批量提取PDF文本到单个文件"""
    with open(output_file, "w", encoding="utf-8") as f:
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(pdf_dir, filename)
                doc = fitz.open(pdf_path)

                f.write(f"\n{'='*80}\n")
                f.write(f"文件: {filename}\n")
                f.write(f"{'='*80}\n\n")

                for page in doc:
                    f.write(page.get_text())

                doc.close()
                print(f"✓ 提取完成: {filename}")

if __name__ == "__main__":
    extract_text_batch("./pdfs", "all_texts.txt")
```

### 3. 批量PDF合并

```python
#!/usr/bin/env python3
"""
批量PDF合并工具
"""
import fitz
import os

def batch_merge(pdf_dir, output_file):
    """合并文件夹中所有PDF"""
    result = fitz.open()

    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    pdf_files.sort()

    for filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, filename)
        doc = fitz.open(pdf_path)
        result.insert_pdf(doc)
        doc.close()
        print(f"✓ 合并: {filename}")

    result.save(output_file)
    result.close()
    print(f"\n合并完成: {output_file}")

if __name__ == "__main__":
    batch_merge("./pdfs", "merged.pdf")
```

### 4. 批量加密

```python
#!/usr/bin/env python3
"""
批量PDF加密工具
"""
import fitz
import os

def batch_encrypt(pdf_dir, owner_pw, user_pw, output_dir):
    """批量加密PDF"""
    os.makedirs(output_dir, exist_ok=True)

    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY |
        fitz.PDF_PERM_PRINT
    )

    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            doc = fitz.open(pdf_path)

            output_path = os.path.join(output_dir, filename)
            doc.save(
                output_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw=owner_pw,
                user_pw=user_pw,
                permissions=perm
            )

            doc.close()
            print(f"✓ 加密: {filename}")

if __name__ == "__main__":
    batch_encrypt("./pdfs", "admin123", "viewer123", "./encrypted")
```

---

## 实用场景示例

### 📄 简历批量处理

```python
#!/usr/bin/env python3
"""
简历批量处理工具
"""
import fitz
import os
import re

class ResumeProcessor:
    """简历处理器"""

    def __init__(self):
        self.tool = PDFTool()

    def extract_resume_info(self, pdf_path):
        """提取简历关键信息"""
        self.tool.open(pdf_path)
        text = self.tool.extract_text()
        self.tool.close()

        if not text:
            return None

        # 合并所有页面文本
        full_text = "\n".join(text)

        # 提取关键信息
        info = {
            "email": re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', full_text),
            "phone": re.search(r'\b\d{11}\b', full_text),
            "name": re.search(r'姓名[：:]\s*(\S+)', full_text),
            "education": re.search(r'教育经历', full_text, re.IGNORECASE),
            "experience": re.search(r'工作经历', full_text, re.IGNORECASE)
        }

        # 提取匹配结果
        result = {}
        for key, match in info.items():
            if match:
                result[key] = match.group() if hasattr(match, 'group') else "存在"

        return result

    def add_watermark_to_resume(self, pdf_path, output_path):
        """为简历添加机密水印"""
        self.tool.open(pdf_path)
        self.tool.add_watermark("机密简历", output_path, fontsize=40)
        self.tool.close()

    def batch_process(self, resume_dir, output_dir):
        """批量处理简历"""
        os.makedirs(output_dir, exist_ok=True)

        results = []

        for filename in os.listdir(resume_dir):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(resume_dir, filename)

                # 提取信息
                info = self.extract_resume_info(pdf_path)
                if info:
                    results.append({
                        "filename": filename,
                        "info": info
                    })

                # 添加水印
                output_path = os.path.join(output_dir, filename)
                self.add_watermark_to_resume(pdf_path, output_path)

        return results

# 使用
processor = ResumeProcessor()
results = processor.batch_process("./resumes", "./processed_resumes")

for result in results:
    print(f"\n文件: {result['filename']}")
    print(f"信息: {result['info']}")
```

### 📋 报告自动生成

```python
#!/usr/bin/env python3
"""
报告自动生成工具
"""
import fitz
from datetime import datetime

class ReportGenerator:
    """报告生成器"""

    def generate_report(self, title, content, output_path):
        """生成格式化报告"""
        doc = fitz.open()
        page = doc.new_page()

        # 标题
        page.insert_text(
            fitz.Point(200, 100),
            title,
            fontsize=24,
            fontname="helv-b",
            color=(0, 0, 0.8)
        )

        # 日期
        date = datetime.now().strftime("%Y年%m月%d日")
        page.insert_text(
            fitz.Point(100, 150),
            f"生成日期: {date}",
            fontsize=12
        )

        # 内容
        content_rect = fitz.Rect(100, 200, 500, 700)
        page.insert_textbox(content_rect, content, fontsize=11)

        # 页脚
        page.insert_text(
            fitz.Point(250, 750),
            "第 1 页",
            fontsize=10
        )

        doc.save(output_path)
        doc.close()

        return True

    def batch_generate(self, data_list, output_dir):
        """批量生成报告"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        for i, data in enumerate(data_list):
            output_path = os.path.join(output_dir, f"report_{i+1}.pdf")
            self.generate_report(
                data["title"],
                data["content"],
                output_path
            )
            print(f"✓ 生成: report_{i+1}.pdf")

# 使用
generator = ReportGenerator()
data_list = [
    {"title": "月度报告", "content": "本月业绩..."},
    {"title": "季度报告", "content": "本季度总结..."}
]
generator.batch_generate(data_list, "./reports")
```

---

## 命令行工具

### PDF处理CLI

```python
#!/usr/bin/env python3
"""
PDF处理命令行工具
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="PDF处理工具")
    parser.add_argument("input", help="输入PDF文件")
    parser.add_argument("--output", help="输出文件")
    parser.add_argument("--action", choices=[
        "extract", "watermark", "split", "merge", "encrypt"
    ], help="操作类型")
    parser.add_argument("--text", help="水印文本或搜索文本")
    parser.add_argument("--password", help="加密密码")

    args = parser.parse_args()

    tool = PDFTool(args.input)

    if args.action == "extract":
        text = tool.extract_text()
        print(text)

    elif args.action == "watermark":
        tool.add_watermark(args.text, args.output)

    elif args.action == "split":
        tool.split(args.output)

    elif args.action == "encrypt":
        tool.encrypt(args.output, args.password, args.password)

    tool.close()

if __name__ == "__main__":
    main()
```

---

## 使用方式

### 命令行使用
```bash
# 提取文本
python pdf_tool.py input.pdf --action extract

# 添加水印
python pdf_tool.py input.pdf --action watermark --output output.pdf --text "CONFIDENTIAL"

# 拆分PDF
python pdf_tool.py input.pdf --action split --output ./pages

# 加密PDF
python pdf_tool.py input.pdf --action encrypt --output encrypted.pdf --password "secret123"
```

---

## 注意事项

⚠️ **异常处理** - 所有操作都包含异常捕获
⚠️ **资源释放** - 使用完毕后立即关闭文档
⚠️ **路径检查** - 自动创建输出目录
⚠️ **进度提示** - 批量操作显示处理进度

---

## 相关文档

- [读取功能](reading.md)
- [编辑功能](editing.md)
- [合并拆分](merging.md)
- [安全加密](security.md)
- [PDF生成](generation.md)
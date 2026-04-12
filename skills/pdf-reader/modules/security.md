# PDF安全加密模块

PDF文档的加密、解密和权限控制

---

## 核心能力

✅ **AES-256加密** - 军用级加密标准
✅ **双密码系统** - 用户密码+所有者密码
✅ **权限控制** - 打印、复制、修改等权限设置
✅ **解密验证** - 密码验证和访问控制
✅ **批量加密** - 自动化批量处理

---

## 加密功能

### 1. 基础加密

```python
import fitz

doc = fitz.open("document.pdf")

# 设置用户密码和所有者密码
owner_pw = "owner123"  # 所有者密码（完全权限）
user_pw = "user123"    # 用户密码（受限权限）

doc.save(
    "encrypted.pdf",
    encryption=fitz.PDF_ENCRYPT_AES_256,  # AES-256加密
    owner_pw=owner_pw,
    user_pw=user_pw
)

doc.close()
```

### 2. 权限控制加密

```python
import fitz

doc = fitz.open("document.pdf")

# 定义权限
perm = int(
    fitz.PDF_PERM_ACCESSIBILITY |  # 允许辅助功能
    fitz.PDF_PERM_PRINT |           # 允许打印
    fitz.PDF_PERM_COPY              # 允许复制
    # 不包括：
    # - PDF_PERM_MODIFY    # 禁止修改
    # - PDF_PERM_ANNOTATE  # 禁止注释
    # - PDF_PERM_FORM      # 禁止填写表单
    # - PDF_PERM_EXTRACT   # 禁止提取
    # - PDF_PERM_ASSEMBLE  # 禁止组装
)

owner_pw = "admin123"
user_pw = "viewer123"

doc.save(
    "restricted.pdf",
    encryption=fitz.PDF_ENCRYPT_AES_256,
    owner_pw=owner_pw,
    user_pw=user_pw,
    permissions=perm
)

doc.close()
```

### 3. 加密方法对比

```python
import fitz

doc = fitz.open("document.pdf")

# 方法1: AES-256（推荐）
doc.save(
    "aes256.pdf",
    encryption=fitz.PDF_ENCRYPT_AES_256,
    owner_pw="owner",
    user_pw="user"
)

# 方法2: AES-128
doc.save(
    "aes128.pdf",
    encryption=fitz.PDF_ENCRYPT_AES_128,
    owner_pw="owner",
    user_pw="user"
)

# 方法3: RC4-128（旧标准，不推荐）
doc.save(
    "rc4.pdf",
    encryption=fitz.PDF_ENCRYPT_RC4_128,
    owner_pw="owner",
    user_pw="user"
)

doc.close()
```

### 4. 只读加密

```python
import fitz

doc = fitz.open("document.pdf")

# 只读权限（只允许查看）
perm = int(fitz.PDF_PERM_ACCESSIBILITY)  # 仅辅助功能

doc.save(
    "readonly.pdf",
    encryption=fitz.PDF_ENCRYPT_AES_256,
    owner_pw="admin",
    user_pw="viewer",
    permissions=perm
)

doc.close()
```

---

## 解密功能

### 1. 密码验证

```python
import fitz

doc = fitz.open("encrypted.pdf")

if doc.is_encrypted:
    print("PDF已加密")

    # 尝试用密码解密
    if doc.authenticate("user123"):
        print("密码正确，可以访问")
        # 现在可以读取内容
        text = doc[0].get_text()
        print(text)
    else:
        print("密码错误")
else:
    print("PDF未加密")

doc.close()
```

### 2. 自动解密

```python
import fitz

def decrypt_pdf(encrypted_pdf, password, output_pdf):
    """解密PDF并保存"""
    doc = fitz.open(encrypted_pdf)

    if doc.is_encrypted:
        if doc.authenticate(password):
            # 解密并保存
            doc.save(output_pdf)
            print(f"解密成功: {output_pdf}")
        else:
            print("密码错误，无法解密")
    else:
        print("文件未加密")

    doc.close()

# 使用
decrypt_pdf("encrypted.pdf", "user123", "decrypted.pdf")
```

### 3. 批量解密

```python
import fitz
import os

def batch_decrypt(directory, password, output_dir):
    """批量解密目录下的所有加密PDF"""
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            doc = fitz.open(filepath)

            if doc.is_encrypted:
                if doc.authenticate(password):
                    output_path = os.path.join(output_dir, filename)
                    doc.save(output_path)
                    print(f"✓ 解密: {filename}")
                else:
                    print(f"✗ 密码错误: {filename}")
            else:
                print(f"- 未加密: {filename}")

            doc.close()

# 使用
batch_decrypt("./encrypted_pdfs", "password123", "./decrypted_pdfs")
```

---

## 权限系统

### 1. 可用权限列表

```python
import fitz

# PDF权限常量
permissions = {
    "PDF_PERM_PRINT": fitz.PDF_PERM_PRINT,              # 打印
    "PDF_PERM_MODIFY": fitz.PDF_PERM_MODIFY,            # 修改
    "PDF_PERM_COPY": fitz.PDF_PERM_COPY,                # 复制
    "PDF_PERM_ANNOTATE": fitz.PDF_PERM_ANNOTATE,        # 注释
    "PDF_PERM_FORM": fitz.PDF_PERM_FORM,                # 填写表单
    "PDF_PERM_EXTRACT": fitz.PDF_PERM_EXTRACT,          # 提取
    "PDF_PERM_ASSEMBLE": fitz.PDF_PERM_ASSEMBLE,        # 组装
    "PDF_PERM_PRINT_HQ": fitz.PDF_PERM_PRINT_HQ,        # 高质量打印
    "PDF_PERM_ACCESSIBILITY": fitz.PDF_PERM_ACCESSIBILITY  # 辅助功能
}

for name, value in permissions.items():
    print(f"{name}: {value}")
```

### 2. 常用权限组合

```python
import fitz

# 场景1: 只读查看
readonly_perm = int(fitz.PDF_PERM_ACCESSIBILITY)

# 场景2: 允许打印和复制
view_copy_perm = int(
    fitz.PDF_PERM_ACCESSIBILITY |
    fitz.PDF_PERM_PRINT |
    fitz.PDF_PERM_COPY
)

# 场景3: 允许打印但禁止复制
print_only_perm = int(
    fitz.PDF_PERM_ACCESSIBILITY |
    fitz.PDF_PERM_PRINT
)

# 场景4: 允许填写表单
fill_form_perm = int(
    fitz.PDF_PERM_ACCESSIBILITY |
    fitz.PDF_PERM_PRINT |
    fitz.PDF_PERM_FORM
)

# 场景5: 完全权限（所有者密码）
full_perm = int(
    fitz.PDF_PERM_PRINT |
    fitz.PDF_PERM_MODIFY |
    fitz.PDF_PERM_COPY |
    fitz.PDF_PERM_ANNOTATE |
    fitz.PDF_PERM_FORM |
    fitz.PDF_PERM_EXTRACT |
    fitz.PDF_PERM_ASSEMBLE |
    fitz.PDF_PERM_PRINT_HQ |
    fitz.PDF_PERM_ACCESSIBILITY
)
```

### 3. 检查权限

```python
import fitz

def check_permissions(pdf_path, password=None):
    """检查PDF权限"""
    doc = fitz.open(pdf_path)

    if doc.is_encrypted:
        if not doc.authenticate(password):
            print("密码错误，无法检查权限")
            return

    # 获取权限
    perm = doc.permissions

    print("PDF权限:")
    print(f"打印: {bool(perm & fitz.PDF_PERM_PRINT)}")
    print(f"修改: {bool(perm & fitz.PDF_PERM_MODIFY)}")
    print(f"复制: {bool(perm & fitz.PDF_PERM_COPY)}")
    print(f"注释: {bool(perm & fitz.PDF_PERM_ANNOTATE)}")
    print(f"填写表单: {bool(perm & fitz.PDF_PERM_FORM)}")
    print(f"提取: {bool(perm & fitz.PDF_PERM_EXTRACT)}")

    doc.close()

# 使用
check_permissions("document.pdf", "user123")
```

---

## 实用场景

### 🔒 合同加密

```python
def encrypt_contract(contract_pdf, owner_password):
    """加密合同文档"""
    doc = fitz.open(contract_pdf)

    # 只允许查看和打印，禁止修改和复制
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY |
        fitz.PDF_PERM_PRINT
    )

    doc.save(
        "contract_encrypted.pdf",
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw=owner_password,
        user_pw="",  # 不需要用户密码
        permissions=perm
    )

    doc.close()
    print("合同加密完成")

# 使用
encrypt_contract("contract.pdf", "admin_secret_123")
```

### 📋 报告分级授权

```python
def create_tiered_access(pdf_path):
    """创建分级访问的PDF"""

    # 级别1: 完全访问（管理员）
    doc = fitz.open(pdf_path)
    doc.save(
        "report_admin.pdf",
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="admin_pass",
        user_pw="admin_pass",
        permissions=int(
            fitz.PDF_PERM_PRINT |
            fitz.PDF_PERM_MODIFY |
            fitz.PDF_PERM_COPY |
            fitz.PDF_PERM_ACCESSIBILITY
        )
    )

    # 级别2: 只读+打印（经理）
    doc = fitz.open(pdf_path)
    doc.save(
        "report_manager.pdf",
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="admin_pass",
        user_pw="manager_pass",
        permissions=int(
            fitz.PDF_PERM_PRINT |
            fitz.PDF_PERM_ACCESSIBILITY
        )
    )

    # 级别3: 仅查看（员工）
    doc = fitz.open(pdf_path)
    doc.save(
        "report_employee.pdf",
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="admin_pass",
        user_pw="employee_pass",
        permissions=int(fitz.PDF_PERM_ACCESSIBILITY)
    )

    doc.close()
    print("分级报告生成完成")

# 使用
create_tiered_access("report.pdf")
```

### 🔐 密码保护批处理

```python
import os

def batch_encrypt(directory, password):
    """批量加密PDF"""
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            doc = fitz.open(filepath)

            # 添加密码保护
            doc.save(
                filepath.replace('.pdf', '_encrypted.pdf'),
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw=password,
                user_pw=password
            )

            doc.close()
            print(f"✓ 加密: {filename}")

# 使用
batch_encrypt("./documents", "secure_password_123")
```

---

## 安全最佳实践

### 1. 强密码策略

```python
import re

def validate_password(password):
    """验证密码强度"""
    if len(password) < 12:
        return False, "密码长度至少12位"

    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含大写字母"

    if not re.search(r'[a-z]', password):
        return False, "密码必须包含小写字母"

    if not re.search(r'\d', password):
        return False, "密码必须包含数字"

    if not re.search(r'[!@#$%^&*]', password):
        return False, "密码必须包含特殊字符"

    return True, "密码强度符合要求"

# 使用
password = "MyStr0ng!Pass"
is_valid, message = validate_password(password)
print(message)
```

### 2. 密码管理

```python
import fitz
import hashlib
import base64

def generate_password(seed):
    """从种子生成密码"""
    hash_obj = hashlib.sha256(seed.encode())
    password = base64.b64encode(hash_obj.digest()).decode()[:16]
    return password

# 使用
password = generate_password("document_id_123_secret_key")
print(f"生成密码: {password}")
```

---

## 注意事项

⚠️ **密码强度** - 使用强密码（12位以上，包含大小写字母、数字、特殊字符）
⚠️ **密码管理** - 妥善保管密码，建议使用密码管理器
⚠️ **加密算法** - 推荐使用AES-256，避免使用RC4
⚠️ **权限设置** - 根据实际需求设置最小权限
⚠️ **备份** - 加密前务必备份原始文件

---

## 下一步

- [PDF生成功能](generation.md) - 学习创建PDF
- [完整示例](examples.md) - 查看更多实用代码
#!/usr/bin/env python3
"""
飞书文档上传脚本
将测试用例思维导图创建为新的飞书文档
使用内部飞书API上传文档内容
"""
import os
import sys
import json
import requests

API_BASE_URL = 'https://cfe-doc-backend.inner.chj.cloud'
AUTH_TOKEN = os.environ.get('FEISHU_TOKEN', '')


def create_feishu_document(title, content=None, parent_folder_id=None):
    """
    创建新的飞书文档

    Args:
        title: 文档标题
        content: 文档内容（支持Markdown格式）
        parent_folder_id: 父文件夹ID（可选，默认为根目录）

    Returns:
        dict: 包含文档信息的字典，或None表示失败
    """
    if not AUTH_TOKEN:
        print('Error: 未设置 FEISHU_TOKEN 环境变量，请先配置认证 token', file=sys.stderr)
        return None

    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'User-Agent': 'M3CE-Agent-Tool',
        'Content-Type': 'application/json'
    }

    # 构建请求体
    payload = {
        'title': title
    }

    if content:
        payload['content'] = content

    if parent_folder_id:
        payload['parent_folder_id'] = parent_folder_id

    try:
        # 调用创建文档API
        url = f'{API_BASE_URL}/openapi/v1/document/create'
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            print(f'Error: 创建文档失败, 状态码: {response.status_code}', file=sys.stderr)
            print(response.text, file=sys.stderr)
            return None

        result = response.json()

        if not result.get('success', False):
            print(f'Error: 创建文档失败 - {result.get("message", "未知错误")}', file=sys.stderr)
            return None

        doc_data = result.get('data', {})
        doc_id = doc_data.get('document_id') or doc_data.get('doc_id')
        doc_url = doc_data.get('url') or doc_data.get('document_url')

        return {
            'document_id': doc_id,
            'url': doc_url,
            'title': title
        }

    except Exception as e:
        print(f'Error: 创建文档异常 - {e}', file=sys.stderr)
        return None


def parse_xmind_to_markdown(xmind_json_file):
    """
    将xmind JSON文件转换为Markdown格式的思维导图

    Args:
        xmind_json_file: xmind JSON文件路径

    Returns:
        str: Markdown格式的内容
    """
    with open(xmind_json_file, 'r', encoding='utf-8') as f:
        xmind_data = json.load(f)

    root = xmind_data["sheets"][0]["topic"]
    lines = []

    # 添加标题
    lines.append(f"# {root['title']}")
    lines.append("")

    # 遍历子节点
    for child in root.get("children", []):
        if child["title"] == "测试用例统计":
            lines.append(f"## {child['title']}")
            for stat in child["children"]:
                lines.append(f"- {stat['title']}")
            lines.append("")
        else:
            lines.append(f"## {child['title']}")

            # 添加每个测试用例
            for tc in child.get("children", []):
                lines.append(f"### {tc['title']}")

                for detail in tc.get("children", []):
                    if detail["title"].startswith("优先级") or detail["title"].startswith("测试类型"):
                        lines.append(f"- {detail['title']}")
                    elif detail["title"] in ["前置条件", "测试步骤", "预期结果", "测试数据"]:
                        lines.append(f"- {detail['title']}:")
                        for item in detail.get("children", []):
                            if item.get("title"):
                                lines.append(f"  - {item['title']}")

                lines.append("")

    return "\n".join(lines)


def upload_xmind_to_feishu(xmind_file, title=None):
    """
    上传xmind到飞书

    Args:
        xmind_file: xmind Markdown文件或JSON文件路径
        title: 文档标题（可选，默认从文件名提取）

    Returns:
        dict: 包含文档信息的字典，或None表示失败
    """
    if not os.path.exists(xmind_file):
        print(f'Error: 文件不存在: {xmind_file}', file=sys.stderr)
        return None

    # 如果没有指定标题，从文件名提取
    if not title:
        file_name = os.path.basename(xmind_file)
        # 移除扩展名和_xmind后缀
        title = file_name.replace('.md', '').replace('_xmind', '')

    # 读取文件内容
    with open(xmind_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建飞书文档
    doc_info = create_feishu_document(title, content)

    if doc_info:
        print(f'✓ 文档上传成功')
        print(f'文档名称：{doc_info["title"]}')
        print(f'文档ID：{doc_info["document_id"]}')
        if doc_info.get("url"):
            print(f'文档链接：{doc_info["url"]}')
        print()
        print('文档已创建成功，可以在飞书中查看。')

    return doc_info


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使用方法: python upload_xmind_to_feishu.py <xmind文件> [文档标题]', file=sys.stderr)
        print('示例: python upload_xmind_to_feishu.py docs/测试用例_数据集26H1需求_V3.3模块_xmind.md')
        print('示例: python upload_xmind_to_feishu.py docs/测试用例_数据集26H1需求_V3.3模块_xmind.md "测试用例-数据集26H1"')
        sys.exit(1)

    xmind_file = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None

    success = upload_xmind_to_feishu(xmind_file, title)
    sys.exit(0 if success else 1)

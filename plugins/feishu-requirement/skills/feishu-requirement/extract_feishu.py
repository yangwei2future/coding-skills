#!/usr/bin/env python3
"""
飞书文档提取脚本
从飞书文档提取内容并保存为本地 Markdown 文件
"""
import os
import sys
import time
import requests

API_BASE_URL = 'https://cfe-doc-backend.inner.chj.cloud'
AUTH_TOKEN = os.environ.get('FEISHU_TOKEN', '')

def check_task_status(task_id, headers, max_retries=60, retry_interval=2):
    """检查任务状态"""
    url = f'{API_BASE_URL}/openapi/v1/extract/task/status'
    for i in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params={'task_id': task_id})
            if response.status_code == 200:
                data = response.json().get('data', {})
                status = data.get('state')
                if status == 'done':
                    return 'done'
                elif status == 'failed':
                    return 'failed'
                elif status in ['running', 'init']:
                    time.sleep(retry_interval)
                else:
                    time.sleep(retry_interval)
            else:
                time.sleep(retry_interval)
        except Exception as e:
            time.sleep(retry_interval)
    print('✗ 任务超时', file=sys.stderr)
    return None

def extract_document(doc_url, output_dir='docs'):
    """提取飞书文档并保存"""
    # 验证 URL
    if not (doc_url.startswith('https://li.feishu.cn/docx') or doc_url.startswith('https://li.feishu.cn/wiki')):
        print('Error: 不是有效的飞书文档 URL!', file=sys.stderr)
        return False

    if not AUTH_TOKEN:
        print('Error: 未设置 FEISHU_TOKEN 环境变量，请先配置认证 token', file=sys.stderr)
        return False

    headers = {'Authorization': f'Bearer {AUTH_TOKEN}', 'User-Agent': 'M3CE-Agent-Tool'}

    # 提交任务
    try:
        submit_url = f'{API_BASE_URL}/openapi/v1/extract/task/submit'
        files = {'file_key': (None, doc_url), 'task_type': (None, 'feishu')}
        response = requests.post(submit_url, headers=headers, files=files, timeout=30)

        if response.status_code != 200:
            print(f'Error: 创建任务失败,状态码: {response.status_code}', file=sys.stderr)
            print(response.text, file=sys.stderr)
            return False

        task_data = response.json().get('data')
        task_id = task_data.get('id')
    except Exception as e:
        print(f'Error: 提交任务失败 - {e}', file=sys.stderr)
        return False

    # 等待任务完成
    status = check_task_status(task_id, headers)
    if status != 'done':
        print(f'Error: 任务未成功完成,最终状态: {status}', file=sys.stderr)
        return False

    # 下载文档内容
    try:
        download_url = f"{API_BASE_URL}{task_data['url']}"
        response = requests.get(download_url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
        file_name = task_data.get('fileName', 'untitled_document')
    except Exception as e:
        print(f'Error: 下载文档失败 - {e}', file=sys.stderr)
        return False

    # 保存文档
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 分析文档类型并生成对应前缀
        doc_type = '需求'  # 默认前缀
        if '技术方案' in file_name or '方案' in file_name or '设计' in file_name:
            doc_type = '方案'
        
        # 生成输出文件路径
        output_file = os.path.join(output_dir, f'{doc_type}_{file_name}.md')

        # 使用二进制模式写入，避免编码问题
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # 打印成功信息
        file_size = len(content)
        print(f'✓ 文档提取成功')
        print(f'文档名称：{file_name}')
        print(f'保存路径：{output_file}')
        print(f'文档大小：{file_size} 字符')
        print()
        print(f'{doc_type}文档已保存，你可以使用 /test-case 命令基于此文档生成测试用例。')

        return True

    except Exception as e:
        print(f'Error: 保存文档失败 - {e}', file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使用方法: python extract_feishu.py <飞书文档URL> [输出目录]', file=sys.stderr)
        print('示例: python extract_feishu.py https://li.feishu.cn/docx/abc123 docs', file=sys.stderr)
        sys.exit(1)

    doc_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'docs'

    # 若 output_dir 为相对路径，解析为项目根目录（脚本上3级）下的路径
    if not os.path.isabs(output_dir):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        output_dir = os.path.join(project_root, output_dir)

    success = extract_document(doc_url, output_dir)
    sys.exit(0 if success else 1)

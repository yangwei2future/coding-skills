#!/usr/bin/env python3
"""
Test Case to XMind Converter
将test-case skill输出的测试用例Markdown转换为飞书思维导图格式
"""
import sys
import re
import json


# ============ 修复1: 新增段落边界检测函数 ============
# 已知的段落标记关键词
SECTION_KEYWORDS = [
    'Setup', '执行步骤', 'Teardown',
    '用例信息', '测试数据', '前置条件',
    '后置条件', '测试步骤', '预期结果'
]

# 预编译正则：匹配 "N. **段落名**" 格式
_SECTION_RE = re.compile(
    r'\d+\.\s*\*\*(' + '|'.join(SECTION_KEYWORDS) + r')\*\*'
)


def is_section_boundary(line):
    """
    检测是否是段落边界（用于内循环 break 条件）
    匹配：
      - "N. **Setup**" / "N. **执行步骤**" 等任意编号的段落标记
      - "####" 开头的标题（下一条用例 or 子标题）
      - "---" 分隔线
    """
    if not line:
        return False
    if _SECTION_RE.match(line):
        return True
    if line.startswith('####'):  # 同时覆盖 #### 和 #####
        return True
    if line.startswith('---'):
        return True
    return False


def parse_testcase_document(content):
    """解析test-case skill格式的文档"""
    lines = content.split('\n')

    # 提取根标题
    root_title = "测试用例思维导图"
    for line in lines[:20]:
        if line.startswith('# '):
            root_title = line[2:].strip()
            if ' 测试用例文档' in root_title:
                root_title = root_title.replace(' 测试用例文档', '')
            break

    # 提取测试统计信息
    stats = {}
    summary_found = False
    for i, line in enumerate(lines):
        if '## 测试总结' in line or '测试用例统计' in line:
            summary_found = True
        if summary_found and '- **总用例数**' in line:
            match = re.search(r'总用例数.*?(\d+)', line)
            if match:
                stats['total'] = match.group(1)
        if summary_found and '- **P0用例**' in line:
            match = re.search(r'P0用例.*?(\d+)', line)
            if match:
                stats['P0'] = match.group(1)
        if summary_found and '- **P1用例**' in line:
            match = re.search(r'P1用例.*?(\d+)', line)
            if match:
                stats['P1'] = match.group(1)
        if summary_found and '- **P2用例**' in line:
            match = re.search(r'P2用例.*?(\d+)', line)
            if match:
                stats['P2'] = match.group(1)
            break

    # 解析所有测试用例
    modules = {}
    current_module = None
    current_tc = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 模块标题（精确匹配 ### 三级标题，避免误匹配 #### 四级标题）
        if line.startswith('### 模块') or (line.startswith('### ') and not line.startswith('#### ') and '：' in line):
            module_match = re.match(r'###\s*(?:模块[一二三四五六七八九十]：\s*)?(.+)', line)
            if module_match:
                current_module = module_match.group(1).split('（')[0].strip()
                if '模块' in current_module[:10]:
                    current_module = re.sub(r'模块[一二三四五六七八九十]：\s*', '', current_module)
                    current_module = re.sub(r'\s*\(\d+条\)', '', current_module)
                if not current_module:
                    current_module = "其他功能"
                modules[current_module] = []
                current_tc = None

        # 测试用例标题
        elif line.startswith('#### TC_'):
            match = re.match(r'####\s+(TC_\w+_\d+)\s*-\s*(.+)', line)
            if match and current_module:
                tc_id = match.group(1)
                tc_title = match.group(2)
                current_tc = {
                    'id': tc_id,
                    'title': tc_title,
                    'priority': '',
                    'type': '',
                    'preconditions': [],
                    'steps': [],
                    'data': None,
                    'postconditions': []
                }
                modules[current_module].append(current_tc)

        # 解析用例属性
        elif current_tc:
            # 优先级
            if '优先级：' in line or '优先级:' in line:
                match = re.search(r'优先级[：:]\s*(P[0-3])', line)
                if match:
                    current_tc['priority'] = match.group(1)
            elif '类型：' in line or '类型:' in line:
                match = re.search(r'类型[：:]\s*(.+)', line)
                if match:
                    current_tc['type'] = match.group(1).strip()
            # 旧格式兼容
            elif line.startswith('**优先级**'):
                match = re.search(r'优先级\*\*:\s*(P[0-3])', line)
                if match:
                    current_tc['priority'] = match.group(1)
            elif line.startswith('**测试类型**'):
                match = re.search(r'测试类型\*\*:\s*(.+)', line)
                if match:
                    current_tc['type'] = match.group(1)

            # ============ 修复2: Setup 用正则匹配，不再用 == ============
            elif re.match(r'\d+\.\s*\*\*Setup\*\*', line) or line == '##### 前置条件':
                i += 1
                while i < len(lines):
                    stripped_line = lines[i].strip()
                    # ★ 用统一的段落边界检测，不再硬编码
                    if is_section_boundary(stripped_line):
                        i -= 1  # 回退，让主循环处理这个段落标记
                        break
                    if stripped_line.startswith('-'):
                        current_tc['preconditions'].append(stripped_line[1:].strip())
                    i += 1

            # ============ 修复3: 执行步骤 用正则匹配 ============
            elif re.match(r'\d+\.\s*\*\*执行步骤\*\*', line) or line == '##### 测试步骤':
                i += 1
                current_step = None
                while i < len(lines):
                    stripped_line = lines[i].strip()
                    # ★ 用统一的段落边界检测
                    if is_section_boundary(stripped_line):
                        i -= 1
                        break

                    # 步骤编号（如：1. 查询第一页数据）
                    step_match = re.match(r'^(\d+)\.\s+(.+)', stripped_line)
                    if step_match:
                        if current_step:
                            current_tc['steps'].append(current_step)
                        current_step = {
                            'action': step_match.group(2).strip(),
                            'expected': []
                        }
                    # 预期结果（嵌套在步骤下，以 - 开头）
                    elif current_step and stripped_line.startswith('-'):
                        expected = stripped_line[1:].strip()
                        if expected:
                            current_step['expected'].append(expected)
                    i += 1
                # 添加最后一个步骤
                if current_step:
                    current_tc['steps'].append(current_step)

            elif line == '##### 预期结果':
                i += 1
                while i < len(lines):
                    if lines[i].strip().startswith('#####') or lines[i].strip().startswith('---'):
                        break
                    if lines[i].strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                        exp = lines[i].strip()[3:].strip() if len(lines[i].strip()) > 3 else lines[i].strip()
                        if exp:
                            current_tc['expected'].append(exp)
                    i += 1

            elif line == '##### 测试数据':
                i += 1
                data_lines = []
                while i < len(lines):
                    if lines[i].strip().startswith('#####') or lines[i].strip().startswith('---'):
                        break
                    if lines[i].strip():
                        data_lines.append(lines[i].strip())
                    i += 1
                if data_lines:
                    current_tc['data'] = '有'

            # ============ 修复4: Teardown 用正则匹配 + 修复 break 条件 ============
            elif re.match(r'\d+\.\s*\*\*Teardown\*\*', line) or line == '##### 后置条件':
                i += 1
                postconditions = []
                while i < len(lines):
                    stripped_line = lines[i].strip()
                    # ★ 用统一的段落边界检测（修复了不识别 #### 的问题）
                    if is_section_boundary(stripped_line):
                        i -= 1  # 回退，防止吞掉下一条用例
                        break
                    if stripped_line:
                        content = stripped_line
                        if content.startswith('-'):
                            content = content[1:].strip()
                        if content and content != '无':
                            postconditions.append(content)
                    i += 1
                if postconditions:
                    current_tc['postconditions'] = postconditions

        i += 1

    return root_title, stats, modules


def convert_to_xmind_markdown(root_title, stats, modules):
    """转换为飞书思维导图Markdown格式（### heading格式）

    飞书思维导图 API 要求标题层级连续：# → ## → ###
    用例内容作为 ### 的直接子节点（- 列表项），Setup/执行步骤/Teardown 与 ###
    平级挂载，不再套一层 title 子节点，避免渲染错位问题。
    """
    lines = []

    # 根节点
    lines.append(f"# {root_title}")
    lines.append("")

    # 按模块输出用例（不输出统计信息节点，不在模块名后附加条数）
    for module_name, test_cases in modules.items():
        lines.append(f"## {module_name}")
        lines.append("")

        for tc in test_cases:
            priority_map = {'P0': '核心', 'P1': '重要', 'P2': '一般', 'P3': '次要'}
            priority_text = priority_map.get(tc['priority'], tc['priority'])
            type_text = '功能' if '功能' in tc['type'] else tc['type']

            # 用例标题用 ### heading，内容直接挂在其下
            lines.append(f"### {tc['id']} - {tc['title']}")
            lines.append(f"- {priority_text} | {type_text}")

            # Setup
            if tc['preconditions']:
                lines.append("- Setup")
                for pc in tc['preconditions']:
                    if len(pc) > 50:
                        pc = pc[:48] + ".."
                    lines.append(f"  - {pc}")

            # 执行步骤
            if tc['steps']:
                lines.append("- 执行步骤")
                for step in tc['steps']:
                    action = step.get('action', '')
                    if len(action) > 60:
                        action = action[:58] + ".."
                    lines.append(f"  - {action}")
                    if step.get('expected'):
                        for exp in step['expected']:
                            if len(exp) > 60:
                                exp = exp[:58] + ".."
                            lines.append(f"    - {exp}")

            # Teardown — 只有内容不为"无"且非空时才显示
            if tc.get('postconditions'):
                lines.append("- Teardown")
                for pc in tc['postconditions']:
                    if len(pc) > 50:
                        pc = pc[:48] + ".."
                    lines.append(f"  - {pc}")

            # 用例之间加空行
            lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("使用方法: python convert_testcase_xmind.py <testcase_md文件>")
        print("示例: python convert_testcase_xmind.py docs/测试用例_数据集26H1需求_V3.3模块.md")
        sys.exit(1)

    md_file = sys.argv[1]

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error: 无法读取文件 - {e}", file=sys.stderr)
        sys.exit(1)

    root_title, stats, modules = parse_testcase_document(content)
    xmind_md = convert_to_xmind_markdown(root_title, stats, modules)
    print(xmind_md)


if __name__ == '__main__':
    main()
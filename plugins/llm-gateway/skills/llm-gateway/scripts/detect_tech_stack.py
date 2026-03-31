#!/usr/bin/env python3
"""
检测项目技术栈,识别使用的 LLM 框架
"""
import argparse
import json
import os
from pathlib import Path


import re

def detect_tech_stack(project_dir):
    """
    检测项目使用的技术栈和 LLM 框架
    """
    project_path = Path(project_dir)
    result = {
        "frameworks": [],
        "package_managers": [],
        "recommendations": []
    }

    def has_dependency(content: str, pkg_name: str) -> bool:
        # 使用正则匹配完整的包名，避免 partial match
        # 匹配 pkg_name 后面跟着版本号操作符、空格、换行或结尾
        # e.g. "openai==1.0", "openai>=1.0", "openai\n", "openai"
        pattern = r'(^|\s|["\'])' + re.escape(pkg_name) + r'($|\s|["\']|[<>=!~])'
        return bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))

    # 检查 Python 项目
    if (project_path / "requirements.txt").exists():
        result["package_managers"].append("pip")
        requirements = (project_path / "requirements.txt").read_text()

        # 检测常见 LLM 框架
        if has_dependency(requirements, "langchain"):
            result["frameworks"].append("langchain")
        if has_dependency(requirements, "litellm"):
            result["frameworks"].append("litellm")
        if has_dependency(requirements, "openai"):
            result["frameworks"].append("openai-sdk")
        if has_dependency(requirements, "anthropic"):
            result["frameworks"].append("anthropic-sdk")
        if has_dependency(requirements, "llama-index"):
            result["frameworks"].append("llama-index")

    if (project_path / "pyproject.toml").exists():
        result["package_managers"].append("poetry/uv")
        pyproject = (project_path / "pyproject.toml").read_text()

        if has_dependency(pyproject, "langchain"):
            result["frameworks"].append("langchain")
        if has_dependency(pyproject, "litellm"):
            result["frameworks"].append("litellm")
        if has_dependency(pyproject, "openai"):
            result["frameworks"].append("openai-sdk")
        if has_dependency(pyproject, "anthropic"):
            result["frameworks"].append("anthropic-sdk")
        if has_dependency(pyproject, "llama-index"):
            result["frameworks"].append("llama-index")

    # 检查 Node.js 项目
    if (project_path / "package.json").exists():
        result["package_managers"].append("npm/pnpm/yarn")
        package_json_text = (project_path / "package.json").read_text()

        if has_dependency(package_json_text, "langchain"):
            result["frameworks"].append("langchain-js")
        if has_dependency(package_json_text, "openai"):
            result["frameworks"].append("openai-node")
        if has_dependency(package_json_text, "@anthropic-ai/sdk"):
            result["frameworks"].append("anthropic-node")

    # 去重
    result["frameworks"] = list(set(result["frameworks"]))
    result["package_managers"] = list(set(result["package_managers"]))

    # 生成建议
    if "langchain" in result["frameworks"]:
        result["recommendations"].append({
            "framework": "langchain",
            "approach": "使用 ChatOpenAI 配置 base_url 参数",
            "priority": "high"
        })

    if "litellm" in result["frameworks"]:
        result["recommendations"].append({
            "framework": "litellm",
            "approach": "使用 LiteLLM 直接传递 api_key 和 base_url 参数",
            "priority": "high"
        })

    if "openai-sdk" in result["frameworks"]:
        result["recommendations"].append({
            "framework": "openai-sdk",
            "approach": "配置 OpenAI client 的 base_url 参数",
            "priority": "high"
        })

    if not result["frameworks"]:
        result["recommendations"].append({
            "framework": "custom",
            "approach": "使用 requests 库直接调用 API",
            "priority": "medium"
        })

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="检测项目技术栈")
    parser.add_argument("project_dir", help="项目目录路径")

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(json.dumps({
            "error": f"目录不存在: {args.project_dir}"
        }, ensure_ascii=False, indent=2))
        exit(1)

    result = detect_tech_stack(args.project_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))

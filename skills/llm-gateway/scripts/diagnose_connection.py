#!/usr/bin/env python3
"""
独立诊断工具 - 测试模型 API 连接
支持三种协议 (OpenAI, Gemini, Claude)
不依赖项目中的其他配置，直接通过命令行参数测试连接。
"""
import argparse
import json
import sys
from typing import Dict, Any, Optional

try:
    import requests
    from gateway_client import GatewayClient
except ImportError:
    print("❌ 缺少必要的依赖: requests 或 gateway_client")
    print("💡 建议先运行 call_gateway.py 脚本来自动设置环境：")
    print("   python3 scripts/call_gateway.py --list")
    print("或者手动安装:")
    print("   pip install requests")
    sys.exit(1)

def diagnose_connection(api_key, model_name):
    """
    测试模型 API 是否可用 - 自动检测协议类型
    """
    print(f"🔍 正在初始化 GatewayClient (Model: {model_name})...")
    
    try:
        client = GatewayClient(api_key=api_key, model=model_name)
        
        print(f"📝 检测到协议: {client.protocol}")
        print(f"🌐 Base URL: {client.base_url}")
        
        messages = [
            {"role": "user", "content": "Hello, this is a connection test."}
        ]
        
        # 使用非流式调用测试
        response = client.chat_completion(messages, timeout=30)
        
        if response.startswith("❌"):
             return {
                "success": False,
                "message": response,
                "protocol": client.protocol
             }
        else:
             return {
                "success": True,
                "message": f"✅ {client.protocol} 协议模型 API 连接成功!",
                "protocol": client.protocol,
                "response_preview": response[:200] + "..."
             }
             
    except Exception as e:
         return {
            "success": False,
            "message": f"❌ 客户端初始化或调用失败: {str(e)}"
         }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="独立诊断工具 - 测试模型 API 连接")
    parser.add_argument("--api-key", required=True, help="API key (JWT Token)")
    parser.add_argument("--model", required=True, help="模型名称")

    args = parser.parse_args()

    result = diagnose_connection(args.api_key, args.model)
    print("\n" + "="*60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result["success"] else 1)

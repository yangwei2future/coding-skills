#!/usr/bin/env python3
"""
LLM Gateway CLI - 命令式接口
提供原子化命令用于 SKILL 流程编排
"""

import argparse
import json
import sys
import os
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def json_output(data, success=True):
    """统一的 JSON 输出格式"""
    result = {
        "success": success,
        "data": data
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if success else 1)

def json_error(message, details=None):
    """统一的错误输出"""
    result = {
        "success": False,
        "error": message
    }
    if details:
        result["details"] = details
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1)

# ==================== 认证相关 ====================

def cmd_login():
    """执行认证登录"""
    try:
        from auth import login
        token = login()
        if token:
            json_output({"message": "认证成功", "token": f"{token[:10]}...已截断"})
        else:
            json_error("认证失败")
    except Exception as e:
        json_error(f"认证失败: {e}")

def get_authenticated_ops():
    """获取已认证的 GatewayOps 实例"""
    try:
        from auth import get_valid_token
        from gateway_ops import GatewayOps

        token = get_valid_token(auto_login=True)
        if not token:
            json_error("认证失败：无法获取有效 Token")

        return GatewayOps(token)
    except Exception as e:
        json_error(f"初始化失败: {e}")

# ==================== 查询命令 ====================

def cmd_list_tenants():
    """列出用户的所有租户"""
    ops = get_authenticated_ops()
    try:
        profile = ops.get_user_profile()
        tenants = ops.get_user_tenants()

        json_output({
            "username": profile.get('username'),
            "tenants": [
                {
                    "tenantId": t.get('tenantId'),
                    "name": t.get('name')
                }
                for t in tenants
            ]
        })
    except Exception as e:
        json_error(f"获取租户列表失败: {e}")

def cmd_list_models(args):
    """列出可用模型"""
    ops = get_authenticated_ops()
    try:
        models = ops.get_provider_models(force_refresh=args.force)

        # 如果指定了搜索关键词
        if args.search:
            keyword = args.search.lower()
            models = [m for m in models if keyword in m['id'].lower()]

        # 格式化输出
        result = {
            "total": len(models),
            "models": []
        }

        # 按 provider 分组
        by_provider = {}
        for m in models:
            provider = m.get('owned_by', 'unknown').lower()
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(m['id'])

        # 构建结果
        for provider, model_ids in sorted(by_provider.items()):
            result["models"].append({
                "provider": provider,
                "models": sorted(model_ids, reverse=True)
            })

        # 添加推荐模型列表
        result["recommended"] = ops.DEFAULT_RECOMMENDED_MODELS

        json_output(result)
    except Exception as e:
        json_error(f"获取模型列表失败: {e}")

def cmd_list_apps(args):
    """列出用户的应用"""
    if not args.tenant:
        json_error("缺少必需参数: --tenant")

    ops = get_authenticated_ops()
    try:
        profile = ops.get_user_profile()
        username = profile.get('username')

        apps = ops.get_user_consumers(args.tenant, username)

        json_output({
            "tenant_id": args.tenant,
            "total": len(apps),
            "apps": [
                {
                    "appName": app.get('appName'),
                    "owner": app.get('owner')
                }
                for app in apps
            ]
        })
    except Exception as e:
        json_error(f"获取应用列表失败: {e}")

def cmd_check_key(args):
    """验证 API Key 有效性"""
    if not args.key or not args.model:
        json_error("缺少必需参数: --key 和 --model")

    # 验证参数格式
    if not args.key.strip():
        json_error("API Key 不能为空")
    if not args.model.strip():
        json_error("模型 ID 不能为空")
    if len(args.key) < 10:
        json_error("API Key 格式无效 (长度过短)")

    try:
        from gateway_client import GatewayClient

        client = GatewayClient(api_key=args.key, model=args.model)
        response = client.chat_completion(
            [{"role": "user", "content": "test"}],
            timeout=30
        )

        if response and not response.startswith("❌"):
            json_output({
                "valid": True,
                "message": "API Key 验证成功",
                "model": args.model
            })
        else:
            json_output({
                "valid": False,
                "message": "API Key 无效或模型不可用"
            })
    except Exception as e:
        json_output({
            "valid": False,
            "message": f"验证失败: {e}"
        })

# ==================== 操作命令 ====================

def cmd_create_app(args):
    """创建新应用"""
    if not args.name or not args.tenant:
        json_error("缺少必需参数: --name 和 --tenant")

    ops = get_authenticated_ops()
    try:
        profile = ops.get_user_profile()
        username = profile.get('username')

        # 清理应用名称
        sanitized_name = ops.sanitize_consumer_name(args.name)

        # 检查是否已存在
        existing = ops.check_app_exists(sanitized_name, args.tenant)
        if existing:
            json_output({
                "created": False,
                "exists": True,
                "message": "应用已存在",
                "app": {
                    "name": existing.get('appName'),
                    "id": existing.get('appId')
                }
            })

        # 创建应用
        app_name = ops.create_placeholder_function(sanitized_name, args.tenant, username)

        json_output({
            "created": True,
            "message": "应用创建成功",
            "app": {
                "name": app_name
            }
        })
    except Exception as e:
        json_error(f"创建应用失败: {e}")

def cmd_subscribe(args):
    """申请模型订阅"""
    if not args.consumer or not args.model or not args.tenant:
        json_error("缺少必需参数: --consumer, --model 和 --tenant")

    ops = get_authenticated_ops()
    try:
        # 检查是否已订阅该特定模型
        check_result = ops.check_model_subscription(args.tenant, args.consumer, args.model)

        if check_result['consumer_exists'] and check_result['subscribed']:
            # 已订阅该模型，直接返回
            json_output({
                "subscribed": True,
                "new": False,
                "message": f"模型 '{args.model}' 已订阅",
                "consumer_id": check_result['consumer_id']
            })

        # 只传递未订阅的新模型
        if check_result['consumer_exists'] and not check_result['subscribed']:
            existing_models = check_result.get('all_models', [])
            print(f"📝 应用已存在，将追加订阅模型: {args.model}", file=sys.stderr)
            print(f"📋 当前已订阅: {', '.join(existing_models) if existing_models else '无'}", file=sys.stderr)

        # 申请订阅（只传递新模型）
        result = ops.apply_subscription(args.tenant, args.consumer, [args.model])

        # 处理不同的返回状态
        if isinstance(result, dict):
            status = result.get('status')
            new_applied = result.get('new_applied', False)

            if status == 'success' and new_applied:
                # 订阅申请成功提交
                json_output({
                    "subscribed": True,
                    "new": True,
                    "message": "订阅申请已提交，请前往飞书审批",
                    "approval_required": True,
                    "status": status
                })
            elif status == 'duplicate':
                # 提交的模型中包含已订阅的模型
                existing_models = check_result.get('all_models', []) if check_result.get('consumer_exists') else []
                json_error(
                    f"订阅申请失败：提交的模型中包含已订阅的模型。\n\n"
                    f"应用 '{args.consumer}' 的订阅状态:\n"
                    f"  • 当前已订阅: {', '.join(existing_models) if existing_models else '无'}\n"
                    f"  • 尝试订阅: {args.model}\n\n"
                    "这通常是程序逻辑错误。正确的做法是:\n"
                    "  1. 先检查模型是否已订阅 (--check-model)\n"
                    "  2. 如果未订阅，再调用 --subscribe\n\n"
                    "如果您需要手动追加订阅，请:\n"
                    "  • 前往飞书审批系统\n"
                    f"  • 找到应用 '{args.consumer}' 的订阅记录\n"
                    "  • 编辑订阅，添加新模型"
                )
            else:
                # 其他情况
                json_output({
                    "subscribed": True,
                    "new": False,
                    "message": "订阅已完成"
                })
    except Exception as e:
        error_msg = str(e)

        # 特殊处理 400009 错误（通过检查错误消息）
        if "不允许重复订阅" in error_msg or "400009" in error_msg:
            existing_models = check_result.get('all_models', []) if check_result.get('consumer_exists') else []
            json_error(
                f"无法通过 API 追加订阅模型 '{args.model}'。\n\n"
                f"应用 '{args.consumer}' 已有订阅记录:\n"
                f"  当前已订阅: {', '.join(existing_models) if existing_models else '无'}\n\n"
                "Gateway API 不支持为已有订阅的应用追加模型。\n\n"
                "解决方案:\n\n"
                "【方案 1】通过飞书审批界面手动追加模型（推荐）\n"
                "  1. 前往飞书审批系统\n"
                f"  2. 搜索应用 '{args.consumer}' 的订阅记录\n"
                "  3. 编辑订阅，添加新模型\n\n"
                "【方案 2】创建新应用订阅该模型\n"
                f"  python3 scripts/gateway_cli.py --create-app --name <new-app-name> --tenant {args.tenant}\n"
                f"  python3 scripts/gateway_cli.py --subscribe --consumer <new-app-name> --tenant {args.tenant} --model {args.model}\n\n"
                "【方案 3】使用已订阅该模型的其他应用\n"
                f"  python3 scripts/gateway_cli.py --list-apps --tenant {args.tenant}"
            )
        else:
            json_error(f"订阅申请失败: {error_msg}")

def cmd_get_key(args):
    """获取 API Key"""
    if not args.consumer or not args.tenant:
        json_error("缺少必需参数: --consumer 和 --tenant")

    ops = get_authenticated_ops()
    try:
        api_key = ops.get_consumer_secret(args.tenant, args.consumer)

        if api_key:
            # 脱敏显示
            masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"

            json_output({
                "success": True,
                "message": "API Key 获取成功",
                "key": api_key,
                "masked_key": masked
            })
        else:
            json_output({
                "success": False,
                "message": "未找到 API Key，可能需要等待审批完成"
            })
    except Exception as e:
        json_error(f"获取 API Key 失败: {e}")

def cmd_save_env(args):
    """保存配置到 .env 文件"""
    if not args.key or not args.model:
        json_error("缺少必需参数: --key 和 --model")

    env_path = args.env_path or ".env"

    try:
        from call_gateway import _update_env_file, DEFAULT_GATEWAY_URL

        _update_env_file(
            api_key=args.key,
            model_id=args.model,
            env_path=env_path,
            consumer_name=args.consumer
        )

        json_output({
            "message": "配置已保存",
            "path": os.path.abspath(env_path),
            "keys": ["LX_LLM_GATEWAY_API_KEY", "LX_LLM_GATEWAY_MODEL", "LX_LLM_GATEWAY_URL"]
        })
    except Exception as e:
        json_error(f"保存配置失败: {e}")

def cmd_read_env(args):
    """读取 .env 文件中的配置"""
    env_path = args.env_path or ".env"

    try:
        if not os.path.exists(env_path):
            json_output({
                "exists": False,
                "message": "配置文件不存在",
                "path": os.path.abspath(env_path)
            })
            return

        # 读取 .env 文件
        config = {}
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 处理 export 前缀
                if line.startswith('export '):
                    line = line[7:].strip()

                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()

                    # 去除引号和注释
                    value = value.strip()
                    if value.startswith('"') and '"' in value[1:]:
                        value = value[1:value.index('"', 1)]
                    elif value.startswith("'") and "'" in value[1:]:
                        value = value[1:value.index("'", 1)]
                    elif '#' in value:
                        value = value.split('#', 1)[0].strip()

                    # 只保存 LLM Gateway 相关配置
                    if key.startswith('LX_LLM_GATEWAY_'):
                        short_key = key.replace('LX_LLM_GATEWAY_', '').lower()
                        config[short_key] = value

        # 脱敏 API Key
        if 'api_key' in config and config['api_key']:
            key = config['api_key']
            if len(key) > 12:
                config['api_key_masked'] = f"{key[:8]}...{key[-4:]}"
            else:
                config['api_key_masked'] = "***"

        json_output({
            "exists": True,
            "path": os.path.abspath(env_path),
            "config": {
                "api_key": config.get('api_key', ''),
                "api_key_masked": config.get('api_key_masked', ''),
                "model": config.get('model', ''),
                "consumer": config.get('consumer', ''),
                "url": config.get('url', '')
            },
            "complete": all(k in config and config[k] for k in ['api_key', 'model'])
        })
    except Exception as e:
        json_error(f"读取配置失败: {e}")

def cmd_update_env(args):
    """更新 .env 文件中的单个配置项"""
    env_path = args.env_path or ".env"

    # 检查是否提供了要更新的字段
    updates = {}
    if args.key:
        updates['LX_LLM_GATEWAY_API_KEY'] = args.key
    if args.model:
        updates['LX_LLM_GATEWAY_MODEL'] = args.model
    if args.consumer:
        updates['LX_LLM_GATEWAY_CONSUMER'] = args.consumer
    if args.url:
        updates['LX_LLM_GATEWAY_URL'] = args.url

    if not updates:
        json_error("请至少提供一个要更新的字段: --key, --model, --consumer, 或 --url")

    try:
        # 读取现有配置
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        # 更新配置
        new_lines = []
        updated_keys = set()

        for line in lines:
            matched = False
            clean_line = line.strip()
            prefix = ""

            if clean_line.startswith('export '):
                prefix = "export "
                clean_line = clean_line[7:].strip()

            for key, value in updates.items():
                if clean_line.startswith(f"{key}="):
                    new_lines.append(f"{prefix}{key}={value}\n")
                    updated_keys.add(key)
                    matched = True
                    break

            if not matched:
                new_lines.append(line)

        # 添加未找到的键
        for key, value in updates.items():
            if key not in updated_keys:
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines.append('\n')
                new_lines.append(f"{key}={value}\n")

        # 写入文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        # 设置文件权限
        try:
            os.chmod(env_path, 0o600)
        except:
            pass

        json_output({
            "message": "配置已更新",
            "path": os.path.abspath(env_path),
            "updated_fields": list(updates.keys())
        })
    except Exception as e:
        json_error(f"更新配置失败: {e}")

def cmd_check_subscription(args):
    """查询订阅状态"""
    if not args.consumer or not args.tenant:
        json_error("缺少必需参数: --consumer 和 --tenant")

    ops = get_authenticated_ops()
    try:
        sub_info = ops.query_consumer_info(args.tenant, args.consumer)

        if sub_info:
            consumer_id = sub_info.get('id')

            # 获取订阅的项目/模型列表
            projects = ops.get_subscribed_projects(args.tenant, consumer_id, debug=False)
            subscribed_models = [p.get('projectCode') for p in projects if p.get('projectCode')]

            json_output({
                "subscribed": True,
                "subscription": {
                    "id": sub_info.get('id'),
                    "consumer": args.consumer,
                    "tenant_id": args.tenant,
                    "status": sub_info.get('status', 'active'),
                    "create_time": sub_info.get('createTime', ''),
                    "update_time": sub_info.get('updateTime', ''),
                    "subscribed_models": subscribed_models,
                    "model_count": len(subscribed_models)
                }
            })
        else:
            json_output({
                "subscribed": False,
                "message": f"未找到应用 '{args.consumer}' 的订阅记录"
            })
    except Exception as e:
        json_error(f"查询订阅状态失败: {e}")

def cmd_check_model_subscription(args):
    """检查应用是否订阅了指定模型"""
    if not args.consumer or not args.tenant or not args.model:
        json_error("缺少必需参数: --consumer, --tenant 和 --model")

    ops = get_authenticated_ops()
    try:
        result = ops.check_model_subscription(args.tenant, args.consumer, args.model)

        if result['consumer_exists']:
            if result['subscribed']:
                json_output({
                    "subscribed": True,
                    "model": args.model,
                    "consumer": args.consumer,
                    "consumer_id": result['consumer_id'],
                    "message": f"应用 '{args.consumer}' 已订阅模型 '{args.model}'"
                })
            else:
                json_output({
                    "subscribed": False,
                    "model": args.model,
                    "consumer": args.consumer,
                    "consumer_id": result['consumer_id'],
                    "all_models": result['all_models'],
                    "message": f"应用 '{args.consumer}' 未订阅模型 '{args.model}'。已订阅的模型: {', '.join(result['all_models']) if result['all_models'] else '无'}"
                })
        else:
            json_output({
                "subscribed": False,
                "consumer_exists": False,
                "model": args.model,
                "consumer": args.consumer,
                "message": f"未找到应用 '{args.consumer}' 的订阅记录"
            })
    except Exception as e:
        json_error(f"检查模型订阅失败: {e}")

def cmd_batch_check_models(args):
    """批量检查多个模型的订阅状态（高效方式）"""
    if not args.consumer or not args.tenant or not args.models:
        json_error("缺少必需参数: --consumer, --tenant 和 --models")

    ops = get_authenticated_ops()
    try:
        # 解析模型列表
        models = [m.strip() for m in args.models.split(',') if m.strip()]

        if not models:
            json_error("模型列表为空")
            return

        # 只查询一次订阅信息
        sub_info = ops.query_consumer_info(args.tenant, args.consumer)

        if not sub_info:
            json_output({
                "success": False,
                "consumer_exists": False,
                "message": f"应用 '{args.consumer}' 不存在"
            })
            return

        consumer_id = sub_info.get('id')

        # 只查询一次订阅的项目列表
        projects = ops.get_subscribed_projects(args.tenant, consumer_id, debug=False)
        subscribed_model_ids = {
            p.get('projectCode')
            for p in projects
            if p.get('projectCode')
        }

        # 批量检查所有模型（本地操作，无API调用）
        checked_models = {}
        subscribed_count = 0
        not_subscribed_count = 0

        for model in models:
            is_subscribed = model in subscribed_model_ids
            checked_models[model] = {
                "subscribed": is_subscribed
            }
            if is_subscribed:
                subscribed_count += 1
            else:
                not_subscribed_count += 1

        json_output({
            "success": True,
            "consumer": args.consumer,
            "tenant_id": args.tenant,
            "consumer_id": consumer_id,
            "checked_models": checked_models,
            "summary": {
                "total": len(models),
                "subscribed": subscribed_count,
                "not_subscribed": not_subscribed_count
            },
            "all_subscribed_models": list(subscribed_model_ids)
        })

    except Exception as e:
        json_error(f"批量检查模型失败: {e}")

# ==================== 便捷命令 ====================

def cmd_setup():
    """运行交互式完整流程（向后兼容）"""
    import subprocess
    script_dir = Path(__file__).parent
    call_gateway = script_dir / "call_gateway.py"

    try:
        result = subprocess.run(
            [sys.executable, str(call_gateway), "--setup"],
            check=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        json_error(f"运行交互式流程失败: {e}")

# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(
        description="LLM Gateway CLI - 命令式接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询租户
  %(prog)s --list-tenants

  # 查询模型
  %(prog)s --list-models
  %(prog)s --list-models --search claude

  # 查询应用
  %(prog)s --list-apps --tenant wlxlvn

  # 读取配置
  %(prog)s --read-env

  # 更新配置（只更新模型）
  %(prog)s --update-env --model new-model

  # 查询订阅状态
  %(prog)s --check-subscription --consumer my-app --tenant wlxlvn

  # 检查单个模型
  %(prog)s --check-model --consumer my-app --model azure-gpt-5 --tenant wlxlvn

  # 批量检查多个模型（推荐）
  %(prog)s --batch-check-models --consumer my-app --tenant wlxlvn \\
    --models "azure-gpt-5,aws-claude-4,gemini-3-pro"

  # 创建应用
  %(prog)s --create-app --name my-app --tenant wlxlvn

  # 申请订阅
  %(prog)s --subscribe --consumer my-app --model azure-gpt-5 --tenant wlxlvn

  # 获取 Key
  %(prog)s --get-key --consumer my-app --tenant wlxlvn

  # 保存配置
  %(prog)s --save-env --key YOUR_KEY --model azure-gpt-5

  # 交互式完整流程
  %(prog)s --setup
        """
    )

    # 认证命令
    parser.add_argument("--login", action="store_true", help="执行认证登录")

    # 查询命令
    parser.add_argument("--list-tenants", action="store_true", help="列出用户的所有租户")
    parser.add_argument("--list-models", action="store_true", help="列出可用模型")
    parser.add_argument("--list-apps", action="store_true", help="列出用户的应用")
    parser.add_argument("--check-key", action="store_true", help="验证 API Key 有效性")
    parser.add_argument("--check-subscription", action="store_true", help="查询订阅状态")
    parser.add_argument("--check-model", action="store_true", help="检查应用是否订阅了指定模型")
    parser.add_argument("--batch-check-models", action="store_true", help="批量检查多个模型的订阅状态")

    # 操作命令
    parser.add_argument("--create-app", action="store_true", help="创建新应用")
    parser.add_argument("--subscribe", action="store_true", help="申请模型订阅")
    parser.add_argument("--get-key", action="store_true", help="获取 API Key")
    parser.add_argument("--save-env", action="store_true", help="保存配置到 .env")
    parser.add_argument("--read-env", action="store_true", help="读取 .env 配置")
    parser.add_argument("--update-env", action="store_true", help="更新 .env 配置")

    # 便捷命令
    parser.add_argument("--setup", action="store_true", help="运行交互式完整流程")

    # 参数
    parser.add_argument("--tenant", type=str, help="租户 ID")
    parser.add_argument("--name", type=str, help="应用名称")
    parser.add_argument("--consumer", type=str, help="应用名称（消费者）")
    parser.add_argument("--model", type=str, help="模型 ID")
    parser.add_argument("--models", type=str, help="模型 ID 列表（逗号分隔），用于批量检查")
    parser.add_argument("--key", type=str, help="API Key")
    parser.add_argument("--url", type=str, help="Gateway URL")
    parser.add_argument("--search", type=str, help="搜索关键词")
    parser.add_argument("--force", action="store_true", help="强制刷新缓存")
    parser.add_argument("--env-path", type=str, help=".env 文件路径")

    args = parser.parse_args()

    # 路由到对应命令
    if args.login:
        cmd_login()
    elif args.list_tenants:
        cmd_list_tenants()
    elif args.list_models:
        cmd_list_models(args)
    elif args.list_apps:
        cmd_list_apps(args)
    elif args.check_key:
        cmd_check_key(args)
    elif args.check_subscription:
        cmd_check_subscription(args)
    elif args.check_model:
        cmd_check_model_subscription(args)
    elif args.batch_check_models:
        cmd_batch_check_models(args)
    elif args.create_app:
        cmd_create_app(args)
    elif args.subscribe:
        cmd_subscribe(args)
    elif args.get_key:
        cmd_get_key(args)
    elif args.save_env:
        cmd_save_env(args)
    elif args.read_env:
        cmd_read_env(args)
    elif args.update_env:
        cmd_update_env(args)
    elif args.setup:
        cmd_setup()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

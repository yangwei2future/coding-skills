import argparse
import os
import re
import sys
import subprocess
from pathlib import Path
import shutil
import time
import hashlib

# Default Configuration
DEFAULT_GATEWAY_URL = "https://llm-gateway-proxy.inner.chj.cloud/llm-gateway"
MAX_RETRIES = 5  # Maximum number of retries for loops

def safe_input(prompt: str) -> str:
    """
    统一的输入处理函数,处理 EOF 和中断信号

    Args:
        prompt: 提示信息

    Returns:
        用户输入的字符串 (已 strip)

    Raises:
        SystemExit: 当用户按 Ctrl+C 或 Ctrl+D 时
    """
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n❌ 用户取消操作")
        sys.exit(0)

def setup_venv_environment():
    """
    设置虚拟环境 (Consistent with faas-deploy)
    1. 检查是否在虚拟环境中运行
    2. 如果不是，创建/激活虚拟环境并重新执行脚本
    """
    skill_dir = Path(__file__).parent.parent.resolve()
    # 使用本地 venv 目录
    venv_dir = skill_dir / "venv"
    
    if os.name == 'nt':
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python3"

    # 检查是否已在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    # 如果已在虚拟环境中，且是我们的 venv，直接返回
    if in_venv and Path(sys.prefix).resolve() == venv_dir.resolve():
        return True
        
    # 特殊情况：如果当前解释器路径与目标解释器路径一致，也认为是正确的
    # (解决某些情况下 sys.prefix 不匹配的问题)
    if Path(sys.executable).resolve() == venv_python.resolve():
        return True

    # 不在虚拟环境中，需要创建/使用 venv
    print("=" * 70)
    print("🔧 步骤 0: 准备 Python 虚拟环境 (自动配置)")
    print(f"   目标路径: {venv_dir}")
    print("=" * 70)
    print()

    # 检查 venv 是否存在且完整
    venv_exists = venv_dir.exists()
    venv_valid = venv_exists and venv_python.exists()

    if not venv_valid:
        # 如果目录存在但 Python 不存在,说明环境已损坏
        if venv_exists and not venv_python.exists():
            print(f"⚠️  检测到虚拟环境已损坏 (Python 解释器不存在)")
            print(f"📦 正在删除损坏的虚拟环境...")
            print()

            import shutil
            try:
                shutil.rmtree(venv_dir)
                print(f"✅ 已清理损坏的虚拟环境")
                print()
            except Exception as e:
                print(f"❌ 清理失败: {e}")
                print(f"💡 请手动删除目录: {venv_dir}")
                sys.exit(1)

        print(f"📦 正在创建虚拟环境: {venv_dir}")
        print()

        try:
            # 创建虚拟环境
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print("❌ 虚拟环境创建失败")
                print(result.stderr)
                sys.exit(1)

            print(f"✅ 虚拟环境创建成功: {venv_dir}")
            print()

        except Exception as e:
            print(f"❌ 创建虚拟环境时出错: {e}")
            sys.exit(1)

        # 安装依赖
        print("📦 正在安装依赖包...")
        print()

        requirements_file = skill_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                # 使用 pip install 安装
                install_cmd = [
                    str(venv_python), "-m", "pip", "install", 
                    "-r", str(requirements_file),
                    "--disable-pip-version-check"
                ]
                
                # Add trusted host if needed (keeping original llm-gateway logic for stability)
                install_cmd.extend(["--trusted-host", "gitlabee.chehejia.com"])

                result = subprocess.run(
                    install_cmd,
                    capture_output=False,  # 显示安装过程
                    text=True,
                    timeout=600  # 10分钟超时
                )

                if result.returncode != 0:
                    print()
                    print("❌ 依赖安装失败")
                    print()
                    print("💡 可能原因:")
                    print("  • 需要连接公司 VPN")
                    print("  • 网络连接问题")
                    print()
                    print("请手动执行:")
                    print(f"  {venv_python} -m pip install -r {requirements_file} --trusted-host gitlabee.chehejia.com")
                    print()
                    sys.exit(1)

                print()
                print("✅ 依赖安装完成")
                print()

            except subprocess.TimeoutExpired:
                print()
                print("❌ 依赖安装超时（超过10分钟）")
                sys.exit(1)
            except Exception as e:
                print()
                print(f"❌ 安装依赖时出错: {e}")
                sys.exit(1)
    else:
        print(f"✅ 虚拟环境已存在: {venv_dir}")
        print()

    # 使用 venv 中的 Python 重新执行当前脚本
    print("🔄 切换到虚拟环境并重新执行脚本...")
    print()
    print("=" * 70)
    print()

    # 传递所有命令行参数
    try:
        # Prepare environment variables
        new_env = os.environ.copy()
        # Ensure we don't carry over python path variables that might confuse the venv
        new_env.pop('PYTHONHOME', None)
        new_env.pop('PYTHONPATH', None)
        
        # Add venv bin to PATH
        bin_dir = venv_dir / ("Scripts" if os.name == 'nt' else "bin")
        new_env["PATH"] = str(bin_dir) + os.pathsep + new_env.get("PATH", "")

        cmd = [str(venv_python)] + sys.argv
        result = subprocess.run(cmd, env=new_env)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ 重启脚本失败: {e}")
        sys.exit(1)

# Step 0: 设置虚拟环境（在导入其他模块之前）
if not setup_venv_environment():
    print("⚠️  注意: 环境依赖可能不完整。")
    print("   脚本将尝试继续运行，但如果缺少关键库，可能会在后续步骤失败。")
    print("   建议: 请检查 VPN 连接并重新运行脚本以修复环境。")


def _strip_env_quotes(value: str) -> str:
    """
    Strips matching leading/trailing quotes from an environment variable value.
    Handles single and double quotes.
    Also strips inline comments if unquoted.
    """
    value = value.strip()
    quote_char = None
    if value.startswith('"'): quote_char = '"'
    elif value.startswith("'"): quote_char = "'"
    
    if quote_char:
        end_idx = value.find(quote_char, 1)
        if end_idx != -1:
            return value[1:end_idx]
        else:
            return value.strip(quote_char)
    else:
        if '#' in value:
            return value.split('#', 1)[0].strip()
        return value

def ensure_authentication(args):
    """
    Step 1: 处理认证逻辑 (Authentication Phase)
    返回: access_token (str)
    """
    if args.login:
        print("\n🔐 正在执行独立认证流程...")
        try:
            from auth import login
            token = login()
            if token:
                print("✨ 认证完成！现在您可以正常运行脚本了。")
            sys.exit(0)
        except ImportError:
            print("❌ 无法导入 auth 模块，请检查环境。")
            print("💡 可能是 idaas-sdk 安装失败。请尝试手动运行安装命令修复环境。")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 认证失败: {e}")
            if "idaas-sdk" in str(e) or "not installed" in str(e):
                 print("💡 请检查 idaas-sdk 是否正确安装。")
            sys.exit(1)

    print("\n🔐 1. 正在认证...", flush=True)
    try:
        from auth import get_valid_token
        token = get_valid_token(auto_login=True)
        
        if token is None:
             print("❌ 认证未完成。")
             sys.exit(1)

        if token == "MOCK_TOKEN_MISSING_DEP":
             print("⚠️  警告: idaas-sdk 未安装，使用模拟 Token (仅限已有 API Key 模式)。")
        else:
             print("✅ 认证成功 (User Access Token)。")
        return token
    except ImportError as e:
        print(f"⚠️  警告: 未找到 auth.py 或 idaas-sdk 缺失。错误详情: {e}")
        return None
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        print("⚠️  将尝试继续执行 (部分交互功能可能受限)...")
        return None

def setup_configuration(ops, args, available_models=None):
    """
    Step 2: 配置与资源准备 (Configuration Phase)
    返回: (api_key, model_id)
    """
    
    # 判断是否强制进入 Setup 流程
    # 如果用户显式指定了 tenant/consumer/new-subscription，说明意图是重新配置或切换环境
    is_explicit_config = args.tenant or args.consumer or args.new_subscription
    should_enter_setup = args.setup or is_explicit_config

    # Step 0: 交互式 API Key 询问 (Interactive Key Prompt)
    # 始终在交互模式下给予用户选择权，即使检测到了环境变量中的 Key
    if not should_enter_setup:
        try:
            # 检查当前是否已有 Key (来自 Env 或 CLI)
            has_key = bool(args.api_key)
            
            print("\n🔑 API Key 配置:")
            if has_key:
                masked = f"{args.api_key[:8]}******{args.api_key[-4:]}" if len(args.api_key) > 12 else "******"
                print(f"   检测到现有 API Key: {masked}")
                print("   (按回车继续使用，或输入 'new' / 'reset' 重新配置)")
            else:
                print("   未检测到 API Key。")
                print("   如果您已有 Key，请直接输入以跳过繁琐的订阅流程。")
                print("   (按回车键进入新订阅申请流程)")

            sys.stdout.flush()
            
            user_input = safe_input("👉 请输入 (回车/Key/new): ")
            
            if user_input:
                if user_input.lower() in ['new', 'reset', 'n']:
                    # 用户想要重置/新建
                    args.api_key = None
                    # 强制进入 setup 流程
                    # 注意: 这里不直接设置 args.setup=True，而是让后续逻辑自然流转到无 Key 状态
                    print("🔄 已清除现有 Key，将进入配置流程。")
                elif len(user_input) > 20: 
                    # 假设输入的是新的 Key
                    args.api_key = user_input
                    print("✅ 已使用新输入的 API Key。")
                    # 如果手动输入了 Key，提示确认模型
                    if not args.model:
                        print("\nℹ️  提示: 请记得补充对应的模型 ID (后续步骤中选择)。")
                else:
                    # 输入了其他短字符，可能是误触，但如果原本有 Key，就保持原样
                    if not has_key:
                        # 原本没 Key，输入了无效内容，视为跳过输入，进入订阅流程
                        pass
            else:
                # 用户直接回车
                if has_key:
                    print("✅ 继续使用现有 API Key。")
                else:
                    print("ℹ️  无 Key 输入，进入订阅申请流程...")

        except (EOFError, OSError):
            # 即使有 Key，如果无法读取输入（非交互环境），也应该提示用户
            if has_key:
                print("\n⚠️  提示: 非交互环境，自动使用现有 API Key。")
            elif not args.api_key:
                 print("\n⚠️  警告: 无法读取输入 (非交互环境)，且未提供 API Key。")


    # 状态提示
    if not args.api_key:
        print("\nℹ️  提示: 未检测到 API Key，即将开始配置流程...")
    elif should_enter_setup:
        print("\nℹ️  提示: 检测到 API Key，但因用户参数要求，将进入重新配置流程...")

    if args.api_key and not should_enter_setup:
        model_input = args.model
        if not model_input:
             if not available_models:
                 available_models = ops.get_provider_models(force_refresh=args.force)
             model_input = resolve_interactive_model(args, available_models, ops)
             
        target_model_id = ops.match_model(model_input, available_models)
        if not target_model_id:
            print("❌ 错误: 未指定或解析出模型 ID。")
            return None, None

        _try_save_env(args, args.api_key, target_model_id, consumer_name=args.consumer)
        
        print(f"\n⚡ 快速通道: 检测到 API Key，跳过配置流程...")
        print(f"   (如需切换租户/应用，请使用 --setup 参数或指定 --tenant)")
        return args.api_key, target_model_id

    # 2.2 完整配置流程
    # (1) 选择租户
    username, tenant_id = get_user_and_tenant(ops, args)
    if not username or not tenant_id:
        return None, None

    # (2) 选择模型
    if not available_models:
        try:
            available_models = ops.get_provider_models(force_refresh=args.force)
        except Exception as e:
            print(f"⚠️ 获取模型列表失败: {e}")
            available_models = []

    model_input = resolve_interactive_model(args, available_models, ops)
    target_model_id = ops.match_model(model_input, available_models)
    
    if not target_model_id or target_model_id == "?":
        print("❌ 错误: 未指定或解析出有效的模型 ID。")
        return None, None
        
    model_ids = [target_model_id]

    print(f"\n✅ 已选模型: {target_model_id}")
    print("---------------------------------------------------------")
    print("📋 下一步: 配置应用标识 (Consumer)")
    print("   这通常是您的应用或项目名称，用于在网关中区分不同调用方。")
    print("---------------------------------------------------------")
    time.sleep(1) # 稍微停顿，让用户意识到步骤切换

    # (3) 选择/创建应用 (Consumer) - 强制交互逻辑
    consumer_name = decide_consumer_flow(ops, args, username, tenant_id)
    if not consumer_name:
        return None, None

    # (4) 验证应用存在
    _verify_app_existence(ops, consumer_name, tenant_id, username)

    # (5) 申请订阅
    if not _apply_subscription(ops, args, tenant_id, consumer_name, model_ids):
        return None, None

    # (6) 获取 API Key
    api_key = _fetch_api_key_loop(ops, args, tenant_id, consumer_name)
    
    if api_key:
        # 保存配置
        _try_save_env(args, api_key, target_model_id, force_save=True, consumer_name=consumer_name)
        return api_key, target_model_id
    else:
        # 即使没获取到 Key，如果用户选择跳过，也保存占位符
        _try_save_env(args, "YOUR_API_KEY_HERE", target_model_id, force_save=True, consumer_name=consumer_name)
        return None, None

def execute_request(api_key, model_id, args):
    """
    Step 3: 执行请求 (Execution Phase)
    """
    if not api_key or not model_id:
        print("\n❌ 无法执行请求: 缺少 API Key 或 Model ID。")
        return

    if args.setup:
        print("\n✨ 设置完成！(已跳过模型调用)")
        return

    key_display = api_key if args.show_key else f"{api_key[:10]}******"
    print(f"   使用 API Key: {key_display}")
    call_model_api(api_key, model_id, args.prompt, args.input, args.output_dir)

# --- Helper Functions for Setup Phase ---

def _try_save_env(args, api_key, model_id, force_save=False, consumer_name=None):
    """尝试保存环境变量"""
    should_save = args.save_env
    
    # 交互模式下默认保存
    if not should_save and (sys.stdin.isatty() or args.setup or force_save):
         should_save = ".env" 

    if should_save:
         env_target_path = should_save if isinstance(should_save, str) else ".env"
         _update_env_file(api_key, model_id, env_target_path, consumer_name=consumer_name)
         print(f"✅ 凭据已保存至 {env_target_path}")

def _verify_app_existence(ops, consumer_name, tenant_id, username):
    print(f"🔍 正在验证应用 '{consumer_name}' 是否就绪...")
    try:
        if not ops.check_app_exists(consumer_name, tenant_id):
            print(f"❌ 严重错误: 应用 '{consumer_name}' 验证未找到。尝试重建...")
            ops.create_placeholder_function(consumer_name, tenant_id, username)
            print("✅ 重新创建成功！")
    except Exception as e:
         print(f"⚠️ 验证应用存在时出错: {e}")

def _apply_subscription(ops, args, tenant_id, consumer_name, model_ids):
    print(f"\n📋 确认信息汇总:")
    print(f"   租户 ID:   {tenant_id}")
    print(f"   模型 ID:    {', '.join(model_ids)}")
    print(f"   应用标识: {consumer_name}")

    # 1. 检查订阅状态（包括模型级别检查）
    print(f"\n🔍 正在检查现有订阅状态...")
    try:
        existing_sub = ops.query_consumer_info(tenant_id, consumer_name)

        if existing_sub:
            consumer_id = existing_sub.get('id')
            print(f"✅ 检测到有效订阅 (ID: {consumer_id})。")

            # 1.1 检查模型级别的订阅
            print(f"\n🔍 正在检查模型订阅状态...")
            subscribed_projects = ops.get_subscribed_projects(tenant_id, consumer_id, debug=False)

            # 提取已订阅的模型 ID
            subscribed_model_ids = [p.get('projectCode') for p in subscribed_projects if p.get('projectCode')]

            # 检查哪些模型已订阅，哪些需要新申请
            already_subscribed = []
            need_to_subscribe = []

            for model_id in model_ids:
                if model_id in subscribed_model_ids:
                    already_subscribed.append(model_id)
                else:
                    need_to_subscribe.append(model_id)

            # 显示检查结果
            if already_subscribed:
                print(f"\n✅ 以下模型已订阅:")
                for model_id in already_subscribed:
                    print(f"   ✓ {model_id}")

            if need_to_subscribe:
                print(f"\n⚠️  以下模型需要订阅:")
                for model_id in need_to_subscribe:
                    print(f"   ✗ {model_id}")
                print(f"\n   将为这些模型申请订阅...")
            else:
                print(f"\n✅ 所有请求的模型均已订阅，无需重复申请。")

                # 所有模型都已订阅，直接返回成功
                if not args.auto_approve:
                    print("ℹ️  提示: 您选择的应用已订阅所有请求的模型。脚本将复用该配置。")
                else:
                    print("⚡ 自动批准: 直接复用现有订阅。")
                return True

            # 更新 model_ids 为需要订阅的模型
            model_ids = need_to_subscribe

        else:
            print("   未找到现有订阅，将创建新订阅。")

    except Exception as e:
        print(f"⚠️ 检查订阅状态时出错: {e}")
        # 继续执行，尝试申请订阅

    # 2. Confirmation
    if args.auto_approve:
        print("⚡ 自动批准 (--auto-approve): 跳过确认。")
    else:
        try:
            # 修改为默认拒绝 (Default No) 以防止误操作
            print("\n⚠️  即将提交订阅申请 (或确认现有配置)。")
            print("   这将向网关后端发起请求。")
            confirm = safe_input("👉 确认继续? (y/N): ").lower()

            # 必须显式输入 y 或 yes
            if confirm not in ['y', 'yes']:
                print("❌ 用户未确认 (需要输入 y)，操作已取消。")
                return False
        except EOFError:
            print("\n🛑 错误: 检测到非交互环境，无法进行交互式确认。")
            print("\n💡 解决方案:")
            print("   1. 在交互式终端中运行脚本")
            print("   2. 使用 --auto-approve 参数跳过确认:")
            print(f"      python3 scripts/call_gateway.py --auto-approve --consumer {consumer_name} --tenant {tenant_id}")
            print("   3. 使用完整流程命令:")
            print(f"      python3 scripts/call_gateway.py --setup")
            return False

    # 3. Apply subscription for new models
    print(f"\n📝 4. 正在申请/同步订阅状态...")
    try:
        result = ops.apply_subscription(tenant_id, consumer_name, model_ids)

        # Handle Waiting Logic
        if isinstance(result, dict) and result.get('new_applied'):
            _wait_for_approval(ops, tenant_id, consumer_name)

        return True
    except Exception as e:
        error_msg = str(e)
        print(f"\n⚠️ 订阅申请遇到问题: {error_msg}")

        # 提供针对性的解决方案
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            print("\n💡 可能的原因: 认证失败")
            print("   解决方案:")
            print("   1. 重新登录: python3 scripts/gateway_cli.py --login")
            print("   2. 检查 token 是否过期")
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            print("\n💡 可能的原因: 权限不足")
            print("   解决方案:")
            print("   1. 检查是否有订阅该模型的权限")
            print("   2. 联系管理员开通权限")
        elif "timeout" in error_msg.lower():
            print("\n💡 可能的原因: 网络超时")
            print("   解决方案:")
            print("   1. 检查网络连接")
            print("   2. 稍后重试")
        elif "重复订阅" in error_msg:
            print("\n💡 提示: 模型可能已订阅")
            print("   验证订阅状态:")
            print(f"   python3 scripts/gateway_cli.py --check-subscription --consumer {consumer_name} --tenant {tenant_id}")
        else:
            print("\n💡 建议:")
            print("   1. 检查网络连接")
            print("   2. 验证参数是否正确")
            print("   3. 查看详细错误信息")

        return True # Try to proceed anyway

def _wait_for_approval(ops, tenant_id, consumer_name):
    print("\n" + "!" * 60)
    print("📢 重要提示：模型订阅申请已提交！")
    print("📢 当前状态：等待审批", flush=True)
    print("请立即前往 **飞书 (Feishu)** 完成订阅审批。", flush=True)
    print("!" * 60, flush=True)
    
    while True:
        try:
            user_in = safe_input("\n✅ 审批完成后按 [回车] 验证; [s] 跳过: ").lower()
        except EOFError:
            user_in = 's'
        
        if user_in == 's': break
        
        check_key = ops.get_consumer_secret(tenant_id, consumer_name)
        if check_key:
            print("🎉 验证成功！审批已通过。")
            break
        else:
            print("❌ 尚未获取到 API Key。请稍后再试。")

def _fetch_api_key_loop(ops, args, tenant_id, consumer_name):
    print(f"\n🔑 5. 获取 API Key...")
    fetched_api_key = ops.get_consumer_secret(tenant_id, consumer_name)
    
    # Retry loop if key is missing and interactive
    if (not fetched_api_key or "YOUR_API_KEY_HERE" in fetched_api_key):
         while True:
             print("\n⚠️  未检测到有效 API Key。")
             try:
                 retry = safe_input("🔄 按 [回车] 再次尝试，或输入 's' 跳过: ").lower()
             except EOFError:
                 retry = 's'

             if retry == 's': break
             
             fetched_api_key = ops.get_consumer_secret(tenant_id, consumer_name)
             if fetched_api_key and fetched_api_key != "YOUR_API_KEY_HERE":
                 print("🎉 成功获取到 API Key！")
                 break
                 
    return fetched_api_key

# ----------------------------------------

def resolve_interactive_model(args, available_models, ops):
    """Handles the interactive model selection."""
    model_input = args.model
    
    if not model_input:
        try:
            config = ops.load_config()
            recommended = config.get("recommended_models", [])
            
            # 总是显示推荐模型，不过滤
            # 即使远程列表里没有，也允许用户选择（可能用于 Fast Path 或强制指定）
            display_models = recommended

            while True:
                # Show numbered list
                print("\n📋 推荐模型:")
                for idx, model_id in enumerate(display_models, 1):
                    print(f"   {idx}. {model_id}")
                
                # Add Search Option
                search_option_idx = len(display_models) + 1
                print(f"   {search_option_idx}. 🔍 搜索远程模型...")

                print("\n💡 提示: 您也可以直接输入模型名称或关键词。")
                
                user_choice = safe_input(f"\n👉 请选择模型 (1-{search_option_idx} 或名称): ")
                if not user_choice:
                    print("⚠️  输入不能为空，请重新输入。")
                    continue
                
                # Try to parse as number first
                if user_choice.isdigit():
                    choice_idx = int(user_choice)
                    
                    if choice_idx == search_option_idx:
                        # Fetch and Search
                        print("\n🔄 正在获取完整模型列表...")
                        full_models = ops.get_provider_models(force_refresh=False)
                        keyword = safe_input("👉 请输入搜索关键词 (例如 'claude'): ").lower()
                        print(f"\n🔍 '{keyword}' 的搜索结果:")
                        filtered = [m for m in full_models if keyword in m['id'].lower()]
                        if not filtered:
                            print("   (未找到匹配项)")
                            model_input = safe_input("👉 手动输入完整模型 ID: ")
                        else:
                            for idx, fm in enumerate(filtered, 1):
                                print(f"   {idx}. {fm['id']}")
                            
                            sel_input = safe_input("👉 请选择模型 (输入序号或完整 ID): ")
                            if sel_input.isdigit():
                                s_idx = int(sel_input)
                                if 1 <= s_idx <= len(filtered):
                                    model_input = filtered[s_idx - 1]['id']
                                else:
                                    # 如果输入的数字超出范围，可能用户就是想输个数字ID? (不太可能，但保持兼容)
                                    print(f"⚠️  序号 {s_idx} 无效，将尝试作为 ID 处理。")
                                    model_input = sel_input
                            else:
                                model_input = sel_input
                        
                        if model_input:
                            break
                        # If empty, loop again
                    
                    elif 1 <= choice_idx <= len(display_models):
                        model_input = display_models[choice_idx - 1]
                        break
                    else:
                        print(f"⚠️  选择无效。")
                else:
                    model_input = user_choice  # Use as keyword/ID
                    break

        except EOFError:
            print("\n❌ 错误: 无法读取输入（非交互环境）。")
            print("\n💡 解决方案:")
            print("   1. 使用 --model <模型ID> 参数显式指定模型:")
            print("      python3 scripts/call_gateway.py --model azure-gpt-5")
            print("   2. 先查看可用模型:")
            print("      python3 scripts/gateway_cli.py --list-models")
            print("   3. 搜索特定模型:")
            print("      python3 scripts/gateway_cli.py --list-models --search claude")
            return None
    return model_input

def _get_filtered_models(available_models: list, limit_per_provider: int = None, provider_whitelist: list = None) -> list:
    """Get a filtered and sorted list of model IDs for display."""
    by_provider = {}
    for m in available_models:
        p = m.get('owned_by', 'unknown').lower()
        if provider_whitelist and p not in [pw.lower() for pw in provider_whitelist]:
            continue
        if p not in by_provider:
            by_provider[p] = []
        by_provider[p].append(m['id'])
    
    result = []
    for provider in sorted(by_provider.keys()):
        ids = sorted(by_provider[provider], reverse=True)
        if limit_per_provider:
            ids = ids[:limit_per_provider]
        result.extend(sorted(ids))
    
    return result

def get_user_and_tenant(ops, args):
    """Fetches user info and selects a tenant."""
    explicit_tenant_id = args.tenant
    print("\n👤 2. 获取用户信息与租户...")
    try:
        user_profile = ops.get_user_profile()
        username = user_profile.get('username', 'unknown')
        print(f"   User: {username}")
        
        tenants = ops.get_user_tenants()
        if not tenants:
            print("❌ 未找到用户租户。")
            return None, None
            
        # 1. Use explicit tenant if provided
        if explicit_tenant_id:
            for t in tenants:
                if t.get('tenantId') == explicit_tenant_id:
                    print(f"   使用指定租户: {t.get('name')} ({explicit_tenant_id})")
                    return username, explicit_tenant_id
            print(f"⚠️  警告: 指定的租户 '{explicit_tenant_id}' 不在您的列表中。")
            
        # 3. If multiple tenants, show them
        print(f"\n💡 找到 {len(tenants)} 个租户:")
        for i, t in enumerate(tenants):
            print(f"   {i+1}. {t.get('name')} ({t.get('tenantId')})")

        # Select tenant
        if explicit_tenant_id:
            return username, explicit_tenant_id
            
        try:
            # 只有当确实是非交互环境（EOFError）时才跳过
            print(f"\n👉 请选择租户 (输入 1-{len(tenants)}):")
            while True:
                # 尝试从 stdin 读取一行
                choice = safe_input(f"   输入序号: ")
                
                if not choice:
                    print("⚠️  输入不能为空，请重新输入。")
                    continue
                        
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(tenants):
                        selected = tenants[idx]
                        print(f"   已选租户: {selected.get('name')} ({selected['tenantId']})")
                        return username, selected['tenantId']
                
                print(f"⚠️  选择无效，请输入 1-{len(tenants)} 之间的数字。")
        except EOFError:
            # 确实无法交互，提供详细的解决方案
            print("\n❌ 错误: 无法读取输入（非交互环境）。")
            print("\n💡 解决方案:")
            print("   1. 使用 --tenant <租户ID> 参数显式指定租户:")
            if tenants and len(tenants) > 0:
                print(f"      python3 scripts/call_gateway.py --tenant {tenants[0]['tenantId']}")
            print("   2. 先查看可用租户:")
            print("      python3 scripts/gateway_cli.py --list-tenants")
            print("\n📌 可用的租户:")
            for idx, t in enumerate(tenants[:3], 1):  # 显示前3个
                print(f"   {idx}. {t.get('name')} (ID: {t['tenantId']})")
            if len(tenants) > 3:
                print(f"   ... 还有 {len(tenants) - 3} 个租户")
            pass  # 继续执行 fallback 逻辑
        except Exception as e:
             # 其他 IO 错误
             print(f"⚠️  交互模式出错: {e}")
             pass
                
        # Non-TTY or EOF fallback
        if len(tenants) > 1:
            if args.auto_approve:
                print(f"⚠️  警告: 非交互模式下发现多个租户 ({len(tenants)})。")
                print(f"   [Auto-Approve] 默认使用第一个租户。")
                selected = tenants[0]
                print(f"✅ 默认使用租户: {selected.get('name')} ({selected['tenantId']})")
                return username, selected['tenantId']
            else:
                print(f"\n❌ 错误: 非交互模式下发现多个租户 ({len(tenants)})。")
                print("   系统无法自动选择。请使用以下方法之一解决:")
                print("   1. 使用 --tenant <ID> 指定明确的租户。")
                print("   2. 使用 --auto-approve 参数允许自动选择默认值。")
                return None, None
            
        # Should be unreachable if len=1 handled above, but for safety
        selected = tenants[0]
        print(f"✅ 默认使用租户: {selected.get('name')} ({selected['tenantId']})")
        return username, selected['tenantId']
        
    except Exception as e:
        print(f"❌ 获取用户信息/租户失败: {e}")
        return None, None

def _generate_consumer_name(username: str, ops, use_random_suffix: bool = False) -> str:
    """
    Generates a robust consumer name with collision avoidance.
    """
    suffix_str = "-llm"
    if use_random_suffix:
        suffix_str += f"-{str(int(time.time()))[-6:]}"
        
    # Max FaaS name length is 32.
    max_user_len = 32 - len(suffix_str)
    
    # Sanitize with a larger length first to allow for hashing if needed
    sanitized_user = ops.sanitize_consumer_name(username, max_len=64)
    
    if len(sanitized_user) > max_user_len:
        trunc_len = max_user_len - 5
        if trunc_len < 1: trunc_len = 1 # Edge case safety
        
        prefix = sanitized_user[:trunc_len].rstrip('-')
        user_hash = hashlib.md5(username.encode()).hexdigest()[:4]
        sanitized_user = f"{prefix}-{user_hash}"
        
    return f"{sanitized_user}{suffix_str}"

def decide_consumer_flow(ops, args, username, tenant_id):
    """Handles logic for choosing or creating a consumer/FaaS function."""
    print(f"\n🔍 3. 确定应用标识与订阅...")

    # 1. CLI Override
    if args.consumer:
        print(f"   使用命令行指定的应用: {args.consumer}")
        return ops.sanitize_consumer_name(args.consumer)

    # 2. 获取现有应用
    existing_consumers = []
    try:
        print(f"   正在获取 {username} 的现有应用列表...")
        existing_consumers = ops.get_user_consumers(tenant_id, username)
        print(f"   找到 {len(existing_consumers)} 个现有应用")
    except Exception as e:
        print(f"⚠️ 获取应用列表时发生错误: {e}")
        import traceback
        traceback.print_exc()
        existing_consumers = []
    
    # 3. 严格交互选择逻辑 (Strict Selection)

    create_default_idx = len(existing_consumers) + 1
    create_custom_idx = len(existing_consumers) + 2

    default_new_name = _generate_consumer_name(username, ops, use_random_suffix=True)

    print("\n📋 请选择应用标识 (Consumer):")
    if existing_consumers:
        for idx, app in enumerate(existing_consumers, 1):
            app_id = app.get('appId')
            id_str = f" (ID: {app_id})" if app_id else ""
            print(f"   {idx}. 复用现有: {app['appName']}{id_str}")
    else:
        print("   (暂无现有应用)")

    print(f"   {create_default_idx}. 新建默认: {default_new_name}")
    print(f"   {create_custom_idx}. 新建自定义名称")

    # 检测交互环境：尝试更健壮的检测方式
    # 在某些环境（如 Claude Code）中，sys.stdin.isatty() 可能返回 False，但实际上可以交互
    is_tty = sys.stdin.isatty()
    should_auto_select = args.auto_approve and not is_tty

    consumer_name = None  # 初始化为 None，确保必须经过选择逻辑

    if should_auto_select:
        if existing_consumers:
            selected = existing_consumers[0]['appName']
            print(f"\n⚡ [Auto-Approve] (非交互模式) 自动复用第一个应用: {selected}")
            return selected
        else:
            print(f"\n⚡ [Auto-Approve] (非交互模式) 自动使用新建默认名: {default_new_name}")
            consumer_name = default_new_name
            # Continue to creation logic
    else:
        if args.auto_approve and is_tty:
            print("\n⚠️  [安全提示] 交互模式下，已忽略 --auto-approve 的自动选择功能。请手动选择应用。")

        # 强制要求用户输入，不允许跳过
        retry_count = 0
        max_retries = 3

        # 首次尝试前，刷新输出确保提示可见
        sys.stdout.flush()

        while retry_count < max_retries:
            try:
                choice = safe_input(f"\n👉 请选择 (1-{create_custom_idx}): ")

                if not choice:
                    print("⚠️  输入不能为空，请重新输入。")
                    retry_count += 1
                    continue

                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(existing_consumers):
                        selected = existing_consumers[idx-1]['appName']
                        print(f"   ✅ 已选择现有应用: {selected}")
                        return selected
                    elif idx == create_default_idx:
                        consumer_name = default_new_name
                        print(f"   ✨ 已选择新建应用: {consumer_name}")
                        break  # 跳出循环，继续创建流程
                    elif idx == create_custom_idx:
                        custom_name = safe_input("👉 请输入新应用名称: ")
                        if not custom_name:
                            print("❌ 应用名称不能为空")
                            retry_count += 1
                            continue
                        consumer_name = custom_name
                        print(f"   ✨ 已选择新建应用: {consumer_name}")
                        break  # 跳出循环，继续创建流程
                    else:
                        print(f"❌ 无效选择，请输入 1-{create_custom_idx} 之间的数字")
                        retry_count += 1
                        continue
                else:
                    print("❌ 输入无效，请输入数字")
                    retry_count += 1
                    continue

            except EOFError:
                # EOFError 表示无法读取输入（真正的非交互环境或输入流已关闭）
                print("\n❌ 错误: 无法读取输入（非交互环境或输入流已关闭）。")
                print("\n💡 解决方案:")
                print("   1. 在交互式终端中运行脚本")
                print("   2. 使用 --consumer <应用名称> 参数显式指定应用:")
                print(f"      python3 scripts/call_gateway.py --consumer <应用名称> --tenant {tenant_id}")
                print("   3. 使用 --auto-approve 参数允许自动选择默认应用:")
                print(f"      python3 scripts/call_gateway.py --auto-approve --tenant {tenant_id}")
                print("   4. 先列出可用应用:")
                print(f"      python3 scripts/gateway_cli.py --list-apps --tenant {tenant_id}")
                print("\n📌 提示: 如果在 CI/CD 或脚本中运行，建议使用 --consumer 参数明确指定应用。")

                # 如果有现有应用，提示可用的应用名称
                if existing_consumers:
                    print("\n   您的现有应用:")
                    for app in existing_consumers[:5]:  # 只显示前 5 个
                        print(f"     - {app['appName']}")
                else:
                    print(f"\n   建议的新应用名称: {default_new_name}")

                return None

        # 如果重试次数用完仍未成功
        if retry_count >= max_retries and not consumer_name:
            print(f"\n❌ 错误: 超过最大重试次数 ({max_retries})，操作已取消。")
            return None

    # 确保 consumer_name 不为 None
    if not consumer_name:
        print("\n❌ 错误: 未能确定应用名称。")
        return None

    # Final existence check and creation (for new ones)
    app_exists = False
    for app in existing_consumers:
        if app.get('appName') == consumer_name:
            app_exists = True
            break
            
    if not app_exists:
        try:
             remote_app = ops.check_app_exists(consumer_name, tenant_id)
             if remote_app: app_exists = True
        except Exception: pass

    if not app_exists:
        try:
            print(f"   正在创建新函数: {consumer_name}...")
            ops.create_placeholder_function(consumer_name, tenant_id, username)
        except Exception as e:
            err_msg = str(e).lower()
            if "exist" in err_msg or "重复" in err_msg or "409" in err_msg:
                print(f"✅ 应用已存在 (API确认)。")
            else:
                print(f"❌ 创建失败: {e}")
                return None
                
    return consumer_name


def call_model_api(api_key, model_id, prompt, input_file, output_dir=None):
    """
    Call the LLM Gateway API using the shared GatewayClient.
    """
    try:
        from gateway_client import GatewayClient
    except ImportError:
        print("❌ 错误: 无法导入 GatewayClient。请确保 scripts/gateway_client.py 存在。")
        return

    print(f"\n📞 5. 调用模型 API (Model: {model_id})...")

    # 1. Prepare Messages
    messages = []
    if input_file:
         try:
             with open(input_file, 'r', encoding='utf-8') as f:
                 file_content = f.read()
             messages.append({"role": "system", "content": f"文件上下文内容:\n{file_content}"})
         except Exception as e:
             print(f"⚠️ 读取输入文件失败: {e}")

    user_content = prompt if prompt else "你好，这是测试。"
    messages.append({"role": "user", "content": user_content})

    # 2. Call API using Client
    try:
        client = GatewayClient(api_key=api_key, model=model_id)
        
        # Use a timeout of 300s as per original script
        response_text = client.chat_completion(messages, timeout=300)
        
        if response_text.startswith("❌"):
             # Client returns error messages prefixed with ❌
             print(f"\n{response_text}")
        else:
            print("✅ API 调用成功！")
            print("\n📝 响应内容:")
            print("-" * 40)
            print(response_text)
            print("-" * 40)

            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    timestamp = int(time.time())
                    safe_model = model_id.replace("/", "_").replace(":", "_")
                    filename = f"response_{safe_model}_{timestamp}.txt"
                    output_path = os.path.join(output_dir, filename)
                    
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(response_text)
                    print(f"\n💾 响应已保存至: {output_path}")
                except Exception as e:
                    print(f"\n❌ 保存响应失败: {e}")

    except Exception as e:
        print(f"❌ 请求错误: {e}")
        if "Connection" in str(e) or "addrinfo" in str(e):
            print("\n💡 提示: 这看起来像网络或 VPN 问题。请检查您的内网连接。")

def _print_available_models(available_models: list, limit_per_provider: int = None, provider_whitelist: list = None):
    """
    Print the list of available models, grouped by provider.
    If limit_per_provider is set, it only shows the latest N models per provider.
    If provider_whitelist is set, it only shows providers in the list.
    """
    # 0. Print Recommended Models First (using GatewayOps defaults)
    try:
        from gateway_ops import GatewayOps
        recommended = GatewayOps.DEFAULT_RECOMMENDED_MODELS
        
        print("\n🌟 推荐模型 (建议优先使用):")
        # Filter to show only those that actually exist in available_models
        available_ids = {m['id'] for m in available_models} if available_models else set()
        
        count = 0
        for i, model_id in enumerate(recommended):
            # 总是显示，但在不可用时添加标记
            count += 1
            if available_ids and model_id not in available_ids:
                print(f"   {count}. {model_id} (未检测到)")
            else:
                print(f"   {count}. {model_id}")
        
        if count == 0:
             print("   (当前提供商列表中未找到推荐模型)")
             
    except Exception as e:
        print(f"   (列出推荐模型失败: {e})")

    print("\n📋 所有可用模型列表:")
    by_provider = {}
    for m in available_models:
        p = m.get('owned_by', 'unknown').lower()
        if provider_whitelist and p not in [pw.lower() for pw in provider_whitelist]:
            continue
        if p not in by_provider: by_provider[p] = []
        by_provider[p].append(m['id'])
    
    if not by_provider and provider_whitelist:
        print(f"   (未找到请求提供商的模型: {', '.join(provider_whitelist)})")
        return

    for provider, ids in sorted(by_provider.items()):
        print(f"\n  [{provider.upper()}]")
        
        # Sort logic: latest models first. 
        sorted_ids = sorted(ids, reverse=True)
        
        display_ids = sorted_ids
        if limit_per_provider:
             display_ids = sorted_ids[:limit_per_provider]
             
        for model_id in sorted(display_ids): # Re-sort for nice alpha listing within the subset
            print(f"   - {model_id}")
            
        if limit_per_provider and len(ids) > limit_per_provider:
            print(f"   (... 还有 {len(ids) - limit_per_provider} 个旧模型已隐藏)")

    if provider_whitelist:
        print("\n💡 其他提供商已隐藏。使用 --list 查看完整目录。")

def _update_env_file(api_key: str, model_id: str, env_path: str = ".env", consumer_name: str = None):
    """Updates or creates the .env file with the gateway credentials."""

    abs_path = os.path.abspath(env_path)
    print(f"📂 正在保存配置到: {abs_path}")

    # 如果文件存在,先创建备份
    if os.path.exists(abs_path):
        backup_path = f"{abs_path}.backup"
        try:
            import shutil
            shutil.copy2(abs_path, backup_path)
            print(f"💾 已备份原配置: {backup_path}")
        except Exception as e:
            print(f"⚠️ 备份失败: {e}")
            # 继续执行,不中断

    lines = []
    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # Map of keys to update
    updates = {
        "LX_LLM_GATEWAY_API_KEY": api_key,
        "LX_LLM_GATEWAY_MODEL": model_id,
        "LX_LLM_GATEWAY_URL": DEFAULT_GATEWAY_URL
    }

    if consumer_name:
        updates["LX_LLM_GATEWAY_CONSUMER"] = consumer_name

    new_lines = []
    processed_keys = set()

    for line in lines:
        matched = False
        # Handle 'export ' prefix
        clean_line = line.strip()
        prefix = ""
        if clean_line.startswith("export "):
            prefix = "export "
            clean_line = clean_line[7:].strip()

        for key, value in updates.items():
            if clean_line.startswith(f"{key}="):
                # Preserve export prefix if present
                new_lines.append(f"{prefix}{key}={value}\n")
                processed_keys.add(key)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    # Add missing keys
    for key, value in updates.items():
        if key not in processed_keys:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{key}={value}\n")

    # 使用原子写入: 写入临时文件,再重命名
    temp_path = f"{abs_path}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # 原子重命名
        os.replace(temp_path, abs_path)

        # Set file permissions to 600 (rw-------) for security
        try:
            os.chmod(abs_path, 0o600)
        except Exception as e:
            # Might fail on Windows or non-standard FS, just log warning
            print(f"⚠️ 无法设置文件权限: {e}")
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise Exception(f"写入配置失败: {e}")

def main():
    """
    Main entry point for the LLM Gateway caller script.
    """
    parser = argparse.ArgumentParser(description="Call LLM Gateway to process data.")
    parser.add_argument("--model", type=str, help="The model identifier to use (e.g., gpt-5, claude-4).")
    parser.add_argument("--tenant", type=str, help="Explicit Tenant ID (e.g. wlxlvn).")
    parser.add_argument("--input", type=str, help="Path to the input data file.")
    parser.add_argument("--prompt", type=str, help="The prompt to send to the model.")
    parser.add_argument("--api-key", type=str, help="API Key for the gateway (optional).")
    parser.add_argument("--list", action="store_true", help="List all available models and exit.")
    parser.add_argument("--all", action="store_true", help="When listing, show all models instead of limiting to latest 5.")
    parser.add_argument("--search", type=str, help="Search for models by keyword (case-insensitive).")
    parser.add_argument("--force", action="store_true", help="Force refresh the model list cache.")
    parser.add_argument("--new-subscription", action="store_true", help="Force creation of a new consumer and subscription.")
    parser.add_argument("--consumer", type=str, help="Specify a custom consumer name.")
    parser.add_argument("--show-key", action="store_true", help="Display the full API Key instead of a truncated version (for automation).")
    parser.add_argument("--save-env", nargs="?", const=".env", help="Automatically save the retrieved API Key and Model to .env file (optional path).")
    parser.add_argument("--env-path", type=str, help="Explicit path to the .env file (alias for --save-env <path>).")
    parser.add_argument("--output-dir", type=str, help="Directory to save the output content.")
    parser.add_argument("--auto-approve", action="store_true", help="Automatically select defaults and approve applications in non-interactive mode.")
    parser.add_argument("--setup", action="store_true", help="Run configuration flow only (subscribe/get key) without calling the model API.")
    parser.add_argument("--login", action="store_true", help="Perform authentication login only.")
    
    args = parser.parse_args()

    print("==========================================")
    print("🚀 LLM 网关调用程序 (v2.2 - Modular Pipeline)")
    print("==========================================")

    # 1. 认证 (Authentication Phase)
    token = ensure_authentication(args)
    if not token:
        return # Auth failed

    from gateway_ops import GatewayOps
    ops = GatewayOps(token)

    # Handle Info Commands
    if args.list or args.search:
        # Re-using logic (could be refactored further but kept inline for now or extracted)
        available_models = ops.get_provider_models(force_refresh=args.force)
        if args.search:
             keyword = args.search.lower()
             print(f"\n🔍 关键词 '{args.search}' 的搜索结果:")
             filtered = [m for m in available_models if keyword in m['id'].lower()]
             _print_available_models(filtered)
        else: # List
             # Print Tenants Info
             try:
                 print("\n🏢 租户与应用信息:")
                 user_info = ops.get_user_profile()
                 username = user_info.get('username', 'unknown')
                 tenants = user_info.get('tenants', []) or ops.get_user_tenants()
                 if not tenants: print("   (未找到租户)")
                 else:
                     print(f"   User: {username}")
                     for i, t in enumerate(tenants):
                         print(f"\n   [{i+1}] 租户: {t.get('name')} ({t.get('tenantId')})")
                         # List consumers
                         try:
                             consumers = ops.get_user_consumers(t.get('tenantId'), username)
                             if consumers:
                                 print(f"       已有的应用标识 ({len(consumers)}):")
                                 for c in consumers:
                                     print(f"       - {c.get('appName')} (ID: {c.get('appId')})")
                         except: pass
             except Exception as e:
                 print(f"   (获取信息失败: {e})")
                 
             limit = None if args.all else 5
             _print_available_models(available_models, limit_per_provider=limit)
        return

    # 2. 配置 (Configuration Phase)
    # 尝试加载 Key，如果没有则进入 setup 流程
    # 自动加载环境变量到 args
    if not args.api_key or not args.model:
        env_path = args.env_path if args.env_path else ".env"
        if args.save_env and isinstance(args.save_env, str): env_path = args.save_env
        if os.path.exists(env_path):
             # 简单的读取逻辑
             try:
                 with open(env_path, 'r') as f:
                     for line in f:
                         if "LX_LLM_GATEWAY_API_KEY=" in line and not args.api_key:
                             parts = line.split("=", 1)
                             if len(parts) > 1:
                                 args.api_key = _strip_env_quotes(parts[1])
                         elif "LX_LLM_GATEWAY_MODEL=" in line and not args.model:
                             parts = line.split("=", 1)
                             if len(parts) > 1:
                                 args.model = _strip_env_quotes(parts[1])
                         elif "LX_LLM_GATEWAY_CONSUMER=" in line and not args.consumer:
                             parts = line.split("=", 1)
                             if len(parts) > 1:
                                 args.consumer = _strip_env_quotes(parts[1])
             except: pass

    api_key, model_id = setup_configuration(ops, args)
    
    # 3. 执行 (Execution Phase)
    if api_key and model_id:
        execute_request(api_key, model_id, args)
    else:
        if not args.setup:
            print("\n❌ 流程未完成，无法调用模型。")

if __name__ == "__main__":
    main()

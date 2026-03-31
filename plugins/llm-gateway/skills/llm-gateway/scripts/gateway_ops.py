"""
Gateway Operations Module
Handles FaaS function management and Model Gateway subscription.
"""

import requests
import json
import time
import re
import os
import sys
from typing import Dict, List, Any, Optional

class GatewayOps:
    # API Endpoints
    IAM_BASE_URL = "https://li.chj.cloud/licloud-iam-service"
    OAM_BASE_URL = "https://li.chj.cloud/licloud-oam-service"
    GLOBAL_BASE_URL = "https://lifaas-globalserver-cn01.inner.chj.cloud/proxies/regional/regions/cnhb01"
    SUB_API_URL = "https://bcs-apihub-core-service-csd.prod.k8s.chj.cloud/sub/project"
    SUB_CONSUMER_URL = "https://bcs-apihub-core-service-csd.prod.k8s.chj.cloud/sub/consumer"
    SUB_PROJECT_BY_CONSUMER_URL = "https://bcs-apihub-core-service-csd.prod.k8s.chj.cloud/sub/projectByConsumerId"
    SUB_SECRET_URL = "https://bcs-apihub-ai-market-service-csd.prod.k8s.chj.cloud/sub/app/secret"
    PROVIDER_MODELS_URL = "https://llm-gateway.inner.chj.cloud/llm/provider/models"
    
    DEFAULT_PRODUCT_ID = 1115

    # Skill-local configuration paths (same level as venv)
    SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CACHE_FILE = os.path.join(SKILL_ROOT, ".llm_gateway_models_cache.json")
    CACHE_TTL = 21600  # 6 hours

    # --- Default Configuration (Internal Defaults) ---
    DEFAULT_FAVORITE_PROVIDERS = ["aws", "azure", "google", "kivy"]
    DEFAULT_LIMIT_PER_PROVIDER = 2
    DEFAULT_RECOMMENDED_MODELS = [
        "azure-gpt-5",
        "azure-gpt-5_1",
        "azure-gpt-5_2",
        "aws-claude-sonnet-4",
        "aws-claude-sonnet-4-5",
        "gemini-3-pro-preview",
        "gemini-3-flash-preview"
    ]

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        })

        # 添加订阅缓存（5分钟TTL）
        self._subscription_cache = {}
        self._cache_ttl = 300  # 5 minutes

    @staticmethod
    def sanitize_consumer_name(name: str, max_len: int = 32) -> str:
        """
        Sanitize and truncate name to meet FaaS requirements.
        - Only lowercase letters, numbers, and hyphens.
        - Max length 32 characters.
        - No trailing hyphen.
        """
        # Validate max_len
        if not isinstance(max_len, int) or max_len <= 0:
            max_len = 32

        if not name:
            return ""
        # Only allow lowercase letters, numbers, and hyphens
        sanitized = re.sub(r'[^a-z0-9-]', '-', name.lower())
        # Truncate to max_len
        if len(sanitized) > max_len:
            sanitized = sanitized[:max_len]
        # Ensure it doesn't end with a hyphen
        sanitized = sanitized.rstrip('-')
        return sanitized

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        response = None
        allowed_status_codes = kwargs.pop('allowed_status_codes', [])
        
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 180
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Diagnostic: print response body on failure BEFORE raise_for_status
            if response.status_code >= 400:
                if response.status_code not in allowed_status_codes:
                    print(f"❌ 请求失败: {url} (状态码: {response.status_code})", file=sys.stderr)
                    try:
                        body = response.text[:1000]
                        print(f"   响应内容: {body}")
                    except:
                        pass
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Re-raise to let caller handle business logic (like get_consumer_secret)
            raise

    # --- IAM / Tenant ---
    def get_user_profile(self) -> Dict[str, Any]:
        url = f"{self.IAM_BASE_URL}/v1/users/profile"
        return self._request('GET', url).get('data', {})

    def get_user_tenants(self) -> List[Dict[str, Any]]:
        url = f"{self.IAM_BASE_URL}/v1/users/tenants"
        return self._request('GET', url).get('data', [])

    def get_user_info(self) -> Dict[str, Any]:
        """Combine profile and tenants into a single info dict for easy integration."""
        profile = self.get_user_profile()
        tenants = self.get_user_tenants()
        profile['tenants'] = tenants
        if tenants:
            profile['tenantId'] = tenants[0]['tenantId']
        return profile

    def load_config(self) -> Dict[str, Any]:
        """Return the default configuration directly from code."""
        return {
            "favorite_providers": self.DEFAULT_FAVORITE_PROVIDERS,
            "limit_per_provider": self.DEFAULT_LIMIT_PER_PROVIDER,
            "recommended_models": self.DEFAULT_RECOMMENDED_MODELS
        }

    def list_applications(self, tenant_id: str, page: int = 1, size: int = 100, myself: bool = True) -> List[Dict[str, Any]]:
        """
        List applications.

        Args:
            tenant_id: 租户ID
            page: 页码
            size: 每页大小
            myself: True=只返回当前用户的应用(新接口), False=返回所有应用(旧接口，用于检测命名冲突)
        """
        # 设置 tenant header（某些接口需要）
        headers = {'x-tenant-id': tenant_id}

        if myself:
            # 新接口：只返回当前用户自己的应用（用于获取用户应用列表）
            url = f"{self.OAM_BASE_URL}/v1/apps/tenants/list_favors"
            params = {
                'tenantId': tenant_id,
                'pageNum': page,
                'pageSize': size,
                'myself': 'true',  # 改为字符串 'true' 而不是布尔值 True
                'orderBy': 'create_time',
                'appTypes': 'faas',
                'sort': 'desc',
                'appClassify': 'normal'
            }
        else:
            # 旧接口：返回所有可见应用（用于检测应用名称是否存在，避免命名冲突）
            url = f"{self.OAM_BASE_URL}/v1/apps"
            params = {
                'tenantId': tenant_id,
                'pageNum': page,
                'pageSize': size
            }

        # This will raise HTTPError or RequestException if failure occurs
        response = self._request('GET', url, params=params, headers=headers)

        # Case 1: Response is a dict with 'data' -> 'result' (Standard)
        if isinstance(response, dict):
            data = response.get('data', {})
            if isinstance(data, list):
                result = data
            else:
                result = data.get('result', [])
                # 如果 result 不存在，尝试其他可能的键名
                if not result and isinstance(data, dict):
                    # 尝试常见的其他键名
                    result = data.get('records', []) or data.get('list', []) or data.get('items', [])
        # Case 2: Response is a list (Uncommon but possible)
        elif isinstance(response, list):
            result = response
        else:
            result = []

        return result

    def get_user_consumers(self, tenant_id: str, username: str) -> List[Dict[str, Any]]:
        """List FaaS applications owned by the user with better error handling."""
        try:
            # 使用新接口（myself=True），只获取当前用户的应用
            apps = self.list_applications(tenant_id, size=1000, myself=True)

            user_apps = []
            for app in apps:
                # Filter by owner and ensure it looks like a consumer (optional, but good)
                if app.get('owner') == username:
                    user_apps.append(app)

            return user_apps
        except requests.exceptions.RequestException as e:
            # 区分 HTTP 错误和网络错误
            if hasattr(e, 'response') and e.response is not None:
                status = e.response.status_code
                print(f"⚠️ API 请求失败 (HTTP {status}): {e}", file=sys.stderr)
            else:
                print(f"⚠️ 网络错误: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"❌ 获取用户应用列表失败: {e}", file=sys.stderr)
            return []

    def check_app_exists(self, app_name: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if app exists (检查所有可见应用，包括其他用户的，以避免命名冲突).
        Returns None if not found. Raises Exception if API call fails.
        """
        try:
            # 使用旧接口（myself=False），检查所有应用以避免命名冲突
            apps = self.list_applications(tenant_id, size=1000, myself=False)
            for app in (apps or []):
                if app.get('appName') == app_name:
                    return app
            return None
        except Exception as e:
            # Re-raise to let caller know it was an error, not just 'not-found'
            # Don't print error here, let caller handle it (e.g. for silent fallback)
            raise

    def create_placeholder_function(self, app_name: str, tenant_id: str, owner: str) -> str:
        """Create a placeholder FaaS function to act as consumer."""
        url = f"{self.OAM_BASE_URL}/v1/apps/init"
        component_name = f"lfc-{int(time.time())}" 
        
        payload = {
            "app": {
                "product": self.DEFAULT_PRODUCT_ID,
                "appName": app_name,
                "appNameCn": app_name,
                "appDesc": "LLM Gateway Consumer",
                "appType": "faas",
                "owner": owner,
                "tenantId": tenant_id
            },
            "componentList": [
                {
                    "data": {
                        "code": {
                            "url": "https://prod-faas-func.s3.bj.bcebos.com/lifaas-server-samples/nodejs/helloworld.zip",
                            "type": "zip"
                        },
                        "listenPort": 8080,
                        "entrypoint": "index.js",
                        "runtime": "native-node20"
                    },
                    "componentType": "webservice",
                    "componentDesc": "LLM Gateway Consumer",
                    "componentName": component_name,
                    "componentNameCn": app_name,
                    "language": "",
                    "creationSource": "skill:llm-gateway"
                }
            ]
        }
        headers = {'x-tenant-id': tenant_id}
        
        print(f"   正在创建应用 '{app_name}'...")
        # 409 Conflict is expected if app already exists (optimistic creation)
        response_data = self._request('POST', url, json=payload, headers=headers, allowed_status_codes=[409])
        
        # Validate creation
        app_data = response_data.get('data', {})
        # The API might return id directly or inside an app object
        app_id = app_data.get('id') or app_data.get('appId')
        if not app_id and isinstance(app_data.get('app'), dict):
            app_id = app_data.get('app').get('appId') or app_data.get('app').get('id')
        
        if app_id:
             print(f"✅ 已创建占位函数: {app_name} (ID: {app_id})", file=sys.stderr)
        else:
             print(f"❌ 创建响应无效: {json.dumps(response_data, ensure_ascii=False)}", file=sys.stderr)
             raise Exception(f"Failed to create function {app_name}")
             
        return app_name

    # --- Subscription ---
    def apply_subscription(self, tenant_id: str, consumer_name: str, model_ids: List[str]):
        """Apply for model subscription using the FaaS function as consumer."""
        url = self.SUB_API_URL
        
        payload = {
            "applyProjectDetailsParam": {
                "businessType": "toB",
                "userType": "内部员工",
                "dataLv": "L3",
                "businessUse": "claude code 申请使用模型",
                "batchUse": True,
                "monthInput": "10万以下",
                "monthOutput": "10万以下",
                "oneMaxInput": "10000以下",
            },
            "consumerType": "FaaS",
            "consumer": consumer_name,
            # "consumerParent": "", # Try removing if empty causes issues
            "remark": "claude code 申请使用模型",
            "env": ["prod", "ontest"],
            "projects": model_ids,
            "flowFormCodeEnum": "APIHUB_AI_BATCH_SUBSCRIBE"
        }
        
        headers = {
            'x-tenant-id': tenant_id
        }
        
        print(f"📝 正在为应用申请订阅: {consumer_name}...")
        
        try:
            response = self._request('POST', url, json=payload, headers=headers)
            
            # Check logical success: code '200' OR '000000'
            code = str(response.get('code'))
            msg = response.get('message', '')
            
            # Success cases:
            # 1. Standard success (200/000000) - 订阅申请成功
            if (code == '200' or code == '000000') and (response.get('success') is True or msg == 'success'):
                 print("✅ 订阅申请提交成功！", file=sys.stderr)
                 return {"status": "success", "new_applied": True, "data": response}
            elif code == '400009' or "重复订阅" in msg:
                 # 400009: 提交的模型列表中包含已订阅的模型
                 # 这不是真正的错误，只是提示不要重复订阅已有模型
                 # 调用方应该先过滤掉已订阅的模型，只传递新模型
                 print(f"⚠️  API 提示: {msg}（提交的模型中包含已订阅的）", file=sys.stderr)
                 return {"status": "duplicate", "new_applied": False, "data": response, "code": code}
            else:
                 print(f"❌ 订阅 API 错误: {json.dumps(response, indent=2, ensure_ascii=False)}", file=sys.stderr)
                 raise Exception(f"Subscription failed: {msg}")
            
        except requests.exceptions.HTTPError as e:
            # Handle 500/400 errors where the body contains the business logic error
            if e.response is not None:
                try:
                    error_resp = e.response.json()
                    code = str(error_resp.get('code'))
                    msg = error_resp.get('message', '')

                    if code == '400009' or "重复订阅" in msg:
                        print(f"⚠️  API 提示: {msg}（提交的模型中包含已订阅的）", file=sys.stderr)
                        return {"status": "duplicate", "new_applied": False, "data": error_resp, "code": code}
                    else:
                        print(f"❌ API 业务错误: {json.dumps(error_resp, indent=2, ensure_ascii=False)}", file=sys.stderr)
                except:
                    pass # Not valid JSON
            print(f"❌ 订阅 HTTP 请求失败: {e}", file=sys.stderr)
            raise
        except Exception as e:
            # print(f"❌ Subscription application failed: {e}", file=sys.stderr) 
            # Let caller handle or just re-raise
            raise

    def query_consumer_info(self, tenant_id: str, consumer_name: str) -> Optional[Dict[str, Any]]:
        """Query existing subscription info for a consumer."""
        url = self.SUB_CONSUMER_URL
        headers = {'x-tenant-id': tenant_id}
        payload = {
            "myself": True,
            "consumerType": None,
            "serviceName": consumer_name,
            "page": 1,
            "pageSize": 10
        }

        try:
            print(f"🔍 正在查询订阅状态: {consumer_name}...", file=sys.stderr)
            response = self._request('POST', url, json=payload, headers=headers)

            data = response.get('data', {}) or {}
            records = data.get('records', []) or []

            # Find exact match
            for record in records:
                if record.get('serviceName') == consumer_name:
                    print(f"✅ 找到现有订阅记录 (ID: {record.get('id')})", file=sys.stderr)
                    return record

            print("   未找到订阅记录。", file=sys.stderr)
            return None
        except Exception as e:
            print(f"⚠️ 查询应用信息失败: {e}", file=sys.stderr)
            return None

    def get_subscribed_projects(self, tenant_id: str, consumer_id: int, debug: bool = False) -> List[Dict[str, Any]]:
        """Query subscribed projects/models for a consumer by consumer ID with caching."""
        # 检查缓存
        cache_key = f"sub:{tenant_id}:{consumer_id}"
        if cache_key in self._subscription_cache:
            cached_data, timestamp = self._subscription_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                if not debug:
                    print(f"📦 使用缓存的订阅数据", file=sys.stderr)
                return cached_data

        url = self.SUB_PROJECT_BY_CONSUMER_URL
        headers = {'x-tenant-id': tenant_id}
        payload = {
            "myself": False,
            "consumerId": consumer_id,
            "page": 1,
            "pageSize": 100  # 获取更多记录
        }

        try:
            print(f"🔍 正在查询 Consumer ID {consumer_id} 的订阅项目...", file=sys.stderr)
            response = self._request('POST', url, json=payload, headers=headers)

            # 🐛 DEBUG: 打印完整的 API 响应（仅在调试模式下）
            if debug:
                print("\n" + "=" * 60, file=sys.stderr)
                print("🔍 DEBUG: 订阅项目查询响应:", file=sys.stderr)
                print(json.dumps(response, indent=2, ensure_ascii=False), file=sys.stderr)
                print("=" * 60 + "\n", file=sys.stderr)

            data = response.get('data', {}) or {}
            records = data.get('records', []) or []

            print(f"📋 找到 {len(records)} 个订阅项目", file=sys.stderr)

            # 提取并打印项目信息
            for record in records:
                project_code = record.get('projectCode')
                project_name = record.get('projectName', 'Unknown')
                if project_code:
                    print(f"  ✓ {project_code} ({project_name})", file=sys.stderr)

            # 保存到缓存
            self._subscription_cache[cache_key] = (records, time.time())

            return records
        except Exception as e:
            print(f"⚠️ 查询订阅项目失败: {e}", file=sys.stderr)
            return []

    def check_model_subscription(self, tenant_id: str, consumer_name: str, model_id: str) -> Dict[str, Any]:
        """
        Check if a specific model is subscribed for the consumer with improved error handling.

        Returns:
            {
                "subscribed": bool,           # 是否已订阅该模型
                "consumer_exists": bool,      # 应用是否存在
                "consumer_id": int or None,   # Consumer ID
                "all_models": list,           # 所有已订阅的模型 ID 列表
                "error": str or None,         # 错误信息（仅出错时）
            }
        """
        result = {
            "subscribed": False,
            "consumer_exists": False,
            "consumer_id": None,
            "all_models": [],
            "error": None
        }

        # 参数验证
        if not consumer_name or not model_id:
            result["error"] = "consumer_name 和 model_id 不能为空"
            return result

        try:
            # 1. 查询应用订阅信息
            consumer_info = self.query_consumer_info(tenant_id, consumer_name)

            if not consumer_info:
                result["error"] = f"应用 '{consumer_name}' 不存在"
                return result

            result["consumer_exists"] = True
            consumer_id = consumer_info.get('id')

            if not consumer_id:
                result["error"] = "应用信息中缺少 ID 字段"
                return result

            result["consumer_id"] = consumer_id

            # 2. 查询已订阅的项目/模型
            projects = self.get_subscribed_projects(tenant_id, consumer_id, debug=False)

            # 3. 提取所有已订阅的模型 ID (projectCode)
            subscribed_models = []
            for project in projects:
                project_code = project.get('projectCode')
                if project_code:
                    subscribed_models.append(project_code)

            result["all_models"] = subscribed_models

            # 4. 检查目标模型是否在订阅列表中
            result["subscribed"] = model_id in subscribed_models

            return result

        except requests.exceptions.RequestException as e:
            result["error"] = f"API 请求失败: {e}"
            return result
        except Exception as e:
            result["error"] = f"检查订阅状态时出错: {e}"
            return result

    def get_consumer_secret(self, tenant_id: str, consumer_name: str) -> Optional[str]:
        """Fetch the API Key (Secret) for the consumer."""
        url = self.SUB_SECRET_URL
        headers = {'x-tenant-id': tenant_id}
        payload = {
            "callerName": consumer_name,
            "callerType": "FaaS",
            "env": ["ontest", "prod"]
        }
        
        try:
            print(f"🔑 正在获取 API Key: {consumer_name}...")
            response = self._request('POST', url, json=payload, headers=headers)
            
            data = response.get('data', {}) or {}
            secrets = data.get('secretKey', []) or []
            
            # Look for 'prod' key
            for secret_obj in secrets:
                if 'prod' in secret_obj:
                    key = secret_obj['prod']
                    print("✅ 成功获取 PROD API Key。", file=sys.stderr)
                    return key

            print(f"⚠️ 警告: 未找到 '{consumer_name}' 的 PROD Key。", file=sys.stderr)
            print("   👉 如果您刚刚申请订阅，请确保飞书审批已通过。", file=sys.stderr)
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                if e.response.status_code == 500:
                    print(f"❌ 获取 Key 时发生服务器错误 (500)。", file=sys.stderr)
                    print("   👉 这通常意味着应用存在，但 API Key 尚未生成。", file=sys.stderr)
                    print("   👉 原因: 飞书审批仍在进行中，或系统同步延迟（请等待 2 分钟）。", file=sys.stderr)
                elif e.response.status_code == 403:
                    print(f"❌ 获取 Key 时权限被拒绝 (403)。", file=sys.stderr)
                    print("   👉 请检查您的 Token 是否属于正确的租户。", file=sys.stderr)
                else:
                    print(f"❌ 获取 Key 失败 (状态码: {e.response.status_code})", file=sys.stderr)
            return None # Graceful return
        except Exception as e:
            print(f"❌ 获取 API Key 失败: {e}", file=sys.stderr)
            return None

    def match_model(self, model_input: str, available_models: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Resolve user input to a valid model ID using exact and fuzzy matching.
        This provides backward compatibility for scripts like test_connection.py.
        """
        if not model_input:
            return "azure-gpt-5"

        # Lazy Logic: If models not provided, check local recommended first to avoid network call
        if available_models is None:
            # 1. Try Exact Match in Recommended (Fast Path)
            if model_input in self.DEFAULT_RECOMMENDED_MODELS:
                return model_input
            
            # 2. Try Fuzzy Match in Recommended
            normalized_input = model_input.lower().replace(".", "-")
            for m in self.DEFAULT_RECOMMENDED_MODELS:
                if m.lower() == normalized_input:
                     return m

            # 3. Not found in local cache -> Fetch Remote
            print(f"   模型 '{model_input}' 不在推荐列表中。正在获取完整远程列表...")
            available_models = self.get_provider_models()

        # Normalize input for matching: lowercase and replace dots with hyphens
        normalized_input = model_input.lower().replace(".", "-")

        # 1. Exact Match (Original or Normalized)
        for m in available_models:
            mid = m['id'].lower()
            if m['id'] == model_input or mid == model_input.lower() or mid == normalized_input:
                return m['id']

        # 2. Fuzzy / Keyword Search (using normalized input)
        matches = [m['id'] for m in available_models if normalized_input in m['id'].lower().replace(".", "-")]

        if len(matches) == 1:
            print(f"   映射 '{model_input}' -> '{matches[0]}'")
            return matches[0]
        elif len(matches) > 1:
            # Sort by distance (shorter IDs or matches starting with input higher)
            matches.sort(key=lambda x: (not x.lower().startswith(normalized_input), len(x)))
            print(f"   模型名称 '{model_input}' 有歧义。匹配项: {matches[:5]}...")
            print(f"   选择最佳匹配: {matches[0]}")
            return matches[0]

        # 3. Fallback
        print(f"   ⚠️ 警告: 提供商列表中未找到模型 '{model_input}'。将使用原始 ID。", file=sys.stderr)
        return model_input

    def get_provider_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch list of available models from the provider with caching."""
        
        # 1. Try Loading from Cache
        if not force_refresh and os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    timestamp = cache_data.get('timestamp', 0)
                    if time.time() - timestamp < self.CACHE_TTL:
                        # print(f"✅ Loaded {len(cache_data.get('models', []))} models from cache.", file=sys.stderr)
                        return cache_data.get('models', [])
            except Exception as e:
                print(f"⚠️ Failed to load model cache: {e}", file=sys.stderr)

        # 2. Fetch from Remote
        url = self.PROVIDER_MODELS_URL
        try:
            print(f"🔍 正在获取可用模型列表 (实时)...", file=sys.stderr)
            response = self.session.get(url, timeout=30) 
            
            if response.status_code != 200:
                print(f"⚠️ 获取模型失败: {response.status_code}", file=sys.stderr)
                # Fallback to expired cache if available
                return self._get_expired_cache()
                
            result = response.json()
            if result.get('code') == 0:
                models = result.get('data', [])
                print(f"✅ 获取到 {len(models)} 个可用模型。", file=sys.stderr)
                self._save_cache(models)
                return models
            else:
                print(f"⚠️ 获取模型时发生 API 错误: {result.get('message')}", file=sys.stderr)
                return self._get_expired_cache()
        except Exception as e:
            print(f"⚠️ 获取提供商模型时出错: {e}", file=sys.stderr)
            return self._get_expired_cache()

    def _save_cache(self, models: List[Dict[str, Any]]):
        """Save models to local cache file."""
        try:
            cache_data = {
                'timestamp': time.time(),
                'models': models
            }
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存模型缓存失败: {e}", file=sys.stderr)

    def _get_expired_cache(self) -> List[Dict[str, Any]]:
        """Fallback to expired cache if remote fetch fails."""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    print(f"ℹ️ 使用过期缓存 ({len(cache_data.get('models', []))} 个模型)。", file=sys.stderr)
                    return cache_data.get('models', [])
            except:
                pass
        return []
